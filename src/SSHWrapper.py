'''
Created on Mar 20, 2016

@author: loongchan
'''
import paramiko # maybe try fabric as well????
import os # so we can get to environmental variables
import time # so we can do sleep!
import socket
import config
import util

class SSHWrapper():
    
    def __init__(self, ipAddr, username='cloud'):
        
        # setup and save some variables
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ip = ipAddr
        user_password = os.environ.get('SSH_USER_PASSWORD') # we need it setup as environmental variable
        
        # ok, try to establish connecion
        sleep_time = 1
        while True:
            try:
                time.sleep(sleep_time)
                blah = self.ssh.connect(self.ip, username=username, password=user_password) 
                break;
            except socket.error:
                sleep_time = sleep_time * 2
                if sleep_time > config.MAX_SLEEP_TIME:
                    break;
                print 'retrying to connect in ' + str(sleep_time) + ' seconds'
            except Exception ,e:
                print str(e)
                break
    

    def command(self, command_string):
        # run command
        stdin, stdout, stderr = self.ssh.exec_command(command_string)
        
        # get and return output
        stdout_data = stdout.readlines()
        stderr_data = stderr.readlines()
        
        return stdout_data, stderr_data
    
    def sudo_command(self, sudo_command_string, password = None):
        '''
        Runs the command, then send the password via stdin
        Input: String some commandline string
        Output: output, error 
        '''
        util.debug_print('calling SSHWrapper sudo_command')
        # add sudo to the command string
        if not sudo_command_string.strip().startswith('sudo'):
            sudo_command_string = 'sudo -S ' + sudo_command_string
        
        # run sudo command
        util.debug_print('calling command: ' + sudo_command_string)
        stdin, stdout, stderr = self.ssh.exec_command(sudo_command_string)

        # get password
        util.debug_print('getting password')
        if password is None:
            password = os.environ.get('SSH_USER_PASSWORD') # we need it setup as environmental variable
            
        # sleep just to make sure it's good
        util.debug_print('sleeping....just to make sure we get prompted for the password')
        time.sleep(2)
        
        # give password
        util.debug_print('passing password to stdin')
        stdin.write(password+'\n')
        stdin.flush()
        
        # get and return output
        stdout_data = stdout.readlines()
        stderr_data = stderr.readlines()
        
        return stdout_data, stderr_data
        
    def put_sftp(self, localfile, remotefile):
        ftp = self.ssh.open_sftp()
        ftp.put(localfile, remotefile)
        return True
        
    def __del__(self):
        self.ssh.close()
        
        
        