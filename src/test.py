import simpleCloudStackRest
import secretSause
import pprint

templateid = 'db071a7a-510a-472f-99a6-5bf19f05cf9d'
serviceofferingid = '294442fc-cb8e-47aa-b768-ca0f95054b95'
zoneid = 'c687b45d-2822-43bc-a061-3399e92581d0'
vmid = 'df8ac04e-2a8d-43c8-9f79-ce4d7b019611'

# since all will use these... just leave it here
api = simpleCloudStackRest.CloudStack(secretSause.api_url, secretSause.apiKey, secretSause.secret)
pp = pprint.PrettyPrinter(depth=6)

#delete vm
# result = api.destroyVirtualMachine({'id':vmid})
# pp.pprint(result)



# create vm
# result = api.deployVirtualMachine({'serviceofferingid': serviceofferingid, 'zoneid':zoneid, 'templateid':templateid})
# pp.pprint(result)



# list vm info
# request = {'listall': 'true', 'details':'all'}
# result = api.listVirtualMachines(request)
# print "count", result['count']
# pp.pprint(result)
# print "\n\n"
# print "api url", api.value