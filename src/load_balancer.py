__author__ = 'walthermaciel'
import time

import upsize
import downsize
import health_check

from config import INITIAL_PATIENCE
from config import SLEEP
from config import BIG_SLEEP
from config import QUEUE_WEIGHT
from config import MEMORY_WEIGHT
from config import CPU_WEIGHT
from config import HIGH_STATE_PERCENTAGE
from config import LOW_STATE_PERCENTAGE
from config import THRESHOLD


def compute_cluster_load(w_queue, w_memory, w_cpu):
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
    while compute_cluster_load() < low_threshold:
        patience -= 1
        time.sleep(SLEEP)

        if patience < 0:
            downsize_cluster()
            time.sleep(BIG_SLEEP)
            break

    return patience


def high_state(threshold, high_threshold, patience):
    load = compute_cluster_load()

    while load > high_threshold:
        if load > threshold:
            patience -= 2
        else:
            patience -= 1

        time.sleep(SLEEP)

        if patience < 0:
            upsize_cluster()
            time.sleep(BIG_SLEEP)
            break

    return patience


def main(threshold, w_queue, w_memory, w_cpu):
    high_threshold = HIGH_STATE_PERCENTAGE * threshold
    low_threshold = LOW_STATE_PERCENTAGE * threshold
    patience = INITIAL_PATIENCE

    last_state = None

    while True:
        load = compute_cluster_load(w_queue, w_memory, w_cpu)
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

        if patience > INITIAL_PATIENCE or patience <= 0:
            patience = INITIAL_PATIENCE


if __name__ == '__main__':
    main(THRESHOLD, QUEUE_WEIGHT, MEMORY_WEIGHT, CPU_WEIGHT)
