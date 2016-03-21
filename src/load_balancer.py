__author__ = 'walthermaciel'

import time


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
    # TODO:


def upsize_cluster():
    # TODO:


def low_state():
    patience = 50
    low_threshold = 0.25 * threshold
    while compute_cluster_load() < low_threshold:
        patience -= 1
        time.sleep(10)
        if patience < 0:
            downsize_cluster()
            time.sleep(120)
            return


def high_state():
    patience = 50
    high_threshold = 0.75 * threshold
    while compute_cluster_load() > high_threshold:
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
            low_state()
        elif load > high_threshold:
            high_state()




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
