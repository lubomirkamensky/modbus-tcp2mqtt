#!/usr/bin/python3
# Simple MQTT publishing of Modbus TCP sources
#
# Written and (C) 2018 by Lubomir Kamensky <lubomir.kamensky@gmail.com>
# Provided under the terms of the MIT license
#
# Requires:
# - pyModbusTCP - https://github.com/sourceperl/pyModbusTCP
# - Eclipse Paho for Python - http://www.eclipse.org/paho/clients/python/
#

import argparse
import logging
import logging.handlers
import time
import paho.mqtt.client as mqtt
import sys
import configparser
from pyModbusTCP.client import ModbusClient
    
parser = argparse.ArgumentParser(description='Bridge between Modbus TCP and MQTT')
parser.add_argument('--mqtt-host', default='localhost', help='MQTT server address. \
                     Defaults to "localhost"')
parser.add_argument('--mqtt-port', default='1883', type=int, help='MQTT server port. \
                    Defaults to 1883')
parser.add_argument('--mqtt-topic', default='json', help='Topic prefix to be used for \
                    subscribing/publishing. Defaults to "modbus/"')
parser.add_argument('--modbus-host', help='Modbus server address')
parser.add_argument('--modbus-port', default='502', type=int, help='Modbus server port. \
                    Defaults to 502')
parser.add_argument('--registers', help='Register definition file. Required!')
parser.add_argument('--frequency', default='30', help='How often is the source \
                    checked for the changes, in seconds. Only integers. Defaults to 30')
parser.add_argument('--only-changes', default='False', help='When set to True then \
                    only changed values are published')

args=parser.parse_args()

logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

topic=args.mqtt_topic
if not topic.endswith("/"):
    topic+="/"
frequency=int(args.frequency)

lastValue = {}

config = configparser.ConfigParser()
config.read(args.registers)
inputRegisters = config['Input-Registers']
holdingRegisters = config['Holding-Registers']

# Any received value in the upper range (32768-65535)
# is interpreted as negative value (in the range -32768 to -1). 
def reMap(value, maxInput=65535, minInput=64535, maxOutput=-1, minOutput=-1001):

    if value >= minInput:
        value = maxInput if value > maxInput else value
        value = minInput if value < minInput else value

        inputSpan = maxInput - minInput
        outputSpan = maxOutput - minOutput

        scaledThrust = float(value - minInput) / float(inputSpan)

        return minOutput + (scaledThrust * outputSpan)
    else:
        return value

class Element:
    def __init__(self,row):
        self.topic=row[0]
        self.value=row[1]

    def publish(self):
        try:
            if self.value!=lastValue.get(self.topic,0) or args.only_changes == 'False':
                lastValue[self.topic] = self.value
                fulltopic=topic+self.topic
                logging.info("Publishing " + fulltopic)
                mqc.publish(fulltopic,reMap(self.value),qos=0,retain=False)

        except Exception as exc:
            logging.error("Error reading "+self.topic+": %s", exc)

try:
    mqc=mqtt.Client()
    mqc.connect(args.mqtt_host,args.mqtt_port,10)
    mqc.loop_start()

    c = ModbusClient()
    # define modbus server host, port
    c.host(args.modbus_host)
    c.port(args.modbus_port)

    while True:
        # open or reconnect TCP to server
        if not c.is_open():
            if not c.open():
                logging.error("unable to connect to "+args.mqtt_host+":"+str(args.mqtt_port))

        data = []
        for key, value in inputRegisters.items():
            if c.is_open():
                row = c.read_input_registers(int(value))
                row.insert(0,key)
                data.append(row)

        
        for key, value in holdingRegisters.items():
            if c.is_open():
                row = c.read_holding_registers(int(value))
                row.insert(0,key)
                data.append(row)

        elements=[]

        for row in data:
            e=Element(row)
            elements.append(e)

        for e in elements:
            e.publish()
        
        time.sleep(int(frequency))

except Exception as e:
    logging.error("Unhandled error [" + str(e) + "]")
    sys.exit(1)
    
