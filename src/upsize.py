'''
Created on Mar 21, 2016

@author: loongchan
'''
import sys  
import os
import re
import simpleCloudStackRest # super simple class for doing cloudstack api calls
import SSHWrapper
import util
import config

# function that creates/sets the global counter
def getNextSlaveName(filename=None):
    
    # make filename correct
    if filename is None:
        filename = config.DEFAULT_GLOBAL_COUNTER_FILENAME

    # now check if file exists
    next_name = ''
    if os.path.isfile(filename):
        # get value of file
        with open(filename, 'r+') as fh: 
            max_slave = int(fh.read()) + 1 
            next_name = config.BASE_SLAVE_NAME + str(max_slave)

        # update value of file
        with open(filename, 'w') as fh: 
            fh.write(str(max_slave))
    else:   # ok, file does NOT exist, now we need to create that global counter file!

        # first get all machines
        result = api.listVirtualMachines({'listall': 'true', 'details':'all'})

        # now check if it worked
        if 'errortext' in result:
            # oh man... failed!
            pp.pprint(result)
            return next_name

        vms = result.get('virtualmachine')

        # now we start to look for conventional dlw-Slave# names
        vmlist = dict() # dict of slavenames:ip
        max_numbers = list() # so we can get max number used in naming slaves 
        checker = re.compile(config.SLAVE_NAMING_REGEX)
        for vm in vms:
            test_name = vm.get('displayname')
            matchobj = checker.match(test_name)
            if matchobj:
                ip = vm.get('nic')[0].get('ipaddress')
                vmlist[matchobj.group()] = ip
                max_numbers.append(int(matchobj.group(1)))
            else:
                print 'failed to match name: ' + test_name

        # now get max number of slave and set the global counter
        max_numbers.sort(reverse=True)
        max_slave = int(max_numbers[0]) + 1
        with open(filename, 'w') as fh:
            fh.write(str(max_slave))
        next_name = config.BASE_SLAVE_NAME + str(max_slave)

    # return new name!
    return next_name

def upsize():

    # now we need to get the next slave name
    util.debug_print('Trying to get slave name....') 
    next_name = getNextSlaveName()
    if not next_name:
        pp.pprint('Getting the next name failed.')
        return -1

    util.debug_print('slavename is: '+str(next_name))

    # try to deploy with new slave with correct name
    util.debug_print('Trying to deploy VM')
    result = api.deployVirtualMachine({ 'serviceofferingid': config.SERVICEOFFERINGID,
                                        'zoneid': config.ZONEID,
                                        'templateid': config.TEMPLATEID,
                                        'displayname': next_name,
                                        'name': next_name })

    # now we wait for the async deployVirtualMachine() to finsih
    waitResult = util.waitForAsync(result.get('jobid'))
    if waitResult != True:
        # whoops something went wrong!
        return waitResult

    # now check if deploy worked
    if 'errortext' in result:
        # oh man... failed!
        pp.pprint(result)
        return
    util.debug_print('OK, just created the VM')

    ''' now get ip of new machine ''' 
    # get info for newly generated machine
    result2 = api.listVirtualMachines({'id': result.get("id") })
    ip = result2.get('virtualmachine')[0].get('nic')[0].get('ipaddress')
    util.debug_print('IP of new machine is: '+str(ip))
    
    # clear out datanode
    dataNodessh = SSHWrapper.SSHWrapper(ip)
    dataNodessh.sudo_command('sudo -S su hduser -c "rm -rf /home/hduser/hadoop-tmp/hdfs/datanode/*"')
    
    # change the hostname
    util.update_hostname(ip, next_name, result.get("id"))
    
    # new line for /etc/hosts file
    new_hosts_line =  str(ip) + '\t' + str(next_name) + '\n'

    # update hosts file on master
    util.debug_print('Trying update Hosts file with line: '+new_hosts_line)
    util.updateFile('hosts', new_hosts_line)
    util.debug_print('Updated hosts file')
    
    # update slaves file on master
    util.debug_print('Trying to update slaves file with name:' + next_name)
    util.updateFile('slaves', next_name + "\n")
    util.debug_print('Done updating slaves file')
    
    # now to start the start-dfs.sh and start-yarn.sh
    ssh = SSHWrapper.SSHWrapper(config.MASTER_IP)

    util.debug_print('trying to start-dfs.sh')
    outmsg, errmsg = ssh.sudo_command('sudo -S su hduser -c "bash /home/hduser/hadoop-2.7.0/sbin/start-dfs.sh"')
    util.debug_print(outmsg)
    util.debug_print(errmsg)
    
    util.debug_print('trying to run start-yarn.sh')
    outmsg, errmsg = ssh.sudo_command('sudo -S su hduser -c "bash /home/hduser/hadoop-2.7.0/sbin/start-yarn.sh"')
    util.debug_print(outmsg)
    util.debug_print(errmsg)
    
    util.debug_print('DONE!')

def recommission(slaveName = None):
    '''
    This function recommissions, aka removes from excludes list and runs correct script to add back to node
    Input: None
    Output: None
    '''
    util.debug_print('calling upsize recommission()')
    
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
    
    # confirm if VM is running or stopped or whatever
    vmid = util.get_vm_id_by_name(slaveName)
    raw_result = api.listVirtualMachines({'id':vmid})
    result = raw_result.get('virtualmachine')[0]
    ipaddr = result.get('nic')[0].get('ipaddress')
    
    while True:
        current_state = result.get('state')
        if current_state == 'Running':
            util.debug_print('Machine is currently running')
            
            util.debug_print('trying to hdfs dfsadmin -refreshNodes')
            ssh = SSHWrapper.SSHWrapper(config.MASTER_IP)
            outmsg, errmsg = ssh.sudo_command('sudo -S su hduser -c "/home/hduser/hadoop-2.7.0/bin/hdfs dfsadmin -refreshNodes"')
        
            util.debug_print('trying to yarn rmadmin -refreshNodes')
            outmsg, errmsg = ssh.sudo_command('sudo -S su hduser -c "/home/hduser/hadoop-2.7.0/bin/yarn rmadmin -refreshNodes"')
            
            
            break
        elif current_state == 'Stopped':
            util.debug_print('Machine is currently Stopped')
            
            # start up machine and wait till it finishes starting up
            util.debug_print('Trying to start VM')
            result = api.startVirtualMachine({'id': vmid})
        
            # now we wait for the async deployVirtualMachine() to finsih
            waitResult = util.waitForAsync(result.get('jobid'))
            if waitResult != True:
                # whoops something went wrong!
                return waitResult
            
            # SSHWrapper checks and loops and waits for connection so let's just use it for testing that
            '''
            WHY DOES RESULT NOT GET ANYTHING! INEED THE IP OF THE DEVICE!  MAYBE GET IT EARLIER?
            '''
            sshWaiting = SSHWrapper.SSHWrapper(ipaddr)
            
            util.debug_print('trying to start-dfs.sh')
            ssh = SSHWrapper.SSHWrapper(config.MASTER_IP)
            ssh.sudo_command('sudo -S su hduser -c "bash /home/hduser/hadoop-2.7.0/sbin/start-dfs.sh"')
            
            util.debug_print('trying to run start-yarn.sh')
            ssh.sudo_command('sudo -S su hduser -c "bash /home/hduser/hadoop-2.7.0/sbin/start-yarn.sh"')
            
            util.debug_print('trying to hdfs dfsadmin -refreshNodes')
            ssh.sudo_command('sudo -S su hduser -c "/home/hduser/hadoop-2.7.0/bin/hdfs dfsadmin -refreshNodes"')
        
            util.debug_print('trying to yarn rmadmin -refreshNodes')
            ssh.sudo_command('sudo -S su hduser -c "/home/hduser/hadoop-2.7.0/bin/yarn rmadmin -refreshNodes"')
            
            break
        elif current_state == 'Stopping' or current_state == 'Starting':
            util.debug_print('OK, currently changing state, let us just call listVirtualMachines again and see.')
            raw_result = api.listVirtualMachines({'id':vmid})
            result = raw_result.get('virtualmachine')[0]
        else:
            # something went wrong here!
            util.debug_print('ok, it is in an unexpected state: ' + str(current_state))
            return False

# basic global stuff
api, pp = util.setup()

