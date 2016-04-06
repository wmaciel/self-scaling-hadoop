__author__ = 'walthermaciel'
import time

import upsize
import downsize
import health_check
import util

from config import INITIAL_PATIENCE
from config import SLEEP
from config import BIG_SLEEP
from config import QUEUE_WEIGHT
from config import MEMORY_WEIGHT
from config import CPU_WEIGHT
from config import HIGH_STATE_PERCENTAGE
from config import LOW_STATE_PERCENTAGE
from config import THRESHOLD


def compute_cluster_load(w_queue = None, w_memory = None, w_cpu = None):
    if w_queue is None:
        w_queue = QUEUE_WEIGHT
    if w_memory is None:
        w_memory = MEMORY_WEIGHT
    if w_cpu is None:
        w_cpu = CPU_WEIGHT
    
    metrics = health_check.get_cluster_metrics()
    queue_load = float(int(metrics['appsPending'])) / \
                 sum([
                     int(metrics['appsSubmitted']),
                     int(metrics['appsPending']),
                     int(metrics['appsRunning'])
                 ])
    memory_load = float(int(metrics['totalMB']) - int(metrics['availableMB'])) / int(metrics['totalMB'])
    cpu_load = float(int(metrics['totalVirtualCores']) - int(metrics['availableVirtualCores'])) / int(metrics['totalVirtualCores'])

    return sum([
        w_queue * queue_load,
        w_memory * memory_load,
        w_cpu * cpu_load
    ]) / sum([QUEUE_WEIGHT, MEMORY_WEIGHT, CPU_WEIGHT])


def downsize_cluster():
    downsize.decommission(True)
    downsize.removeDecommissionedMachine()
    return True


def upsize_cluster():
    upsize.upsize()
    return True


def low_state(low_threshold, patience):
    util.debug_print('in low_state() with patience:' + str(patience))
    while compute_cluster_load() < low_threshold:
        patience -= 1
        time.sleep(SLEEP)
        
        util.debug_print('low patience is now: '+str(patience))
        if patience < 0:
            util.debug_print('patience is 0, downsize!')
            downsize_cluster()
            time.sleep(BIG_SLEEP)
            break

    return patience


def high_state(threshold, high_threshold, patience):
    util.debug_print('in high_state() with patience:'+str(patience))
    load = compute_cluster_load()

    while load > high_threshold:
        if load > threshold:
            patience -= 2
        else:
            patience -= 1

        time.sleep(SLEEP)
        
        util.debug_print('patience is now: '+str(patience))
        if patience < 0:
            util.debug_print('patience is 0, UPSIZE!')
            upsize_cluster()
            time.sleep(BIG_SLEEP)
            break
        
        load = compute_cluster_load()

    return patience


def main(threshold):
    high_threshold = HIGH_STATE_PERCENTAGE * threshold
    low_threshold = LOW_STATE_PERCENTAGE * threshold
    patience = INITIAL_PATIENCE
    util.debug_print('high_threshold: ' + str(high_threshold))
    util.debug_print('low_threshold: ' + str(low_threshold))

    last_state = None

    util.debug_print('Starting the main load balancer loop...')
    while True:
        load = compute_cluster_load()
        util.debug_print('current load is: ' + str(load))
        util.debug_print('last_state: ' + str(last_state))
        if load < low_threshold:
            if last_state != 'low':
                last_state = 'low'
                patience = INITIAL_PATIENCE
            patience = low_state(low_threshold, patience)
        elif load > high_threshold:
            if last_state != 'high':
                last_state = 'high'
                patience = INITIAL_PATIENCE
            patience = high_state(threshold, high_threshold, patience)
        else:
            patience += 1
            time.sleep(SLEEP)
            util.debug_print('not in high or low state, thus increment patience to: '+str(patience))
            
        if patience > INITIAL_PATIENCE or patience <= 0:
            patience = INITIAL_PATIENCE


if __name__ == '__main__':
    main(THRESHOLD)
