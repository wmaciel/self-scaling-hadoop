__author__ = 'walthermaciel'
import time

import upsize
import downsize
import health_check


def get_queue_size():
    # TODO:
    return 0


def get_cpu_load():
    # TODO:
    return 0


def get_memory_load():
    # TODO:
    return 0


def compute_cluster_load():
    # TODO:
    return 0


def downsize_cluster():
    downsize.decommission(True)
    downsize.removeDecommissionedMachine()
    
    return True

def upsize_cluster():
    upsize.upsize()
    
    return True


def low_state(low_threshold):
    patience = 50

    while compute_cluster_load() < low_threshold:
        patience -= 1
        time.sleep(10)

        if patience < 0:
            downsize_cluster()
            time.sleep(120)
            return


def high_state(threshold, high_threshold):
    patience = 50
    load = compute_cluster_load()

    while load > high_threshold:
        if load > threshold:
            patience -= 2
        else:
            patience -= 1

        time.sleep(10)

        if patience < 0:
            upsize_cluster()
            time.sleep(120)
            return


def main(threshold, w_queue, w_memory, w_cpu):
    high_threshold = 0.75 * threshold
    low_threshold = 0.25 * threshold

    while True:
        load = compute_cluster_load()
        if load < low_threshold:
            low_state(low_threshold)
        elif load > high_threshold:
            high_state(threshold, high_threshold)




if __name__ == '__main__':
    # Threshold for adding new machine
    threshold = 10

    # Queue size weight
    w_queue = 5

    # Memory load weight
    w_memory = 3

    # CPU load weight
    w_cpu = 1

    main(threshold, w_queue, w_memory, w_cpu)
