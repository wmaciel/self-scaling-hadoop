__author__ = 'walthermaciel'
import time
import datetime

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
from config import BALANCER_LOG_FILE_PATH


def init_log(path):
    log_fp = open(path, 'w')
    if log_fp is None:
        print 'Fatal error, log file could not be opened'
        exit()
    else:
        log_fp.write('time,state,patience\n')
        log_fp.close()


def log_load(load, state, patience):
    timestamp = datetime.datetime.now().isoformat()
    log_fp = open(BALANCER_LOG_FILE_PATH, 'a')
    log_fp.write(timestamp + ',' + state + ',' + str(patience) + '\n')
    log_fp.close()


def compute_cluster_load(w_queue = None, w_memory = None, w_cpu = None):
    if w_queue is None:
        w_queue = QUEUE_WEIGHT
    if w_memory is None:
        w_memory = MEMORY_WEIGHT
    if w_cpu is None:
        w_cpu = CPU_WEIGHT
    
    metrics = health_check.get_cluster_metrics()
    apps_pending = int(metrics['appsPending'])
    apps_running = int(metrics['appsRunning'])
    allocated_mb = int(metrics['allocatedMB'])
    total_mb = int(metrics['totalMB'])
    allocated_vcores = int(metrics['allocatedVirtualCores'])
    total_vcores = int(metrics['totalVirtualCores'])

    # Avoid ripping a hole trough the space time continuum
    if apps_pending == 0:
        queue_load = 0
    else:
        queue_load = float(apps_pending) / \
                     sum([apps_pending, apps_running])

    memory_load = float(allocated_mb) / total_mb

    cpu_load = float(allocated_vcores) / total_vcores

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
    global g_patience
    util.debug_print('LOW state with patience: ' + str(patience))
    load = compute_cluster_load()
    while load < low_threshold:
        patience -= 1
        log_load(load, 'low', patience)
        g_patience = patience
        time.sleep(SLEEP)
        
        util.debug_print('patience: ' + str(patience) + ',\tload: ' + str(load))
        if patience < 0:
            util.debug_print('patience is 0, downsize!')
            downsize_cluster()
            time.sleep(BIG_SLEEP)
            break

        load = compute_cluster_load()

    return patience


def high_state(threshold, high_threshold, patience):
    global g_patience
    global g_state
    util.debug_print('HIGH state with patience: ' + str(patience))
    load = compute_cluster_load()

    while load > high_threshold:
        if load > threshold:
            patience -= 2
            log_load(load, 'very high', patience)
            g_state = 'very high'
        else:
            patience -= 1
            log_load(load, 'high', patience)
            g_state = 'high'

        g_patience = patience

        time.sleep(SLEEP)
        util.debug_print('patience: ' + str(patience) + ',\tload: ' + str(load))
        if patience < 0:
            util.debug_print('patience is 0, UPSIZE!')
            upsize_cluster()
            time.sleep(BIG_SLEEP)
            break
        
        load = compute_cluster_load()

    return patience


def main(threshold):
    global g_patience
    global g_state

    high_threshold = HIGH_STATE_PERCENTAGE * threshold
    low_threshold = LOW_STATE_PERCENTAGE * threshold
    patience = INITIAL_PATIENCE
    util.debug_print('high_threshold: ' + str(high_threshold))
    util.debug_print('low_threshold: ' + str(low_threshold))

    last_state = None

    init_log(BALANCER_LOG_FILE_PATH)

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
            util.debug_print('GOOD state with patience: ' + str(patience))
            patience += 1
            time.sleep(SLEEP)
            util.debug_print('patience: ' + str(patience) + ',\tload: ' + str(load))
            log_load(load, 'good', patience)
            
        if patience > INITIAL_PATIENCE or patience <= 0:
            patience = INITIAL_PATIENCE


if __name__ == '__main__':
    main(THRESHOLD)
