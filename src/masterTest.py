import paramiko # for doing ssh stuff
import simpleCloudStackRest # super simple class for doing cloudstack api calls
import secretSause  # file that includes secret stuff!
import pprint   # pretty printing
import sys  # argument passing from commandline
import time # so we can sleep during vm creation to give create time to assign ip
import os   # to get environmental variables

def main(argv):
    # some constants..... We could be smarter, but let's just get going first. Walk before Running
    templateid = 'db071a7a-510a-472f-99a6-5bf19f05cf9d'
    serviceofferingid = '294442fc-cb8e-47aa-b768-ca0f95054b95'
    zoneid = 'c687b45d-2822-43bc-a061-3399e92581d0'

    # basic setting up of api and stuff
    api, pp = _setup()

    # now we need to use the api to create a new VM
    result = api.deployVirtualMachine({'serviceofferingid': serviceofferingid, 'zoneid':zoneid, 'templateid':templateid})
    time.sleep(10)   # sleep for 5 seconds to let vm get assigned ip

    # now get ip of new machine 
    result2 = api.listVirtualMachines({'id': result.get("id") })
    pp.pprint(result2)
    ip = result2.get('virtualmachine')[0].get('nic')[0].get('ipaddress')
    pp.pprint(ip)
    
    # finally, our simple command!
    # TODO: create function that looks for global counter file, if not found, then do an api call to
    # get list and use regex to get count/max number, then create the global counter file.  If
    # global counter file found, then we just pull from that and update it to the next increment
    new_hostname = 'testSlave'
    
    # now we initialize the ssh connection 
    user_password = os.environ.get('SSH_USER_PASSWORD') #we need it setup as environmental variable
    pp.pprint(user_password)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username='cloud', password=user_password)

    # now we do simplest touch command for testing
    stdin, stdout, stderr = ssh.exec_command("touch ~/test_loong.txt")
    
    #pp.pprint(result2)

def _setup():
    # setup basic api stuff
    api = simpleCloudStackRest.CloudStack(secretSause.api_url, secretSause.apiKey, secretSause.secret)
    pp = pprint.PrettyPrinter(depth=6)
    return api, pp

if __name__ == "__main__":
    main(sys.argv[1:]) # [1:] strips out [0]

