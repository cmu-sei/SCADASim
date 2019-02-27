#!/bin/python
# SCADA Simulator
#
# Copyright 2018 Carnegie Mellon University. All Rights Reserved.
#
# NO WARRANTY. THIS CARNEGIE MELLON UNIVERSITY AND SOFTWARE ENGINEERING INSTITUTE MATERIAL IS FURNISHED ON AN "AS-IS" BASIS. CARNEGIE MELLON UNIVERSITY MAKES NO WARRANTIES OF ANY KIND, EITHER EXPRESSED OR IMPLIED, AS TO ANY MATTER INCLUDING, BUT NOT LIMITED TO, WARRANTY OF FITNESS FOR PURPOSE OR MERCHANTABILITY, EXCLUSIVITY, OR RESULTS OBTAINED FROM USE OF THE MATERIAL. CARNEGIE MELLON UNIVERSITY DOES NOT MAKE ANY WARRANTY OF ANY KIND WITH RESPECT TO FREEDOM FROM PATENT, TRADEMARK, OR COPYRIGHT INFRINGEMENT.
#
# Released under a MIT (SEI)-style license, please see license.txt or contact permission@sei.cmu.edu for full terms.
#
# [DISTRIBUTION STATEMENT A] This material has been approved for public release and unlimited distribution.  Please see Copyright notice for non-US Government use and distribution.
# This Software includes and/or makes use of the following Third-Party Software subject to its own license:
# 1. Packery (https://packery.metafizzy.co/license.html) Copyright 2018 metafizzy.
# 2. Bootstrap (https://getbootstrap.com/docs/4.0/about/license/) Copyright 2011-2018  Twitter, Inc. and Bootstrap Authors.
# 3. JIT/Spacetree (https://philogb.github.io/jit/demos.html) Copyright 2013 Sencha Labs.
# 4. html5shiv (https://github.com/aFarkas/html5shiv/blob/master/MIT%20and%20GPL2%20licenses.md) Copyright 2014 Alexander Farkas.
# 5. jquery (https://jquery.org/license/) Copyright 2018 jquery foundation.
# 6. CanvasJS (https://canvasjs.com/license/) Copyright 2018 fenopix.
# 7. Respond.js (https://github.com/scottjehl/Respond/blob/master/LICENSE-MIT) Copyright 2012 Scott Jehl.
# 8. Datatables (https://datatables.net/license/) Copyright 2007 SpryMedia.
# 9. jquery-bridget (https://github.com/desandro/jquery-bridget) Copyright 2018 David DeSandro.
# 10. Draggabilly (https://draggabilly.desandro.com/) Copyright 2018 David DeSandro.
# 11. Business Casual Bootstrap Theme (https://startbootstrap.com/template-overviews/business-casual/) Copyright 2013 Blackrock Digital LLC.
# 12. Glyphicons Fonts (https://www.glyphicons.com/license/) Copyright 2010 - 2018 GLYPHICONS.
# 13. Bootstrap Toggle (http://www.bootstraptoggle.com/) Copyright 2011-2014 Min Hur, The New York Times.
# DM18-1351
#

from pymodbus.server.sync import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from PLC_Engine import Actuator
from PLC_Engine import Sensor
from PLC_Engine import PLC
import threading
import requests
import getopt
import sys
import time
import os

arduino_modules = {"actuators": [], "status": None, "sensors": [], "config": {}}
status = True
server_ip = {}
client_ip = {}

store = ModbusSlaveContext(
    di = ModbusSequentialDataBlock(0, [17]*100),
    co = ModbusSequentialDataBlock(0, [17]*100),
    hr = ModbusSequentialDataBlock(0, [17]*100),
    ir = ModbusSequentialDataBlock(0, [17]*100))
context = ModbusServerContext(slaves=store, single=True)


identity = ModbusDeviceIdentification()
identity.VendorName  = 'Facility Sensor System'
identity.ProductCode = 'FSS'
identity.VendorUrl   = 'http://www.wehaveyourback.com'
identity.ProductName = 'PLC Sensor Server'
identity.ModelName   = 'Sensor Server 5000'
identity.MajorMinorRevision = '3.a1'



def controller_server():
    StartTcpServer(context, identity=identity, address=(server_ip['ip'], int(server_ip['port'])))

def controller_client():
    print "Client"
    depend = {}
    if "actuators" in arduino_modules['config']:
        for i in arduino_modules['config']["actuators"]:
            b = arduino_modules['config']["actuators"][i]
            print i
            if "status" in i.lower():
                arduino_modules["status"] = Actuator(b["initial_value"], b["device_num"])
            else:
                arduino_modules["actuators"].append(Actuator(b["initial_value"], b["device_num"]))
                if "relationship_id" in b:
                    depend[b["id"]] = {"type": b["relationship_type"], "id": b["relationship_id"], "reg_num": b["device_num"]}
            write_reg(b["device_num"], b["initial_value"])
    if "sensors" in arduino_modules['config']:
        for i in arduino_modules['config']["sensors"]:
            b = arduino_modules['config']["sensors"][i]
            if b["id"] in str(depend):
                p = None
                n = None
                for i in depend:
                    if "positive" in str(depend[i]).lower() and b["id"] in str(depend[i]):
                        p = depend[i]["reg_num"]
                    elif "negative" in str(depend[i]).lower() and b["id"] in str(depend[i]):
                        n = depend[i]["reg_num"]
                    elif b["id"] in str(depend[i]):
                        p = depend[i]["reg_num"]
                        break
                print "P: %s, N: %s" % (p,n)
                sen = Sensor(b["initial_value"], b["device_num"], b["threshold"], b["variability"], b["type"], p, n)
            else:
                sen = Sensor(b["initial_value"], b["device_num"], b["threshold"], b["variability"], b["type"])
            arduino_modules["sensors"].append(sen)
            write_reg(b["device_num"], b["initial_value"])
    plc = PLC(str(client_ip['ip']), int(client_ip['port']), arduino_modules["status"].reg_num)
    plc.connect()
    return plc_run(plc)


def plc_run(plc):
    while plc.status() and status_state():
        check_changes(plc, arduino_modules["status"])
        sleep = True if arduino_modules["status"].value == 0 else False
        for i in arduino_modules["actuators"]:
            sleep_check(i, sleep)
            check_changes(plc, i)
        for i in arduino_modules["sensors"]:
            sleep_check(i, sleep)
            update_sensors(plc, i)
        time.sleep(3)
    os._exit(1)


def sleep_check(dev, sleep):
    if sleep and not dev.sleep:
        dev.sleep = True
    elif not sleep and dev.sleep:
        dev.sleep = False


def update_sensors(plc, sen):
    num = sen.update(read_reg(sen.pos), read_reg(sen.neg))
    plc.write_reg(sen.reg_num, num)
    write_reg(sen.reg_num, num)
    if num and num < 0:
        sen.value = 0


def check_changes(plc, act):
        print "Start: act: %s plc: %s reg: %s" % \
                  (act.value, plc.read_reg(act.reg_num), read_reg(act.reg_num))
        if act.sleep:
            plc.write_reg(act.reg_num, 0)
            write_reg(act.reg_num, 0)
        elif plc.read_reg(act.reg_num) not in [act.value, read_reg(act.reg_num)]:
            act.value = plc.read_reg(act.reg_num)
            write_reg(act.reg_num, plc.read_reg(act.reg_num))
        elif read_reg(act.reg_num) not in [act.value, plc.read_reg(act.reg_num)]:
            act.value = read_reg(act.reg_num)
            plc.write_reg(act.reg_num, read_reg(act.reg_num))
        else:
            print "No Change: act: %s plc: %s reg: %s" % \
                  (act.value, plc.read_reg(act.reg_num), read_reg(act.reg_num))


def read_reg(index):
    if index:
        print "Read Reg: %s" % index
        return store.getValues(3, index)[0]


def write_reg(index, value):
    store.setValues(3, index, [value])


def status_state():

    return False if hex(int(store.getValues(3, arduino_modules["status"].reg_num)[0])) == "0xffff" else True


# Method: Usage
# Description: displays CLI usage
# Arguments: None
# Returns: Void
def usage():
    """Terminal usage message for program"""
    print("[python2] ./PLC.py [-H] -D <Controller ID> -I <HMI IP> -P <HMI Port>")

# Method: Main
# Description: Main Function takes in CLI arguments and validates the user input and if valid initializes the
# application's functions to create the base for the PLC Device.
# Arguments: See Usage Method for Arguments
# Returns: Void
if __name__ == "__main__":
    controller_id = None
    hmi_ip = '127.0.0.1'
    hmi_port = 5000
    try:
        opts, args = getopt.getopt(sys.argv[1:], "HD:I:P:")
    except getopt.GetoptError as err:
        # print help information and exit:
        print(str(err))  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    try:
        for o, a in opts:
            if o in "-H":
                usage()
                sys.exit()
            elif o in "-D":
                controller_id = a
            elif o in "-I":
                hmi_ip = a
            elif o in "-P":
                hmi_port = int(a)
    except ValueError as e:
        print(e)
        sys.exit()
    while True:
        try:
            if requests.get("http://%s:%s/api" % (hmi_ip, hmi_port)).status_code == 200:
                break
        except Exception as e:
            print(e)
            time.sleep(30)
    arduino_modules['config'] = requests.get("http://%s:%s/api/config/%s" %
	                      (hmi_ip, hmi_port, controller_id)).json()
    server_ip = {"ip" : arduino_modules['config']['host_ip'], "port": arduino_modules['config']['host_port']}
    client_ip = {"ip" : arduino_modules['config']['hmi_ip'], "port": arduino_modules['config']['hmi_port']}
    server = threading.Thread(name="Server", target=controller_server)
    server.setDaemon(True)
    client = threading.Thread(name="Server", target=controller_client)
    server.start()
    client.start()

