'''
Created on Mar 10, 2016

PROPS: https://cwiki.apache.org/confluence/display/CLOUDSTACK/Simple+class+for+making+API+calls,+Python
'''
api_url = 'http://sfucloud.ca:8080/client/api'
apiKey = '6Lj2ZotMNCIW9xi9z1WROT9uOKZnrMelzAJ6hkTNj7HJDVykEvxAv8KmJ0uUAN_uRs-xNTr4ZbAjB3VMAYVUkg'
secret = 'AWteZfbIn93DxMmCb75gghypMGPnYcBV-et__7M7xPMan1rTUWR5DVYLXrLLMTJrN35qOLaBlJrHhGPdo-N7Cg'
 
import hashlib, hmac, string, base64, urllib
import json, urllib
 
class SignedAPICall(object):
    def __init__(self, api_url, apiKey, secret):
        self.api_url = api_url
        self.apiKey = apiKey
        self.secret = secret
 
    def request(self, args):
        args['apiKey'] = self.apiKey
 
        self.params = []
        self._sort_request(args)
        self._create_signature()
        self._build_post_request()
 
    def _sort_request(self, args):
        keys = sorted(args.keys())
 
        for key in keys:
            self.params.append(key + '=' + urllib.quote_plus(args[key]))
 
    def _create_signature(self):
        self.query = '&'.join(self.params)
        digest = hmac.new(
            self.secret,
            msg=self.query.lower(),
            digestmod=hashlib.sha1).digest()
 
        self.signature = base64.b64encode(digest)
 
    def _build_post_request(self):
        self.query += '&signature=' + urllib.quote_plus(self.signature)
        self.value = self.api_url + '?' + self.query
 
class CloudStack(SignedAPICall):
    def __getattr__(self, name):
        def handlerFunction(*args, **kwargs):
            if kwargs:
                return self._make_request(name, kwargs)
            return self._make_request(name, args[0])
        return handlerFunction
 
    def _http_get(self, url):
        response = urllib.urlopen(url)
        return response.read()
 
    def _make_request(self, command, args):
        args['response'] = 'json'
        args['command'] = command
        self.request(args)
        data = self._http_get(self.value)
        # The response is of the format {commandresponse: actual-data}
        key = command.lower() + "response"
        return json.loads(data)[key]
 
#Usage
 
#api = CloudStack(api_url, apiKey, secret)
 
#request = {'listall': 'true'}
#result = api.listVirtualMachines(request)
#print "count", result['count']
#print "api url", api.value
