'''
Created on Mar 21, 2016

@author: loongchan
'''
import simpleCloudStackRest # super simple class for doing cloudstack api calls
import secretSause  # file that includes secret stuff!
import pprint   # pretty printing
import time
import SSHWrapper
import config
import re

def setup():
    # setup basic api stuff
    api = simpleCloudStackRest.CloudStack(secretSause.api_url, secretSause.apiKey, secretSause.secret)
    pp = pprint.PrettyPrinter(depth=6)
    return api, pp

def waitForAsync(jobid):
    SLEEP_FOR = 1   # so we don't flood the network with requests.... hopefully!
    while True:
        time.sleep(SLEEP_FOR)
        deploy_status = api.queryAsyncJobResult({'jobId': jobid})
        job_status = int( deploy_status.get('jobstatus') )

        if job_status == 1:
            break;
        elif job_status == 2:
            print str(deploy_status.get('jobresult'))
            pp.pprint(deploy_status)
            return -2
    
    return True

def updateFile(fileType='hosts', newLine = '', filename=None):
    debug_print('calling util.updateFile() with newLine: ' + newLine)
    get_file_command = ''
    dest_filename = ''
    if fileType == 'hosts':
        if filename is None:
            filename = config.DEFAULT_LOCAL_HOSTS_FILENAME
        dest_filename = config.DEFAULT_DESTINATION_HOSTS_FILENAME
    elif fileType == 'slaves':
        if filename is None:
            filename = config.DEFAULT_LOCAL_SLAVES_FILENAME
        dest_filename = config.DEFAULT_DESTINATION_SLAVES_FILENAME
    elif fileType == 'excludes':
        if filename is None:
            filename = config.DEFAULT_LOCAL_EXCLUDES_FILENAME
        dest_filename = config.DEFAULT_DESTINATION_EXCLUDES_FILENAME
    else:
        return -4 # random.... sorry.
    
    get_file_command = 'cat ' + dest_filename
    
    # init stuff for ssh
    ssh = SSHWrapper.SSHWrapper(config.MASTER_IP)
    
    # get file from master...
    some_file_list, some_error = ssh.command(get_file_command)
    debug_print(some_file_list)
    debug_print(some_error)
    
    # append new line for new worker
    if newLine not in some_file_list: 
        some_file_list.append(newLine)
    debug_print('updated file:')
    debug_print(some_file_list)
    
    # save file locally
    with open(filename, 'w') as fh:
        for line in some_file_list:
            fh.write('%s' % line)
    
    # now send updated hosts file back to master at cloud's directory
    debug_print('moving file from manager to master')
    ssh.put_sftp(filename, filename)
       
    # now copy hosts from destination to correct location on remote
    debug_print('trying to move from cloud directory: ' + filename + ' to final directory: ' + dest_filename )
    some_file_list, some_error =ssh.sudo_command('mv ' + filename + ' ' + dest_filename)
    debug_print(some_file_list)
    debug_print(some_error)
    
    debug_print('trying to change to correct file owner for ' + fileType)
    if fileType == 'hosts':
        some_file_list, some_error =ssh.sudo_command('chown root:root ' + dest_filename)
        debug_print(some_file_list)
        debug_print(some_error)
    elif fileType == 'slaves' or fileType == 'excludes':
        some_file_list, some_error =ssh.sudo_command('chown hduser:hadoop ' + dest_filename)
        debug_print(some_file_list)
        debug_print(some_error)
    else:
        return -4 # random.... sorry.
    
    return True    

def get_file_content(dest_filename, ip = None):
    '''
    Returns the content of the dest_filename
    Input: filename, ip
    Output: list of line of file
    '''
    debug_print('calling util.get_file_content()')
    get_file_command = 'cat ' + dest_filename
    
    if ip is None:
        ip = config.MASTER_IP
    
    # init stuff for ssh
    ssh = SSHWrapper.SSHWrapper(ip)
    
    # get file from master...
    some_file_list, some_error = ssh.sudo_command(get_file_command)
    debug_print(some_file_list)
    debug_print(some_error)
    
    return some_file_list

def update_hostname(ip, newName, vmID):
        # init stuff for ssh
    ssh = SSHWrapper.SSHWrapper(ip)
    
    filename = config.DEFAULT_LOCAL_HOSTNAME_FILENAME
    dest_filename = config.DEFAULT_DESTINATION_HOSTNAME_FILENAME
    
    # save file locally on manager
    with  open(filename, 'w') as fh:
        fh.write('%s\n' % newName)
        
    # move hostname file to slave 
    ssh.put_sftp(filename, filename)
    
    # copy from /home/cloud to /etc/hostname in slave
    debug_print('trying to mv from ' + filename + ' to ' + dest_filename)
    ssh.sudo_command('mv -f '+filename+' '+dest_filename)
    
    # restart machine
    restart_machine(vmID)
    
    
def restart_machine(vmID):
    result = api.rebootVirtualMachine({'id':vmID})
    
    waiting = waitForAsync(result.get('jobid'))
    
    if waiting != True: # whoops something went wrong!
        return waiting
    
    return True

def get_max_slavename(some_file_list, return_all = False):
    '''
    This function gets a list of slave names, one per line and either returns the "max" slave name
    Input: ['dlw-Slave2\n', 'dlw-Slave3\n']
    Output 'dlw-Slave3'
    '''
    debug_print('calling on util.get_max_slavename')
    
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
        debug_print('util.get_max_slave is returning list of slaves:')
        debug_print(all_slaves_list)
        return all_slaves_list
    else:
        debug_print('util.get_max_slave is returning: ' + max_slave_name)
        return max_slave_name
    
def debug_print(str):
    if config.DEBUG:
        pp.pprint(str)
        
api, pp = setup()
        
        
        
        
       
       
       
       
       
       
       