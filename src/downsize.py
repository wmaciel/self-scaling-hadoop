'''
Created on Mar 21, 2016

@author: loongchan
'''
import sys  
import os
import re
import simpleCloudStackRest
import SSHWrapper
import util
import config
import time

def getLastSlaveName():
    util.debug_print('called getLastSlaveName()')
    get_file_command = 'cat ' + config.DEFAULT_DESTINATION_SLAVES_FILENAME
    
    # connect to master node
    ssh = SSHWrapper.SSHWrapper(config.MASTER_IP)
    
    # get slaves file info from master...
    some_file_list, some_error = ssh.command(get_file_command)
    
    # get max slave node name
    max_slave_name = ''
    max_slave_number = 0
    checker = re.compile(config.SLAVE_NAMING_REGEX)
    for line in some_file_list:
        matchobj = checker.match(line)
        if matchobj:
            line_slave_number = int(matchobj.group(1))
            if max_slave_number < line_slave_number:
                max_slave_number = line_slave_number
                max_slave_name = matchobj.group()
    util.debug_print('max slave name is: ' + max_slave_name)
    
    return max_slave_name

def decommission():
    util.debug_print('Trying to decommision')
    toBeRemovedSlaveName = getLastSlaveName()
    
    newLine = toBeRemovedSlaveName + "\n"
    util.updateFile('excludes', newLine)


    ssh = SSHWrapper.SSHWrapper(config.MASTER_IP)
    
    util.debug_print('trying to hdfs dfsadmin -refreshNodes')
    outmsg, errmsg = ssh.sudo_command('sudo -S su hduser -c "/home/hduser/hadoop-2.7.0/bin/hdfs dfsadmin -refreshNodes"')
    util.debug_print(outmsg)
    util.debug_print(errmsg)

    util.debug_print('trying to yarn rmadmin -refreshNodes')
    outmsg, errmsg = ssh.sudo_command('sudo -S su hduser -c "/home/hduser/hadoop-2.7.0/bin/yarn rmadmin -refreshNodes"')
    util.debug_print(outmsg)
    util.debug_print(errmsg)

    
    
# basic global stuff
api, pp = util.setup()
