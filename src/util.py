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

    get_file_command = ''
    dest_filename = ''
    if fileType == 'hosts':
        if filename is None:
            filename = config.DEFAULT_LOCAL_HOSTS_FILENAME
        dest_filename = config.DEFAULT_DESTINATION_HOSTS_FILENAME
        file_owner = config.HOSTS_FILE_USER
    elif fileType == 'slaves':
        if filename is None:
            filename = config.DEFAULT_LOCAL_SLAVES_FILENAME
        dest_filename = config.DEFAULT_DESTINATION_SLAVES_FILENAME
        file_owner = config.SLAVES_FILE_USER
    else:
        return -4
    
    get_file_command = 'cat ' + dest_filename
    
    # init stuff for ssh
    ssh = SSHWrapper.SSHWrapper(config.MASTER_IP)
    
    # get hosts file from master...
    some_file_list, some_error = ssh.command(get_file_command)
    print some_file_list
    print some_error
    
    # append new line for new worker
    if newLine not in some_file_list: 
        some_file_list.append(newLine)
    
    # save file locally
    with open(filename, 'w') as fh:
        for line in some_file_list:
            fh.write('%s' % line)
    
    # now send updated hosts file back to master at cloud's directory
    ssh.put_sftp(filename, filename)
       
    # now copy hosts from destination to correct location on remote
    some_file_list, some_error =ssh.sudo_command('cp ' + filename + ' ' + dest_filename)
    print some_file_list
    print some_error
    
    # give correct ownership
    '''
    if fileType == 'hosts':
        some_file_list, some_error = ssh.sudo_command('chown root:root ' + dest_filename)
    elif fileType == 'slaves':
        some_file_list, some_error = ssh.sudo_command('chown  hduser:hadoop' + dest_filename)
    print some_file_list
    print some_error
    '''
    return True    
    
def debug_print(str):
    if config.DEBUG:
        pp.pprint(str)
        
api, pp = setup()
        
        
        
        
       
       
       
       
       
       
       