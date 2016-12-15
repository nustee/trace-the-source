#__author__ = 'eric wang'
# version 1.0 date 2016-11-16 ---- create the file


import commands
import os
import time
from time import ctime
import datetime
import threading
from global_var import *
import urllib2
import md5
import smtplib
from email.mime.text import MIMEText
import hashlib
import logging
import multiprocessing
from multiprocessing import Process
import httplib
import json


log_format = '[%(asctime)s] [%(levelname)s] %(message)s'

logging.basicConfig(format=log_format, filename='servicewarning.log', datefmt='%Y-%m-%d %H:%M:%S %p', filemode="a", level=logging.INFO)


def send_email(content, mailto, get_sub):

    try:

        logging.info('connecting %s', mail_host)
        s = smtplib.SMTP(mail_host, 25)

        logging.info('login to mail_host')
        s.login(mail_user, mail_pwd)

        for i in range(len(content)):
            msg = MIMEText(content[i].encode('utf8'), _subtype='html', _charset='utf8')
            msg['From'] = mail_user
            msg['Subject'] = u'%s' % get_sub
            msg['To'] = ",".join(mailto)
            logging.info('send e-mail')
            s.sendmail("freshwarning@jd.com", mailto, msg.as_string())

        logging.info('close the connection between the mail server')
        s.close()
    except Exception as e:
        logging.info('Exception: %s', e)


def stream_detect_nv(stream_info):
    logging.info("This is the start of stream detect Process !!!")
    msg_flag = "Alarm of Freshwarning !!!"
    stop_status = "down"
    start_status = "up"

    while True:
        msg_context_alarm = []
        web_msg_start = []
        web_msg_stop = []
        stream_url = 'http://trace.jd.local/live/' + stream_info.get('title') + '/' + stream_info.get('stream') + key_rs
        dir_name = "/home/" + stream_info.get('title') + '_' + stream_info.get('stream') + "/"
        # find out if this dir exist,if not ,create new ;
        if os.path.exists(dir_name):
            cmd = 'rm -f ' + dir_name + '*'
            os.system(cmd)
        else:
            cmd = 'mkdir -p ' + dir_name
            os.system(cmd)

        remotefile_name = dir_name + stream_info.get('stream') + '.m3u8'

        # download the m3u8 file from the remote web server
        f0 = urllib2.urlopen(stream_url)
        data = f0.read()
        with open(remotefile_name, "wb") as code:
            code.write(data)
        md5_old = md5new(remotefile_name)
        print md5_old
        cmd = 'rm -f ' + dir_name + '*'
        os.system(cmd)
        # sleep 60s get a new m3u8 file
        time.sleep(time_wait)

        f1 = urllib2.urlopen(stream_url)
        data = f1.read()
        with open(remotefile_name, "wb") as code:
            code.write(data)

        md5_new = md5new(remotefile_name)
        print md5_new
        cmd = 'rm -f ' + dir_name + '*'
        os.system(cmd)
        # the md5_old is equal to the md5_new ,the m3u8 file has not change in last 10s,so the stream has stopped !
        if md5_old == md5_new:
            logging.info('The stream is %s,the old md5 is %s', remotefile_name, md5_old)
            logging.info('The stream is %s,new_md5 is %s', remotefile_name, md5_new)
            str_str = "The stream is stopped,the stream is : " + stream_info.get('title') + '_' + stream_info.get('stream')
            web_msg_tmp = stream_info.get('title') + '/' + stream_info.get('stream') + '.m3u8'
            msg_context_alarm.append(str_str)
            web_msg_stop.append(web_msg_tmp)
        else:
            web_msg_tmp = stream_info.get('title') + '/' + stream_info.get('stream') + '.m3u8'
            web_msg_start.append(web_msg_tmp)

        # send the bad status
        for j in range(len(web_msg_stop)):
            logging.info("send the alarm of web, the web msg is %s", web_msg_stop[j])
            ret = send_post_http(web_msg_stop[j], stop_status)
            if ret != 200:
                logging.info("the alarm_web info send failed, send again!")
                send_post_http(web_msg_stop[j], stop_status)
        # send the good status
        for k in range(len(web_msg_start)):
            logging.info("send the status of web, the web msg is %s", web_msg_start[k])
            ret = send_post_http(web_msg_start[k], start_status)
            if ret != 200:
                logging.info("the alarm_web info send failed, send again!")
                send_post_http(web_msg_start[k], start_status)
        if len(msg_context_alarm) != 0:
            send_email(msg_context_alarm, alarm_to_list, msg_flag)
            time.sleep(alarm_time_wait)


def md5new(file_name):

    cmd = "md5sum " + file_name
    ret = commands.getstatusoutput(cmd)
    tmp_ret = ret[1].split(' ')
    return tmp_ret[0]


def start_restore_all_alarm_web():
    begin_status = "up"
    logging.info("send all restore alarms info to web at the start time")
    for i in range(len(stream_list)):
        stream_str = stream_list[i].get("title") + '/' + stream_list[i].get("stream") + '.m3u8'
        send_post_http(stream_str, begin_status)


def get_alarm_data_nv(proc_name):
    logging.info('This is the start of %s data process !!!!', proc_name)
    msg_flag = "Alarm of Freshwarning !!!"
    while True:
        msg_context_alarm = []
        for i in range(len(ip_list)):
            proc_str = ip_list[i] + '_' + proc_name + '.data'
            http_proc_req = get_http_info(ip_list[i], proc_str)
            if int(http_proc_req) == 0:
                str_str = "The warning server is : " + ip_list[i] + " the exit process name is :" + proc_name
                logging.info("This is the process warning:%s", str_str)
                msg_context_alarm.append(str_str)
        if len(msg_context_alarm) != 0:
            send_email(msg_context_alarm, alarm_to_list, msg_flag)

        time.sleep(1800)


def get_nginx_clients_data_nv():
    logging.info("This is the start of nginx clients process !!!!")
    msg_flag = "Alarm of Freshwarning !!!"
    while True:
        nginx_clients_total = 0
        msg_context_alarm = []
        for i in range(len(ip_list)):
            nginx_clients_num = get_nginx_http_info(ip_list[i])
            nginx_clients_total = nginx_clients_total + nginx_clients_num

        logging.info("the total nginx_clients is %d", nginx_clients_total)
        if nginx_clients_total >= 4000:
            logging.info("the total clients is larger than 4000,the number is :%d", nginx_clients_total)
            str_str = "The total client is larger than 4000, the number is: " + nginx_clients_total
            msg_context_alarm.append(str_str)
            put_http_info('1')
        else:
            put_http_info('0')
        if len(msg_context_alarm) != 0:
            send_email(msg_context_alarm, alarm_to_list, msg_flag)

        time.sleep(nginx_time_wait)


def get_http_info(ip_addr, str):

    url = 'http://' + ip_addr + '/' + str
    req = urllib2.Request(url)
    tmp = 255
    try:
        res_data = urllib2.urlopen(req)
    except urllib2.HTTPError, e:
        print e.code
        tmp = 0
    except urllib2.URLError, e:
        print e.args
        tmp = 0
    if tmp == 255:
        return res_data.read()
    else:
        return tmp


def get_nginx_http_info(ip_addr):

    url = 'http://' + ip_addr + '/' + 'nginx_status'
    req = urllib2.Request(url)
    tmp = 255
    try:
        res_data = urllib2.urlopen(req)
    except urllib2.HTTPError, e:
        print e.code
        tmp = 0
    except urllib2.URLError, e:
        print e.args
        tmp = 0
    if tmp == 255:
        tmp_str = res_data.readlines(1)
        str_num = tmp_str[0].split(':')
        return int(str_num[1])
    else:
        return tmp


def put_http_info(status):
    url = source_url + status
    request = urllib2.Request(url)
    request.add_header('Content-Type', 'application/json')
    request.get_method = lambda: 'GET'
    try:
        request = urllib2.urlopen(request)
    except urllib2.URLError, e:
        print e.code
        logging.info("urllib2 error , the error code is d%", e.code)
    return request.getcode()


def send_post_http(stream_source, stream_status):
    tmp_str = "http://freshremote1.jd.com/live/" + stream_source
    p = {"source": tmp_str, "status": stream_status}
    headers = {"Content-Type": "application/json"}
    conn = httplib.HTTPConnection(web_addr)
    conn.request("POST", "/resource/update", json.dumps(p), headers)
    response = conn.getresponse()
    return response.status


if __name__ == "__main__":

    srs_str = 'srs'
    nginx_str = 'nginx'

    logging.info('The start python time is: %s', ctime())

    start_restore_all_alarm_web()
    logging.info("send the restore msg of all channels to web. %s", ctime())

    # the start of the alarm system ,init the system
    put_http_info('0')

    t_list = []
 
    t0 = Process(target=get_alarm_data_nv, args=(srs_str,))
    t0.daemon = True
    t_list.append(t0)

    t1 = Process(target=get_alarm_data_nv, args=(nginx_str,))
    t1.daemon = True
    t_list.append(t1)

    t2 = Process(target=get_nginx_clients_data_nv, args=())
    t2.daemon = True
    t_list.append(t2)

    for i in range(len(stream_list)):
        t3 = Process(target=stream_detect_nv, args=(stream_list[i],))
        t3.daemon = True
        t_list.append(t3)

    print t_list

    for t in t_list:
        t.start()

    for t in t_list:
        t.join()

    logging.info('all over python time is: %s', ctime())
