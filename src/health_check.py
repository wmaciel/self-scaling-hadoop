__author__ = 'walthermaciel'

import urllib2
import json


'''
Return a dictionary with metrics values about the cluster

Below is an example:
{
    "appsSubmitted":0,
    "appsCompleted":0,
    "appsPending":0,
    "appsRunning":0,
    "appsFailed":0,
    "appsKilled":0,
    "reservedMB":0,
    "availableMB":17408,
    "allocatedMB":0,
    "reservedVirtualCores":0,
    "availableVirtualCores":7,
    "allocatedVirtualCores":1,
    "containersAllocated":0,
    "containersReserved":0,
    "containersPending":0,
    "totalMB":17408,
    "totalVirtualCores":8,
    "totalNodes":1,
    "lostNodes":0,
    "unhealthyNodes":0,
    "decommissionedNodes":0,
    "rebootedNodes":0,
    "activeNodes":1
}
'''
def get_cluster_metrics(ip, port):
    address = 'http://' + str(ip) + ':' + str(port) + '/ws/v1/cluster/metrics'
    data = urllib2.urlopen(address).read()
    metrics = json.loads(data)['clusterMetrics']
    return metrics


def get_queue_size(ip, port):
    metrics = get_cluster_metrics(ip, port)
    return int(metrics['appsPending'])
