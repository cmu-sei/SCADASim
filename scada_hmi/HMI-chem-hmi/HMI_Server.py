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

# SEI SCADA System Simulation (4S) V1.0 HMI Server used on HMI machines

from pymodbus.server.sync import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from DB_Driver import DatabaseDriver
import time
import sys
import threading
import getopt
import requests
import json
import os
uid=None
# Data Store for PLC Devices hr is used for Reg Read and Reg Write and is the only register interaction
store = ModbusSlaveContext(
    di = ModbusSequentialDataBlock(0, [17]*100),
    co = ModbusSequentialDataBlock(0, [17]*100),
    hr = ModbusSequentialDataBlock(0, [17]*100),
    ir = ModbusSequentialDataBlock(0, [17]*100))
context = ModbusServerContext(slaves=store, single=True)


# Data Store for PLC Devices hr is used for Reg Read and Reg Write and is the only register interaction
identity = ModbusDeviceIdentification()
identity.VendorName  = 'Facility Sensor System'
identity.ProductCode = 'FSS'
identity.VendorUrl   = 'http://www.wehaveyourback.com'
identity.ProductName = 'PLC Sensor Server'
identity.ModelName   = 'Sensor Server 5000'
identity.MajorMinorRevision = '3.a1'


# Class: PLC Server Thread
# Description: HMI Machines maintain connection between the PLC device and the Historian. The PLC Thread maintains three
# threads one for the Server itself the interacts directly with the PLC devices. The second is the polling of sensor
# systems and update the database. Lastly the actuator which polls and communicates with the the PLC actuators and
# reflects the changes to the database and sensors.
class PLCThread(threading.Thread):
    # Method: Initializer
    # Description: Initializer for PLC Thread Object to help create the connection between the PLC devices and
    # postgres DB
    # Arguments: address: Address of the System to be used to host the server
    # Returns: Initialized PLC Thread object
    def __init__(self, system_type, db_obj=None, address=None):
        threading.Thread.__init__(self)
        self.system_type = system_type
        self.db_obj = db_obj
        self.address = address

    # Method: Run
    # Description: Starts the PLC Thread object on its own thread to complete tasks defined in the arguments.
    # Arguments: self: initialized PLC Thread Object
    #            System Type: integer of the type of system the thread will be functions as:
    #                         0 server, 1 sensor, 2 actuator
    #            DB Object: The DB Driver object to communicate with the postgres Database
    # Returns: void
    def run(self):
        if self.system_type == 0:
            print "Server"
            self.plc_server()
        elif self.system_type == 1:
            print "Sensor"
            self.sensor_handler()
        elif self.system_type == 2:
            print "Actuator"
            self.actuator_handler()
        elif self.system_type == 3:
            print "Historian"
            self.db_obj.connect()
            self.historian_connection_check()
        else:
            raise Exception("System Type is invalid:\n 0 for server\n 1 for Sensor\n 2 for Actuators")

    # Method: PLC Server
    # Description: Start PLC Server and uses global variables identity and context and runs forever.
    # Arguments: self: initialized PLC Thread Object
    # Returns: Initialized PLC Thread object
    def plc_server(self): StartTcpServer(context, identity=identity, address=self.address)

    # Method: Actuator Handler
    # Description: Polls Data store for Actuator PLC Devices and updates changes within the Database and propagates
    # changes to PLC devices.
    # Arguments: self: initialized PLC Thread Object
    #            DB Object: The DB Driver object to communicate with the postgres Database
    # Returns: void
    def actuator_handler(self):
        time.sleep(10)
        if not self.db_obj or not self.db_obj.connect():
            print("Unable to connect to local database. Check database log-in credentials and connectivity.")
            sys.exit()
        act_list = self.db_obj.get_actuator_list()
        counter = [0]*self.db_obj.get_plc_count()
        while True:
            for i in act_list:
                reg_value = store.getValues(3, i["device_num"])[0]
                current_value = self.db_obj.get_actuator_value(i["id"])
                if reg_value != current_value["value"]:
                    store.setValues(3, i["device_num"], [current_value["value"]])
                    counter[i["device_num"] % self.db_obj.get_plc_count()] += 1
                    c = counter[i["device_num"] % self.db_obj.get_plc_count()]
                    for z in range(0, 10):
                        if i["name"].lower() == "status" and current_value["value"] == int("0xffff", 0):
                            self.kill_walk(self.db_obj.get_dependant_plc_devices(i['id']), c)
                        elif i["name"].lower() == "status" and current_value["value"] == 0:
                            self.off_walk(self.db_obj.get_dependant_plc_devices(i['id']), c)
                        elif i["name"].lower() == "status" and current_value["value"] == 1:
                            self.on_walk(self.db_obj.get_dependant_plc_devices(i['id']), c)
                        elif i["type"] == 'variable':
                            self.variable_walk(current_value["value"], self.db_obj.get_sensor_list(i['relationship_id'])[0], c)
                        elif i["type"] == 'relational':
                            print("Reg: %s Current: %s ID: %s Name: %s" % (reg_value, current_value["value"], i["id"], i["name"]))
                            self.relational_walk(current_value["value"], self.db_obj.get_sensor_list(i['relationship_id'])[0],
                                                 i['relationship_type'].lower(), c)

                elif reg_value == current_value["value"] and not current_value['complete']:
                    self.db_obj.validate_actuator_commands(i["id"])

    # Method: Off Walk
    # Description: Walks the Slave device list and and propagates off command. This will cause all
    # dependent devices to sleep but not disconnect once the on command is propagated then the device
    # will continue as normal.
    # Arguments: self: initialized PLC Thread Object
    #            Device List: List of all devices
    #            Count: The counter used to identify the current command ID
    # Returns: void
    def off_walk(self, device_list, count):
        for i in device_list:
            if "sen" in i['id']:
                store.setValues(3, i["device_num"], [int("0xf700", 0) + (count % 256)])
            if "act" in i['id']:
                self.db_obj.set_actuator_value(i['id'], 0, count)
                store.setValues(3, i["device_num"], [0])

    # Method: On Walk
    # Description: Walks the Slave device list and and propagates on command.
    # Arguments: self: initialized PLC Thread Object
    #            Device List: List of all devices
    #            Count: The counter used to identify the current command ID
    # Returns: void
    def on_walk(self, device_list, count):
        for i in device_list:
            if "sen" in i['id']:
                store.setValues(3, i["device_num"], [int("0xf600", 0) + (count % 256)])
            if "act" in i['id']:
                if i['type'] == 'relational':
                    self.db_obj.set_actuator_value(i['id'], 0, count)
                    store.setValues(3, i["device_num"], [0])
                elif i['type'] == 'variable':
                    self.db_obj.set_actuator_value(i['id'], 2, count)
                    store.setValues(3, i["device_num"], [2])
                else:
                    self.db_obj.set_actuator_value(i['id'], 1, count)
                    store.setValues(3, i["device_num"], [1])

    # Method: Relational Walk
    # Description: Communicates to relational sensor devices the state of the actuator so that the sensor
    # will react according to the actuator state
    # Arguments: Device: Dictionary object of sensor device to be manipulated
    #            Current: Integer Current Actuator state
    #            Type: String of relationship type (Positive or Negative)
    #            Count: The counter used to identify the current command ID
    # Returns: void
    @staticmethod
    def relational_walk(current, device, type, count):
        if type == "negative":
            if current == 0:
                store.setValues(3, device['device_num'], [int("0xf600", 0) + (count % 256)])
            elif current == 1:
                store.setValues(3, device['device_num'], [int("0xfb00", 0) + (count % 256)])
            elif current == 2:
                store.setValues(3, device['device_num'], [int("0xfc00", 0) + (count % 256)])
            elif current == 3:
                store.setValues(3, device['device_num'], [int("0xfd00", 0) + (count % 256)])
        elif type == "positive":
            if current == 0:
                store.setValues(3, device['device_num'], [int("0xf600", 0) + (count % 256)])
            elif current == 1:
                store.setValues(3, device['device_num'], [int("0xf800", 0) + (count % 256)])
            elif current == 2:
                store.setValues(3, device['device_num'], [int("0xf900", 0) + (count % 256)])
            elif current == 3:
                store.setValues(3, device['device_num'], [int("0xfa00", 0) + (count % 256)])

    # Method: Relational Walk
    # Description: Communicates to variable sensor devices the state of the actuator so that the sensor
    # will react according to the actuator state
    # Arguments: Device: Dictionary object of sensor device to be manipulated
    #            Register Value: Integer Current Actuator state
    #            Count: The counter used to identify the current command ID
    # Returns: void
    @staticmethod
    def variable_walk(reg_value, device, count):
        if reg_value == 0:
            store.setValues(3, device["device_num"], [int("0xf700", 0) + (count % 256)])
        elif reg_value == 1:
            store.setValues(3, device["device_num"], [int("0xf400", 0) + (count % 256)])
        elif reg_value == 2:
            store.setValues(3, device["device_num"], [int("0xf600", 0) + (count % 256)])
        elif reg_value == 3:
            store.setValues(3, device["device_num"], [int("0xf500", 0) + (count % 256)])

    # Method: Kill Walk
    # Description: Communicates to dependent devices the kill command to disconnect and shut down the device
    # Arguments: self: initialized PLC Thread Object
    #            Device List: Dictionary List of al dependent devices to propagate the kill command
    #            Count: The counter used to identify the current command ID
    # Returns: void
    def kill_walk(self, device_list, count):
        for i in device_list:
            if "sen" in i['id']:
                store.setValues(3, i["device_num"], [int("0xffff", 0)])
            if "act" in i['id']:
                self.db_obj.set_actuator_value(i['id'], int("0xffff", 0), count)
                store.setValues(3, i["device_num"], [int("0xffff", 0)])

    # Method: Sensor Handler
    # Description: Handles sensor register values and updates the local database
    # Arguments: self: initialized PLC Thread Object
    # Returns: void
    def sensor_handler(self):
        time.sleep(10)
        if not self.db_obj or not self.db_obj.connect():
            print("Unable to connect to local database. Check database log-in credentials and connectivity.")
            sys.exit()
        sensor_list = self.db_obj.get_all_sensors_id()
        while True:
            time.sleep(3)
            for i in sensor_list:
                value = store.getValues(3, i["device_num"])[0]
                if len(hex(int(value))) == 6 and hex(int(value))[:3] == "0xf":
                    if hex(int(value)) == "0xffff":
                        self.db_obj.set_sensor_value(i["id"], 0, '7777')
                    continue
                else:
                    self.db_obj.set_sensor_value(i["id"], value, '7777')

    # Method: Historian Connection Check
    # Description: Continually attempts to establish communication with the historian. Once a successful transaction
    # occurs this thread will continue with the historian handler
    # Arguments: self: initialized PLC Thread Object
    # Returns: void
    def historian_connection_check(self):
        if not self.db_obj or not self.db_obj.connect():
            print("Unable to connect to local database. Check database log-in credentials and connectivity.")
            sys.exit()
        self.hmi_initial_setup()
        historian_ip = None
        root = self.db_obj.get_device_list()
        for i in root:
            if "HISTORIAN" in i["id"]:
                historian_ip = "%s:%s" % (i["host_ip"], i["host_port"])
                print historian_ip
                break
        while True:
            try:
                if requests.get("http://%s/api" % historian_ip).status_code == 200:
                    print "HERE"
                    self.historian_handler(historian_ip)
                    return
            except requests.ConnectionError as e:
                time.sleep(30)
                print e

    # Method: Historian Handler
    # Description: Update Historian with current PLC device state, this polling happens every 30 seconds
    # Arguments: self: initialized PLC Thread Object
    #            ip: string ip address of the historian in http format
    # Returns: void
    def historian_handler(self, ip):
        node_list = self.db_obj.get_all_plc_list()
        while True:
            time.sleep(30)
            print "WTF"
            for i in node_list:
                print "IP %s A: %s" % (ip, i)
                if i["plc_type"] == "actuator":
                    print "IP %s A: %s" % (ip, i)
                    print "IP %s A: %s" % (ip, i)
                    self.send_act(ip, i)
                elif i["plc_type"] == "sensor":
                    self.send_sens(ip, i)

    # Method: HMI Initial Setup
    # Description: Initializes modbus slave store with current PLC device values
    # Arguments: self: initialized PLC Thread Object
    # Returns: void
    def hmi_initial_setup(self):
        plc_list = self.db_obj.get_all_plc_list()
        for i in plc_list:
            store.setValues(3, i['device_num'], [i['initial_value']])

    # Method: Send Actuator
    # Description: Sends Historian HTTP POST of the current value of the PLC actuator device defined by act
    # Arguments: ip: http ip string of the historian
    #            device_id: integer of the PLC device Device Number
    #            Actuator: Dictionary object that defines the current state of the actuator
    # Returns: void
    @staticmethod
    def send_act(ip, act):
        payload = {'uid' : uid, 'newValue': store.getValues(3, act["device_num"])[0]}
        try:
            requests.post("http://%s/api/actuators/%s" % (ip, act["id"]), data=payload)
        except requests.ConnectionError:
            return

    # Method: Send Sensor
    # Description: Sends Historian HTTP POST of the current value of the PLC sensor device defined by sens
    # Arguments: ip: http ip string of the historian
    #            device_id: integer of the PLC device Device Number
    #            Sensor: Dictionary object that defines the current state of the sensor
    # Returns: void
    @staticmethod
    def send_sens(ip, sens):
        payload = {'uid': uid, 'newValue': store.getValues(3, sens["device_num"])[0]}
        requests.post("http://%s/api/sensors/%s" % (ip, sens["id"]), data=payload)

# Method: Usage
# Description: displays CLI usage
# Arguments: None
# Returns: Void
def usage(full=False):
    """Terminal usage message for program"""
    print("[python3] ./plc_hmi.py [-hv] [-p <port-num>] [-i <ip-address>] [-d <database-name>] [-u <db-username>] ")
    if full:
        print("""        -h --help      : Print Help Message
        -v --version   : Print version Message
        -i --ip        : HMI host IP Address
        -p --port      : HMI listening port
        -d --database  : Database Name
        -u --username  : Database Username
        -w --password  : Database User's password to access the database (Required on windows systems)
        """)

# Method: Usage
# Description: displays CLI usage
# Arguments: None
# Returns: Void
if __name__ == "__main__":
    # Default Values
    ipaddr = '127.0.0.1'
    port = 5000
    dbname = None
    dbusername = None
    dbpw = None

    # Process options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvi:p:d:u:w:",
                                   ["help", "version", "ip=", "port=", "database=", "username=", "password="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(str(err))  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-v", "--version"):
            print("CERT Scada Simulator, Web Server v1.0")
            sys.exit()
        elif o in ("-h", "--help"):
            usage(full=True)
            sys.exit()
        elif o in ("-p", "--port"):
            port = int(a)
        elif o in ("-i", "--ipaddr"):
            ipaddr = a
        elif o in ("-d", "--database"):
            dbname = a
        elif o in ("-u", "--username"):
            dbusername = a
        elif o in ("-w", "--password"):
            dbpw = a
        else:
            assert False, "unhandled option"
    if not dbusername or not dbname:
        usage(full=True)
        sys.exit()
    test = DatabaseDriver(dbname, dbusername, dbpw)
    test.connect()
    while not test.database_populated():
        print "Database has yet to be initiated"
        time.sleep(10)
    uid = test.get_root_id()
    print type(uid)
    test.disconnect()
    

    server = PLCThread(0, address=(ipaddr, port))
    sensor = PLCThread(1, DatabaseDriver(dbname, dbusername, dbpw))
    actuators = PLCThread(2, DatabaseDriver(dbname, dbusername, dbpw))
    historian = PLCThread(3, DatabaseDriver(dbname, dbusername, dbpw))
    try:      
        server.start()
        historian.start()
        sensor.start()
        actuators.start()
    except KeyboardInterrupt:
        print "HERE"
        os._exit(1) 
