'''
Created on Mar 21, 2016

@author: loongchan
'''
import sys  
import simpleCloudStackRest
import SSHWrapper
import util
import config
import re

def get_max_slavename(some_file_list, return_all = False):
    '''
    This function gets a list of slave names, one per line and either returns the "max" slave name
    Input: ['dlw-Slave2\n', 'dlw-Slave3\n']
    Output 'dlw-Slave3'
    '''
    util.debug_print('calling on util.get_max_slavename')
    
    # get max slave node name
    max_slave_name = ''
    max_slave_number = 0
    all_slaves_list = list()
    checker = re.compile(config.SLAVE_NAMING_REGEX)
    for line in some_file_list:
        matchobj = checker.match(line)
        if matchobj:
            
            # add to all slave list
            all_slaves_list.append(matchobj.group())
            
            # figure out max slavename
            line_slave_number = int(matchobj.group(1))
            if max_slave_number < line_slave_number:
                max_slave_number = line_slave_number
                max_slave_name = matchobj.group()
    
    if return_all:
        util.debug_print('util.get_max_slave is returning list of slaves:')
        util.debug_print(all_slaves_list)
        return all_slaves_list
    else:
        util.debug_print('util.get_max_slave is returning: ' + max_slave_name)
        return max_slave_name
    
    
def stopDecommissionedMachine(slaveName = None):
    '''
    Checks whether decommissioning completed, then stops the vm
    Input String slavename
    Output: None
    '''
    util.debug_print('calling downsize stopDecommissionedMachine()')
    
    if slaveName is None:
        util.debug_print('not slaveName passed as parameter')
        # get the excludes file from master
        excludes_file_content = util.get_file_content(config.DEFAULT_DESTINATION_EXCLUDES_FILENAME)
        
        # no magic, just get last one
        if len(excludes_file_content) > 0:
            slaveName = excludes_file_content[-1].strip()
        else:
            util.debug_print('no slavename passed in as arument AND we got empty slaves file!')
            return False
    
    
    vmid = util.get_vm_id_by_name(slaveName)
    
    # connect to master 
    ssh = SSHWrapper.SSHWrapper(config.MASTER_IP)
    
    # get status
    util.debug_print('Trying to get report on status of machines... ')
    outmsg, errmsg = ssh.sudo_command('sudo -S su hduser -c "/home/hduser/hadoop-2.7.0/bin/hdfs dfsadmin -report"')

    # find the section for the slave we are interested in
    # eg line is "Name: 199.60.17.186:50010 (dlw-Slave71)"
    checker = re.compile(config.REPORT_DATANODE_STATUS_STARTING_REGEX + str(slaveName) + '\)')
    util.debug_print('starting while loop to check for status of VM is done decommissioning')
    while True:
        # get line for checking machine status
        line = ''
        commission_line = 0
        # ok, I admin it might not be the best to put this here as the report MIGHT not chagne, but who knows... slower but safer for now
        for line in outmsg:
            matchobj = checker.match(line)
            if matchobj:
                util.debug_print('found the line! it is: ' + str(line))
                commission_line = outmsg.index(line) + 2
                break;

        line = outmsg[commission_line]
        util.debug_print('on line: ' + str(commission_line) + ' status of decommissioning machine is: ' + str(line))
        if line.find('Decommissioned') > -1:
            result = api.stopVirtualMachine({'id': vmid})
            util.debug_print('result from calling stopvm')
            util.debug_print(result)
             
            waitResult = util.waitForAsync(result.get('jobid'))
            util.debug_print('result of async wait is.....')
            util.debug_print(waitResult)
             
            if waitResult != True: # whoops something went wrong!
                return waitResult
            
            # let's get out of here!
            util.debug_print('DONE, we waited for it to finish decomissioning, then we stopped the VM! ')
            break;

        # ok, not decommissioned yet, so callthe ssh command again!
        util.debug_print('checking again inside forever WHileTrue loop, as it is not in decomissioned state.')
        outmsg, errmsg = ssh.sudo_command('sudo -S su hduser -c "/home/hduser/hadoop-2.7.0/bin/hdfs dfsadmin -report"')
        util.debug_print(outmsg)
        util.debug_print(errmsg)
        
    return True
    
def decommission(also_stop_vm = True):
    '''
    This function basically copies slave names from slaves list to excludes list and run refresh scripts
    Input: None
    Output: None
    '''
    util.debug_print('Trying to decommision')
    
    # get all slave names in slaves file
    all_slave_names = map(str.strip, util.get_file_content(config.DEFAULT_DESTINATION_SLAVES_FILENAME))
    util.debug_print('all_slave_names:')
    util.debug_print(all_slave_names)
    
    # get excludes content from master
    excludes_list = map(str.strip, util.get_file_content(config.DEFAULT_DESTINATION_EXCLUDES_FILENAME))
    util.debug_print('current excludes list:')
    util.debug_print(excludes_list)
    
    # basic sanity check to see if we should try to decomission 
    remaining_slaves =  len(all_slave_names) - len(excludes_list)
    if remaining_slaves <= config.MINIMUM_DATANODE_SIZE:
        util.debug_print('We have reached the minimum cluster size of ' + str(remaining_slaves) + ', skipping decomissioning.')
        return False
    
    # ok, now we know we can remove some 
    removable_slaves = list(set(all_slave_names) - set(excludes_list))
    max_name = get_max_slavename(removable_slaves, return_all=False)
    util.debug_print('next slavename to remove is: ' + max_name)
    
    # ok, now we have the slave we want to decommission, update the excludes file
    newLine = max_name + "\n"
    util.updateFile('excludes', newLine)

    # run commands on the master that will output make decommission happen
    ssh = SSHWrapper.SSHWrapper(config.MASTER_IP)
    
    util.debug_print('trying to hdfs dfsadmin -refreshNodes')
    outmsg, errmsg = ssh.sudo_command('sudo -S su hduser -c "/home/hduser/hadoop-2.7.0/bin/hdfs dfsadmin -refreshNodes"')

    util.debug_print('trying to yarn rmadmin -refreshNodes')
    outmsg, errmsg = ssh.sudo_command('sudo -S su hduser -c "/home/hduser/hadoop-2.7.0/bin/yarn rmadmin -refreshNodes"')
    
    if also_stop_vm:
        stopDecommissionedMachine(max_name)
    
def removeDecommissionedMachine(slaveName = None):
    '''
    Destroy decommissioned machines from the cluster and removes traces from excludes and slaves file
    INPUT: String slaveName (optional)
    OUTPUT: boolean (True if successful, False otherwise)
    '''
    util.debug_print('calling downsize removeDecommissionedMachine()')
    
    # if not set, then get from excludes list
    if slaveName is None:
        util.debug_print('not slaveName passed as parameter')
        # get the excludes file from master
        excludes_file_content = util.get_file_content(config.DEFAULT_DESTINATION_EXCLUDES_FILENAME)
        
        # no magic, just get last one
        if len(excludes_file_content) > 0:
            slaveName = excludes_file_content[-1].strip()
        else:
            util.debug_print('no slavename passed in as argument AND we got empty slaves file!')
            return False
        
    # remove that slavename from excludes
    remove_line = slaveName + "\n"
    util.debug_print('removing from excludes file the line: ' + remove_line)
    update_excludes = util.updateFile('excludes', remove_line, addLine = False)
    util.debug_print('update_excludes result: ')
    util.debug_print(update_excludes)
        
    # remove that name from slaves file
    util.debug_print('removing from slaves file')
    update_slaves = util.updateFile('slaves', remove_line, addLine = False)
    util.debug_print('update_slaves: ')
    util.debug_print(update_slaves)
    
    # get vmid from slaveName
    vmid = util.get_vm_id_by_name(slaveName)
    
    # NOW deestroy vm
    util.debug_print('Now we will be trying to destroy the machine with ID: ' + str(vmid))
    result = api.destroyVirtualMachine({'id': vmid})
    util.debug_print('result from calling destroy vm')
    util.debug_print(result)
    
    util.debug_print('waiting for the destroyed machine to be finished being destroyed')
    waitResult = util.waitForAsync(result.get('jobid'))
    util.debug_print('result of async wait is.....')
    util.debug_print(waitResult)
    
    # since we destroyed the vm, we can remove from master's /etc/hosts file
    hosts = util.get_file_content(config.DEFAULT_DESTINATION_HOSTS_FILENAME)
    checker = re.compile('.*' + slaveName + '\n')
    to_be_removed_hosts_line = [line for line in hosts if checker.match(line) is not None]
    util.debug_print('remove line:' + str(to_be_removed_hosts_line) + ' from /etc/hosts file')
    util.updateFile('hosts', to_be_removed_hosts_line[0], addLine = False)

    ''' 
    DO WE NEED TO DO ANYTHING ELSE????? MAYBE RUN SOME SCRIPTS????
    '''
    
    return True
    
# basic global stuff
api, pp = util.setup()

