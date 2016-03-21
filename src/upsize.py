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


# function that creates/sets the global counter
def updateHostFile(newSlaveName, newSlaveIp, filename=None):
    new_hosts_line = str(newSlaveName) + '\t' + str(newSlaveIp)
    
    # make filename correct
    if filename is None:
        filename = config.DEFAULT_GLOBAL_HOSTS_FILENAME

    # now check if file exists
    next_name = ''
    if os.path.isfile(filename):
        # get value of file
        list_of_current_slaves = list()
        with open(filename, 'r+') as fh: 
            list_of_current_slaves = [line for line in fh.readlines() if line.strip()]
            
        # now we make sure it's not already in there
        if new_hosts_line not in list_of_current_slaves:
            list_of_current_slaves.append(new_hosts_line)
            
        # update file
        with open(filename, 'w') as fh: 
            for line in list_of_current_slaves:
                fh.write("%s\n", line)
    else:   #uhg. now for case where we have no local hosts file... we pull from master

        # get hosts file from master...
        ssh = SSHWrapper.SSHWrapper(config.MASTER_IP)
        hosts_file, = ssh.sudo_command('cat /etc/hosts')
        print hosts_file
        
        # now get max number of slave and set the global counter
#         max_numbers.sort(reverse=True)
#         max_slave = int(max_numbers[0]) + 1
#         with open(filename, 'w') as fh:
#             fh.write(str(max_slave))
#         next_name = config.BASE_SLAVE_NAME + str(max_slave)

    # return new name!


def upsize(argv):

    # now we need to get the next slave name 
    next_name = getNextSlaveName()
    if not next_name:
        pp.pprint('getting the next name failed.')
        return -1

    # try to deploy with new slave with correct name
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

    ''' now get ip of new machine ''' 
    # get info for newly generated machine
    result2 = api.listVirtualMachines({'id': result.get("id") })
    ip = result2.get('virtualmachine')[0].get('nic')[0].get('ipaddress')

    # now we initialize the ssh connection 
    ssh = SSHWrapper.SSHWrapper(ipAddr=ip)
    
    #
    
    #
    
    ssh.close()
    

# basic global stuff
api, pp = util.setup()

