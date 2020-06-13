import paho.mqtt.client as mqtt
import time
from datetime import datetime
from datetime import timedelta
import random

import dbconfig
from dbhelper import DBHelper

import mqconfig
DB_HOST = dbconfig.IP_ADDR
DB = DBHelper(DB_HOST)

MQ_HOST = mqconfig.mq_host
MQ_TITLE = mqconfig.mq_title


count = 0
sample_count = 0
sample_freq = 10 # count of data in 1 sec.
record_freq = 1 # count of data to record in 1 sec.
sample_max = sample_freq / record_freq
sum_data = 0.0
sum_cpuusage = 0.0
sum_memtotal = 0.0
sum_memusage = 0.0
#cpu_use = 7.2
#mem_use = 34.4

BUF_MAX = record_freq
rec_buf = []

def pushData2DB(tim, dat):
    global count
    try:    
        print("{:d} {},{}".format(count, tim.strftime('%Y-%m-%d %H:%M:%S'), dat))
        DB.insertStatusRec(tim, dat)
        
    except Exception as e:
        print ("Exception at pushData2DB", e)

def on_connect(client, userdata, flags, rc):
    try:    
        print("Connect result: {}".format(mqtt.connack_string(rc)))
        client.connected_flag = True
        client.subscribe(MQ_TITLE, qos=1)
        
    except Exception as e:
        print ("Exception", e)

def on_subscribe(client, userdata, mid, granted_qos):
    print("Subscribed with QoS: {}".format(granted_qos[0]))

def on_message(client, userdata, msg):
    global count
    global sample_count
    global sum_data
    global sum_cpuusage
    global sum_memtotal
    global sum_memusage
    global sample_max
#    global cpu_use, mem_use
    
    try:    
        count +=1
        payload_string = msg.payload.decode('utf-8')
        print("{:d} Topic: {}. Payload: {}".format(count, msg.topic, payload_string))
    
        row_data = payload_string.split(",")
#        print("row_data = {}".format(row_data))
#       row_data = cpu temp, cpu use, mem total, mem use

        rec_time = datetime.strptime(row_data[0], "%Y-%m-%d %H:%M:%S.%f")
        sub_data = float(row_data[1])

        sub_cpuusage = float(row_data[2])
        sub_memtotal = float(row_data[3])
        sub_memusage = float(row_data[4])
    
        sample_count += 1
        sum_data += sub_data
        sum_cpuusage += sub_cpuusage
        sum_memtotal += sub_memtotal
        sum_memusage += sub_memusage
        
        #print(dev_name, rec_time, sub_data)
         
        if sample_count >= sample_max:
            #print(payload_string)
            avg_data = sum_data / sample_count
            avg_cpuusage = sum_cpuusage / sample_count
            avg_memtotal = sum_memtotal / sample_count
            avg_memusage = sum_memusage / sample_count
            #str_data = '{:.1f}'.format(avg_data)
            str_data = '{:.1f},{:.1f},{:.1f},{:.1f}'.format(avg_data, avg_cpuusage, avg_memtotal, avg_memusage)
#            ra = random.uniform(-1, 1)
#            cpu_use = max(0, min(100, cpu_use + ra*2))
#            mem_use = max(0, min(100, mem_use + ra*5))
            #str_data = str_data + ',{:.1f},{:.1f}'.format(cpu_use, mem_use)
#            str_data = str_data + cpu_use + mem_use
#            print(count, sample_count, rec_time, str_data)
#            print("str data = {0}".format(str_data))
            pushData2DB(rec_time, str_data)
            sample_count = 0
            sum_data = 0
            sum_cpuusage = 0.0
            sum_memtotal = 0.0
            sum_memusage = 0.0
    
    except Exception as e:
        print ("Exception", e)

if __name__ == "__main__":
    print ("get client")
    client = mqtt.Client("cpu/temp2")
    client.username_pw_set(mqconfig.mq_user, password=mqconfig.mq_password)
    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_message = on_message
    print ("Try to connect {} ".format(MQ_HOST))
    client.connect(MQ_HOST, 1883, 120)
    print ("connected {} ".format(MQ_HOST))
    client.loop_forever()

