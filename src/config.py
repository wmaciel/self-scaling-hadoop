'''
Created on Mar 21, 2016

@author: loongchan
'''
###### USED FOR SLAVE NAME STUFF ######
DEFAULT_GLOBAL_COUNTER_FILENAME = '/home/cloud/cmpt733_global_counter.txt'
BASE_SLAVE_NAME = 'dlw-Slave'
SLAVE_NAMING_REGEX = BASE_SLAVE_NAME+'(\d+)'

###### USED FOR HOSTS FILE STUFF ######
DEFAULT_GLOBAL_HOSTS_FILENAME = '/home/cloud/hosts'
MASTER_IP = '199.60.17.143'


###### SSH RETRY MAX TIME #####
MAX_SLEEP_TIME = 20

###### STUFF FOR CREATING MACHINE ######
TEMPLATEID = 'db071a7a-510a-472f-99a6-5bf19f05cf9d'
SERVICEOFFERINGID = '294442fc-cb8e-47aa-b768-ca0f95054b95'
ZONEID = 'c687b45d-2822-43bc-a061-3399e92581d0'