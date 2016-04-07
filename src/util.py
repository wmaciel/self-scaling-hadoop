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
from test import vmid

def setup():
    # setup basic api stuff
    api = simpleCloudStackRest.CloudStack(secretSause.api_url, secretSause.apiKey, secretSause.secret)
    pp = pprint.PrettyPrinter(depth=6)
    return api, pp

def waitForAsync(jobid):
    debug_print('waiting for job: ' + str(jobid))
    while True:
        time.sleep(config.ASYNC_SLEEP_FOR)
        deploy_status = api.queryAsyncJobResult({'jobId': jobid})
        job_status = int( deploy_status.get('jobstatus') )

        if job_status == 1:
            break;
        elif job_status == 2:
            debug_print(str(deploy_status.get('jobresult')))
            return -2
    
    debug_print('Done waiting for: ' + str(jobid))
    return True

def updateFile(fileType='hosts', newLine = '', filename=None, addLine=True):
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

    
    # append or remove newLine from file
    if addLine:
        if newLine not in some_file_list: 
            some_file_list.append(newLine)
    else:
        try:
            ind = some_file_list.index(newLine)
            del some_file_list[ind]
        except:
            debug_print('can not find line "' + newLine + '" in file: ' + dest_filename)
            return -5
    
    # save file locally
    with open(filename, 'w') as fh:
        for line in some_file_list:
            fh.write('%s' % line)
    
    # now send updated hosts file back to master at cloud's directory
    debug_print('moving file from manager to master')
    ssh.put_sftp(filename, filename)
       
    # now copy hosts from destination to correct location on remote
    debug_print('trying to move from cloud directory: ' + filename + ' to final directory: ' + dest_filename + ' at master')
    some_file_list, some_error =ssh.sudo_command('mv ' + filename + ' ' + dest_filename)
    
    debug_print('trying to change to correct file owner for ' + fileType)
    if fileType == 'hosts':
        some_file_list, some_error =ssh.sudo_command('chown root:root ' + dest_filename)
    elif fileType == 'slaves' or fileType == 'excludes':
        some_file_list, some_error =ssh.sudo_command('chown hduser:hadoop ' + dest_filename)
    else:
        return -6
    
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
    
    return some_file_list

def update_hostname(ip, newName, vmID):
    debug_print('calling update_hostname for ip: ' + str(ip) + ', with new name: ' + str(newName))
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
    ssh.sudo_command('mv -f '+filename+' '+dest_filename)
    
    # restart machine
    restart_machine(vmID, ip)
    
    
def restart_machine(vmID, ip):
    debug_print('calling restart_machine for: ' +str(vmID) + ' with ip: '+str(ip))
    result = api.rebootVirtualMachine({'id':vmID})

    waiting = waitForAsync(result.get('jobid'))
    
    if waiting != True: # whoops something went wrong!
        return waiting
        
    # make sure connection is valid for machine
    SSHWrapper.SSHWrapper(ip)
    
    debug_print('finish restarting machine: ' + str(vmID))
    return True

def get_vm_id_by_name(slaveName):
    '''
    convert slavename to vmid
    Input String slavename
    Output String vmid, or False if it can't find anything
    '''
    debug_print('calling util.get_vm_by_name')
    
    # first get all machines
    result = api.listVirtualMachines({'listall': 'true', 'details':'all'})

    # now check if it worked
    if 'errortext' in result:
        # oh man... failed!
        pp.pprint(result)
        return -7

    vms = result.get('virtualmachine')
    
    # now run though the list till we get the correct one.
    for vm in vms:
        test_name = vm.get('name')
        if test_name == slaveName:
            debug_print('For slave: ' + str(slaveName) + ' vmID is: ' + vm.get('id'))
            return vm.get('id')
    
    debug_print('Something is fishy as cannot find vmid for: ' + str(slaveName))
    return False

    
def debug_print(str):
    if config.DEBUG:
        pp.pprint(str)
        
api, pp = setup()
        
        
        
        
       
       
       
       
       
       
       