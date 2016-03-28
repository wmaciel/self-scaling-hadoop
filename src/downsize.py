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
from posix import remove
    
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
    util.debug_print(outmsg)
    util.debug_print(errmsg)

    # find the section for the slave we are interested in
    # eg line is "Name: 199.60.17.186:50010 (dlw-Slave71)"
    util.debug_print('trying to find index of where to check status')
    index_for_report_on_slave = -1
    checker = re.compile(config.REPORT_DATANODE_STATUS_STARTING_REGEX + str(slaveName) + '\)')
    for line in outmsg:
        matchobj = checker.match(line)
        if matchobj:
            util.debug_print('found the line! it is: ' + str(line))
            index_for_report_on_slave = outmsg.index(line)
            break
        
    # now check status of slavenode
    commission_line = index_for_report_on_slave + 2
    util.debug_print('commission line is: ' + str(commission_line))
    while True:
        line = outmsg[commission_line]
        util.debug_print('status of decommissioning machine is: ' + str(line))
        if line.find('Decommissioned'):
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
    max_name = util.get_max_slavename(removable_slaves, return_all=False)
    util.debug_print('next slavename to remove is: ' + max_name)
    
    # ok, now we have the slave we want to decommission, update the excludes file
    newLine = max_name + "\n"
    util.updateFile('excludes', newLine)

    # run commands on the master that will output make decommission happen
    ssh = SSHWrapper.SSHWrapper(config.MASTER_IP)
    
    util.debug_print('trying to hdfs dfsadmin -refreshNodes')
    outmsg, errmsg = ssh.sudo_command('sudo -S su hduser -c "/home/hduser/hadoop-2.7.0/bin/hdfs dfsadmin -refreshNodes"')
    util.debug_print(outmsg)
    util.debug_print(errmsg)

    util.debug_print('trying to yarn rmadmin -refreshNodes')
    outmsg, errmsg = ssh.sudo_command('sudo -S su hduser -c "/home/hduser/hadoop-2.7.0/bin/yarn rmadmin -refreshNodes"')
    util.debug_print(outmsg)
    util.debug_print(errmsg)
    
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
            util.debug_print('no slavename passed in as arument AND we got empty slaves file!')
            return False
        
    # remove that slavename from excludes
    remove_line = slaveName + "\n"
    util.debug_print('line to be removed is: ' + remove_line)
    util.debug_print('removing from excludes file')
    update_excludes = util.updateFile('excludes', remove_line, addLine = False)
    util.debug_print('update_excludes: ')
    util.debug_print(update_excludes)
        
    # remove that name from slaves file
    util.debug_print('removing from slaves file')
    update_slaves = util.updateFile('slaves', remove_line, addLine = False)
    util.debug_print('update_slaves: ')
    util.debug_print(update_slaves)
    
    # get vmid from slaveName
    vmid = util.get_vm_id_by_name(slaveName)
    
    util.debug_print('Now we will be trying to destroy the machine with ID: ' + str(vmid))
    result = api.destroyVirtualMachine({'id': vmid})
    util.debug_print('result from calling destroy vm')
    util.debug_print(result)
    
    util.debug_print('waiting for the destroyed machine to be finished being destroyed')
    waitResult = util.waitForAsync(result.get('jobid'))
    util.debug_print('result of async wait is.....')
    util.debug_print(waitResult)
    
    ''' 
    DO WE NEED TO DO ANYTHING ELSE????? MAYBE RUN SOME SCRIPTS????
    '''
    
    return True
    
# basic global stuff
api, pp = util.setup()
