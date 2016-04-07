__author__ = 'walthermaciel'

from load_balancer import compute_cluster_load, get_balancer_state
from health_check import get_cluster_metrics
import config
import datetime
from time import sleep


def build_log_header():
    metrics = get_cluster_metrics(config.MASTER_IP, config.METRIC_PORT)

    header_string = 'time,'
    for k in metrics.keys():
        header_string += str(k) + ','
    header_string += 'load,state,patience\n'
    return header_string


def build_log_line():
    final_string = ''

    metrics = get_cluster_metrics(config.MASTER_IP, config.METRIC_PORT)
    load = compute_cluster_load()
    timestamp = datetime.datetime.now().isoformat()
    state, patience = get_balancer_state()

    final_string += str(timestamp) + ','

    for mv in metrics.values():
        final_string += str(mv) + ','

    final_string += str(load) + ','

    final_string += str(state) + ','

    final_string += str(patience) + '\n'

    return final_string


def log_now():
    fp = open(config.LOG_FILE_PATH, 'w')
    header = build_log_header()
    fp.write(header)
    fp.close()

    while True:
        log_line = build_log_line()
        fp = open(config.LOG_FILE_PATH, 'a')
        fp.write(log_line)
        fp.close()
        sleep(1)

if __name__ == '__main__':
    log_now()
