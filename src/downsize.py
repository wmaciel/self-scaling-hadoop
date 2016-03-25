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

def getAllSlaveNames():
    util.debug_print('called getLastSlaveName()')
    get_file_command = 'cat ' + config.DEFAULT_DESTINATION_SLAVES_FILENAME
    
    # connect to master node
    ssh = SSHWrapper.SSHWrapper(config.MASTER_IP)
    
    # get slaves file info from master...
    some_file_list, some_error = ssh.command(get_file_command)

    # get max slave node name
    return util.get_max_slavename(some_file_list, return_all=True)
    
def decommission():
    '''
    This function basically copies slave names from slaves list to excludes list and run refresh scripts
    Input: None
    Output: None
    '''
    util.debug_print('Trying to decommision')
    
    # get all slave names in slaves file
    all_slave_names = map(str.strip, getAllSlaveNames())
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
    
# basic global stuff
api, pp = util.setup()
