import simpleCloudStackRest # super simple class for doing cloudstack api calls
import secretSause  # file that includes secret stuff!
import pprint   # pretty printing
import sys  # argument passing from commandline
import os   # to get environmental variables and to see if file exists
import re
import SSHWrapper

# function that creates/sets the global counter
def getNextSlaveName(filename=None):
    DEFAULT_GLOBAL_FILENAME = '/home/cloud/cmpt733_global_counter.txt'
    BASE_SLAVE_NAME = 'dlw-Slave'
    SLAVE_NAMING_REGEX = BASE_SLAVE_NAME+'(\d+)'

    # make filename correct
    if filename is None:
        filename = DEFAULT_GLOBAL_FILENAME

    # now check if file exists
    next_name = ''
    if os.path.isfile(filename):
        # get value of file
        with open(filename, 'r+') as fh: 
            max_slave = int(fh.read()) + 1 
            next_name = BASE_SLAVE_NAME + str(max_slave)

        # update value of file
        with open(filename, 'w') as fh: 
            fh.write(str(max_slave))
    else:
        # ok, file does NOT exist, now we need to create that global counter file!

        # first get all machines
        api, pp = _setup()
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
        checker = re.compile(SLAVE_NAMING_REGEX)
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
        next_name = BASE_SLAVE_NAME + str(max_slave)

    # return new name!
    return next_name

def main(argv):
    # some constants..... We could be smarter, but let's just get going first. Walk before Running
    templateid = 'db071a7a-510a-472f-99a6-5bf19f05cf9d'
    serviceofferingid = '294442fc-cb8e-47aa-b768-ca0f95054b95'
    zoneid = 'c687b45d-2822-43bc-a061-3399e92581d0'

    # basic setting up of api and stuff
    api, pp = _setup()

    # now we need to get the next slave name 
    next_name = getNextSlaveName()
    if not next_name:
        pp.pprint('getting the next name failed.')
        return -1

    # try to deploy with new slave with correct name
    result = api.deployVirtualMachine({ 'serviceofferingid': serviceofferingid,
                                        'zoneid': zoneid,
                                        'templateid': templateid,
                                        'displayname': next_name,
                                        'name': next_name })

    # now we wait for the async deployVirtualMachine() to finsih
    while True:
        deploy_status = api.queryAsyncJobResult({'jobId': result.get('jobid')})
        job_status = int( deploy_status.get('jobstatus') )

        if job_status == 1:
            break;
        elif job_status == 2:
            print next_name + ": " + str(deploy_status.get('jobresult'))
            pp.pprint(deploy_status)
            return -2

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
    print ssh.command('touch asdfdlw.txt')
    '''
    user_password = os.environ.get('SSH_USER_PASSWORD') # we need it setup as environmental variable
    sleep_time = 1
    while True:
        try:
            timer.sleep(sleep_time)
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, username='cloud', password=user_password)

            # now we do simplest touch command for testing
            stdin, stdout, stderr = ssh.exec_command("touch ~/test_dlw.txt")

            # now we can get out of this loop!
            break;
        except:
            sleep_time = sleep_time * 2
            if sleep_time > MAX_SLEEP_TIME:
                break;
    '''

    #pp.pprint(result2)

def _setup():
    # setup basic api stuff
    api = simpleCloudStackRest.CloudStack(secretSause.api_url, secretSause.apiKey, secretSause.secret)
    pp = pprint.PrettyPrinter(depth=6)
    return api, pp

if __name__ == "__main__":
    main(sys.argv[1:]) # [1:] strips out [0]

