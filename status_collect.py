# __author__ = 'eric wang'
# data 2016-11-04

import commands
import os
import time
import logging

log_format = '[%(asctime)s] [%(levelname)s] %(message)s'

logging.basicConfig(format=log_format, filename='status_collect.log', datefmt='%Y-%m-%d %H:%M:%S %p', filemode="a", level=logging.INFO)

ip = '10.187.230.41'


def collect_srs_status():
    cmd_get = "netstat -anlp |grep -i listen |grep 1935 |grep srs |wc"
    ret = commands.getstatusoutput(cmd_get)
    status = ret[1].split('  ')[3]
    cmd_set = 'echo ' + status + ' > /export/srs-2.0release/trunk/objs/nginx/html/' + ip + '_srs.data'
    ret = os.system(cmd_set)
    if ret != 0:
        logging.info("the updata of srs data failed !!!")


def collect_nginx_status():
    cmd_get = "netstat -anlp |grep -i listen |grep 80 |grep nginx |wc"
    ret = commands.getstatusoutput(cmd_get)
    status = ret[1].split('  ')[3]
    cmd_set = 'echo ' + status + ' > /export/srs-2.0release/trunk/objs/nginx/html/' + ip + '_nginx.data'
    ret = os.system(cmd_set)
    if ret != 0:
        logging.info("the update of nginx data failed !!!")


def collect_nginx_clients():
    cmd_get = "netstat -anlp |grep worker |wc"
    ret = commands.getstatusoutput(cmd_get)
    status = ret[1].split('  ')[3]
    cmd_set = 'echo ' + status + ' > /export/srs-2.0release/trunk/objs/nginx/html/' + ip + '_nginx_clients.data'
    ret = os.system(cmd_set)
    if ret != 0:
        logging.info("the updata of nginx_clients data failed !!!")


if __name__ == "__main__":

    while True:
        collect_srs_status()
        collect_nginx_status()
        collect_nginx_clients()

        time.sleep(5)
