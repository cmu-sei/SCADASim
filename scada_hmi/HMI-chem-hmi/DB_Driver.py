#!/usr/local/bin/python3
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

# SEI SCADA System Simulation (4S) V1.0 Database Engine

import psycopg2
from psycopg2.extensions import AsIs
from psycopg2 import extras
import datetime


# Class: Database Driver
# Description: Interface class between the Postgres Database and SCADA Sensor Network can be used at all levels
# of SCADA network between HMI and Historian
class DatabaseDriver:
    # Method: Initializer
    # Description: Initializer for Database Driver to help create the connection between the driver and postgres DB
    # Arguments: dbname: String name of the database
    #            dbusername: String username to access database
    #            dbpw: string of password for database required for windows systems
    # Returns: Initialized Database Driver object
    def __init__(self, dbname=None, dbusername=None, dbpw=None):
        self.dbname = dbname
        self.dbusername = dbusername
        self.dbpw = dbpw
        self.curr = None
        self.conn = None

    # Method: Connect
    # Description: Establishes connection to database with auto commit and returns dictionary quarry objects
    # Arguments: self: Initialized Database Driver Object
    # Returns: Boolean Value: True for established connection and a cursor object, False for an error has occurred
    def connect(self):
        try:
            self.conn = psycopg2.connect("dbname=%s user=%s password=%s" % (self.dbname, self.dbusername, self.dbpw))
            self.conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            self.curr = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            return True
        except psycopg2.OperationalError:
            print("Unable to connect to Databse: %s with Username: %s and Password %s" %
                  (self.dbname, self.dbusername, self.dbpw))
            return False

    # Method: Disconnect
    # Description: Destroies connection to Database and Cursor object
    # Arguments: self: Initialized Database Driver Object
    # Returns: Void
    def disconnect(self):
        self.curr.close()
        self.conn.close()
    # Method: Get Devise List
    # Description: Returns a list of all devises within the device table
    # Arguments: self: Initialized Database Driver Object
    #            did: String object of device ID
    # Returns: Dictionary Object of all or single device created
    def database_populated(self):
        self.curr.execute("Select table_name from information_schema.tables")
        check = str(self.curr.fetchall())
        if 'device' in check and 'plc' in check:
            return True
        return False
        
    # Method: Get Devise List
    # Description: Returns a list of all devises within the device table
    # Arguments: self: Initialized Database Driver Object
    #            did: String object of device ID
    # Returns: Dictionary Object of all or single device created
    def get_device_config(self, did=None):
        if did:
            self.curr.execute("Select * from devices WHERE id='%s'" % did)
            return self.curr.fetchone()
        else:
            d = {"hmi": [], "con": []}
            self.curr.execute("Select * from devices")
            l = self.curr.fetchall()
            for i in l:
                if "hmi" in i["id"]:
                    d["hmi"].append(i)
                elif "con" in i["id"]:
                    d["con"].append(i)
                elif "his" in i["id"]:
                    d["his"] = i
            return d

    # Method: Get Devise List
    # Description: Returns a list of all devises within the device table
    # Arguments: self: Initialized Database Driver Object
    #            did: String object of device ID
    # Returns: Dictionary Object of all or single device created
    def get_device_list(self, did=None):
        if did:
            self.curr.execute("Select * from devices WHERE id='%s'" % did)
        else:
            self.curr.execute("Select * from devices")
        return self.curr.fetchall()

    # Method: Device Actuator
    # Description: Each Device has an actuator that turns on and off the device and all sub-devices this method
    # returns true if the actuator is such a device and false if the not
    # Arguments: self: Initialized Database Driver Object
    #            AID: String Actuator ID to check
    # Returns: Boolean Value: True if actuator is a status actuator, False if not a status actuator
    def dev_actuator(self, aid):
        dev_list = self.get_device_list()
        for i in dev_list:
            if aid in i["slave_devices"]:
                act = self.get_actuator_list(aid)
                if act[0]["name"].lower() == "status":
                    return True
        else:
            return False

    # Method: Get Actuator List
    # Description: If an actuator id is defined then the actuator information is returned
    # If an actuator ID is not supplied then a list of all actuators is returned
    # Arguments: self: Initialized Database Driver Object
    #            AID: String Actuator ID with default of None
    # Returns: Dictionary Object of actuator or actuators
    def get_actuator_list(self, aid=None):
        if aid:
            self.curr.execute("SELECT * FROM plc where plc_type='actuator' AND id='%s';" % aid)
        else:

            self.curr.execute("SELECT * FROM plc where plc_type='actuator';")
        return self.curr.fetchall()

    # Method: Get All Actuators by ID
    # Description: Returns a list of all Actuator ID Strings
    # Arguments: self: Initialized Database Driver Object
    # Returns: Dictionary Object of actuator IDs defined within the PLC Database
    def get_all_actuators_id(self):
        self.curr.execute("SELECT id FROM plc where plc_type='actuator';")
        try:
            return self.curr.fetchall()
        except Exception:
            print("No sensors defined within the system")

    # Method: Get Actuator Value
    # Description: Returns the value of the Actuator defined with the Actuator ID
    # Arguments: self: Initialized Database Driver Object
    #            AID: String Actuator ID to return value
    # Returns: Dictionary Object of the current value of the actuator
    def get_actuator_value(self, aid):
        self.curr.execute("SELECT * from %s ORDER BY event_time DESC LIMIT 1" % aid)
        return self.curr.fetchone()

    # Method: Set Actuator Value
    # Description: Set the value of the Actuator with value supplied within the arguments. The complete variable
    # is set to false until the actuator reflects the new value
    # Arguments: self: Initialized Database Driver Object
    #            AID: String Actuator ID to insert value
    #            new_value: Float Value of the actuator state
    #            UID: String Update ID of the entity that inserted new entry into the Database
    # Returns: Boolean Value: True if entry is injected into the table
    def set_actuator_value(self, aid, new_value, uid):
        self.curr.execute("INSERT INTO %(data_table_str)s (event_time, value, update_id, complete) VALUES (%(time)s, "
                          "%(sensor_value)s, %(update_id_str)s, FALSE)",
                          {'data_table_str': AsIs(aid),
                           'time': datetime.datetime.now(),
                           'sensor_value': new_value,
                           'update_id_str': str(uid)
                           })
        return True

    # Method: Validate Actuator Commands
    # Description: Once the Actuator reflects the current value in the database the database entry is updated to
    # True to validate the change to the actuator
    # Arguments: self: Initialized Database Driver Object
    #            AID: String Actuator ID to update
    # Returns: Void
    def validate_actuator_commands(self, aid):
        print(aid)
        acts = self.get_all_actuators_id()
        if {"id": aid} not in acts:
            raise Exception("Actuator ID is not in PLC Database.")
        self.curr.execute("UPDATE %(act_id)s SET complete=TRUE;", {'act_id': AsIs(aid)})

    # Method: Get Actuator Count
    # Description: Returns the number of actuators within the PLC database
    # Arguments: self: Initialized Database Driver Object
    # Returns: Integer of actuator count
    def get_plc_count(self):
        self.curr.execute("SELECT COUNT(*) FROM plc;")
        try:
            c = self.curr.fetchone()
            return int(c['count'])
        except Exception:
            print("No sensors defined within the system")
    
    # Method: Get Pending Actuator
    # Description: Returns the Dictionary of all actuators with complete as False
    # Arguments: self: Initialized Database Driver Object
    # Returns: Dictionary of actuator objects with complete set to False
    def get_pending_actuator(self):
        a_list = []
        actuator_list = self.get_all_actuators_id()
        for i in actuator_list:
            try:
                self.curr.execute("SELECT * FROM %s ORDER BY event_time DESC LIMIT 1;" % i)
                c = self.curr.fetchone()
                if not c["complete"]:
                     a_list.append(i)
            except Exception:
                print("No sensors defined within the system")
        return a_list

    # Method: Get Sensor List
    # Description: If an sensor id is defined then the sensor information is returned
    # if a sensor ID is not supplied then a list of all sensors is returned
    # Arguments: self: Initialized Database Driver Object
    #            SID: String Sensor ID with default of None
    # Returns: Dictionary Object of sensor or sensors
    def get_sensor_list(self, sid=None):
        if sid:
            self.curr.execute("SELECT * FROM plc WHERE plc_type='sensor' and id='%s'" % sid)
        else:
            self.curr.execute("SELECT * FROM plc WHERE plc_type='sensor'")
        return self.curr.fetchall()

    # Method: Get All Sensors by ID
    # Description: Returns a list of all Sensor ID Strings
    # Arguments: self: Initialized Database Driver Object
    # Returns: Dictionary Object of Sensor IDs defined within the PLC Database
    def get_all_sensors_id(self):
        self.curr.execute("SELECT device_num, id FROM plc where plc_type='sensor';")
        try:
            return self.curr.fetchall()
        except Exception:
            print("No sensors defined within the system")

    # Method: Get Sensor Data
    # Description: Returns the value of the Sensor defined by the Sensor ID
    # Arguments: self: Initialized Database Driver Object
    #            SID: String Sensor ID to return value
    # Returns: Dictionary Object of the last 50 sensor readings
    def get_sensor_data(self, sid, count=True):
        if count == 1:
            return self.get_current_sensor_data(sid)
        else:
            coor = []
            now = datetime.datetime.now()
            x = 0
            self.curr.execute("SELECT value FROM %(data_table_str)s ORDER BY event_time DESC LIMIT 500;",
                          {'data_table_str': AsIs(sid)})
            b = self.curr.fetchall()
            for i in range(0, 500):
                if len(b) > i:
                    coor.append({"value": b[i]["value"] + x, "event_time": now.__str__()})
                else:
                    coor.append({"value": b[len(b) - 1]["value"] + x, "event_time": now.__str__()})
                now += datetime.timedelta(seconds=-3)
        coor.reverse()
        return coor

    # Method: Get Current Sensor Data
    # Description: Returns the value of all Sensors defined
    # Arguments: self: Initialized Database Driver Object
    # Returns: Dictionary Object of all current sensor readings
    def get_current_sensor_data(self, sid):
        self.curr.execute("SELECT value FROM %(data_table_str)s ORDER BY event_time DESC LIMIT 1;",
                          {'data_table_str': AsIs(sid)})
        return self.curr.fetchone()

    # Method: Get Sensor Initial Value
    # Description: Returns the original value of the Sensor defined by the Sensor ID
    # Arguments: self: Initialized Database Driver Object
    #            SID: String Sensor ID to return value
    # Returns: Dictionary Object of the initial sensor value
    def get_sensor_initial_value(self, sid):
        self.curr.execute("SELECT value FROM PLC with 'id' = '%s';" % sid)
        return self.curr.fetchall()

    # Method: Set Sensor Value
    # Description: Set the value of the Sensor with value supplied within the arguments. If there are more then 1000
    # records defined within the sensor's table then the oldest record is removed.(FIFO) This ensures the table
    # maintains no more then 1000 records
    # Arguments: self: Initialized Database Driver Object
    #            SID: String Sensor ID to insert value
    #            new_value: Integer Value of the sensor state
    #            UID: String Update ID of the entity that inserted new entry into the Database
    # Returns: Boolean Value: True if entry is injected into the table
    def set_sensor_value(self, sid, new_value, uid):
        self.curr.execute("INSERT INTO %(data_table_str)s (event_time, value, update_id) VALUES (%(time)s, "
                          "%(sensor_value)s, %(update_id_str)s)",
                          {'data_table_str': AsIs(sid),
                           'time': datetime.datetime.now(),
                           'sensor_value': new_value,
                           'update_id_str': str(uid)
                           })
        self.curr.execute("SELECT COUNT(*) FROM %s" % AsIs(sid))
        count = self.curr.fetchone()
        count = count['count'] - 1000
        if count > 0:
            self.curr.execute("DELETE FROM %(data_table_str)s WHERE event_time = ANY (SELECT event_time from "
                              "%(data_table_str)s ORDER BY event_time ASC LIMIT %(count_str)s)",
                              {'data_table_str': AsIs(sid),
                               'count_str': count
                               })
        return True

    # Method: Remove Sensor
    # Description: Removes a sensor from the PLC table and drops sensor's table
    # Arguments: self: Initialized Database Driver Object
    #            SID: String Sensor ID to remove from scada network
    # Returns: Boolean Value: True if sensor is removed from PLC and Table Dropped
    def remove_sensor(self, sid):
        try:
            self.curr.execute("DELETE FROM plc WHERE id = %s;" % sid)
            self.curr.execute("DROP TABLE %s" % sid)
            return True
        except Exception:
            print("No sensors defined within the system")
            return False

    # Method: Add Sensor
    # Description: Creates sensor entry in PLC table and Creates sensor's table
    # Arguments: self: Initialized Database Driver Object
    #            SID: Dictionary Object of Sensor with all variables defined
    # Returns: Boolean Value: True if sensor is added to PLC table and Table created
    def add_sensor(self, sid):
        try:
            self.curr.execute("CREATE TABLE %(data_table_str)s timestamp "
                              "PRIMARY KEY, value INTEGER, update_id VARCHAR);" % sid['id'])
            self.curr.execute("INSERT INTO plc (id, name, type, ipaddr, initial_value, plc_type, variance) VALUES "
                              "(%(device_id)s, %(name_str)s,  %(type_str)s, %(ip_str)s, %(initial_value_str)s, "
                              "%(plc_str)s, %(variance_str)s);", {
                                 'device_id': sid['id'],
                                 'name_str': sid['name'],
                                 'type_str': sid['type'],
                                 'ip_str': sid['ip'],
                                 'initial_value_str': sid['initial_value'],
                                 'plc_str': "sensor",
                                 'variance_str': sid['variance']})
            self.curr.execute("INSERT INTO %(data_table_str)s (event_time, value, update_id) VALUES (%(time)s, "
                              "%(value_int)s,%(update_id_str)s);", {
                                'data_table_str': AsIs(sid['id']),
                                'time': datetime.datetime.now(),
                                'value_int': int(sid['initial_value']),
                                'update_id_str': "INITIAL"})
            return True
        except Exception:
            print("No sensors defined within the system")
            return False

    # Method: Get All PLC List
    # Description: Returns contents of PLC Table
    # Arguments: self: Initialized Database Driver Object
    # Returns: Dictionary Object of all PLC Devices in PLC Table
    def get_all_plc_list(self):
        self.curr.execute("SELECT * FROM plc;")
        try:
            return self.curr.fetchall()
        except Exception:
            print("No sensors defined within the system")

    # Method: Get All PLC ID
    # Description: Returns list of all PLC ID's in PLC Table
    # Arguments: self: Initialized Database Driver Object
    # Returns: Dictionary Object of all PLC ID's
    def get_all_plc_id(self):
        self.curr.execute("SELECT id, device_num, type FROM plc;")
        try:
            return self.curr.fetchall()
        except Exception:
            print("No sensors defined within the system")

    # Method: Populate Current Data
    # Description: Returns list of all current sensor values
    # Arguments: self: Initialized Database Driver Object
    #            sensor_list: List of all sensor ID's desired to get current value
    # Returns: Dictionary Object of Sensor List ID's current values
    def populate_current_data(self, sensor_list):
        current_value = {}
        for sensor in sensor_list:
            self.curr.execute("SELECT * FROM %(data_table_str)s ORDER BY read_time DESC LIMIT 1;",
                              {'data_table_str': AsIs(sensor['id'])})
            data_point = self.curr.fetchone()
            current_value[sensor['id']] = data_point['value']
        return current_value

    # Method: Build Config File
    # Description: Builds a configuration file from current Database State
    # Arguments: self: Initialized Database Driver Object
    #            Sub_System: String value of Subsystem desired to create config file for default is None
    # Returns: Dictionary Object of Configuration requested
    def build_config_file(self, sub_system=None):
        root_id = self.get_root_id() if not sub_system else sub_system
        self.curr.execute("SELECT * FROM devices;")
        device_list = self.curr.fetchall()
        self.curr.execute("SELECT * FROM plc;")
        plc_list = self.curr.fetchall()
        for i in device_list:
            if root_id == i['id']:
                return self.get_device_map(i, device_list, plc_list)
        raise Exception("Unable to locate sub_system or root node")

    # Method: Get Device Map
    # Description: Recursive method to define map of each device. This method is most effective
    # when called from build config file method and should not be used on its own
    # Arguments: self: Initialized Database Driver Object
    #            root_node: Dictionary Object of root node and all child nodes
    #            device_list: List of all devices defined within the Device Table
    #            plc_list: List of PLC devices defined within the PLC Table
    # Returns: Dictionary of Device Map at this level
    def get_device_map(self, root_node, device_list, plc_list):
        if 'slave_devices' in root_node:
            for i in root_node["slave_devices"]:
                if "act" in i and i in str(plc_list):
                    index = [index for index, _ in enumerate(plc_list) if i == _['id']][0]
                    if "actuators" not in root_node:
                        root_node["actuators"] = {}
                    b = plc_list.pop(index)
                    root_node["actuators"][b["name"]] = b
                elif "sen" in i and i in str(plc_list):
                    index = [index for index, _ in enumerate(plc_list) if i == _['id']][0]
                    if "sensors" not in str(root_node):
                        root_node["sensors"] = {}
                    b = plc_list.pop(index)
                    root_node["sensors"][b["name"]] = b
                elif ("con" in i or "hmi" in i) and i in str(device_list):
                    index = [index for index, _ in enumerate(device_list) if i == _['id']][0]
                    if "sub_devices" not in root_node:
                        root_node["sub_devices"] = {}
                    b = device_list.pop(index)
                    root_node["sub_devices"][b["name"]] = self.get_device_map(b, device_list, plc_list)
                else:
                    raise Exception("Unknown device type %s" % i)
        return root_node

    # Method: Get Device Tree
    # Description: Recursive method to defines configuration used for javascript map frontend
    #            root_node: Dictionary Object of root node and all child nodes
    #            device_list: List of all devices defined within the Device Table
    #            plc_list: List of PLC devices defined within the PLC Table
    # Returns: Dictionary of Device Map at this level
    def get_device_tree(self, root_node, device_list, plc_list):
        if not root_node:
            index = [index for index, _ in enumerate(device_list) if "his" in _['id']][0]
            root = device_list.pop(index)
        else:
            index = [index for index, _ in enumerate(device_list) if root_node == _['id']][0]
            root = device_list.pop(index)
        config = {"id": root["id"], "name": root["name"], "data": {"Actuators": [], "Sensors": []}, "children": []}
        if 'slave_devices' in root:
            for i in root["slave_devices"]:
                if "act" in i and i in str(plc_list):
                    index = [index for index, _ in enumerate(plc_list) if i == _['id']][0]
                    b = plc_list.pop(index)
                    config["data"]["Actuators"].append({"name": b["name"],
                                                        "id": b['id'],
                                                        "value": self.get_actuator_value(b['id'])['value'],
                                                        "type": b['type']})
                elif "sen" in i and i in str(plc_list):
                    index = [index for index, _ in enumerate(plc_list) if i == _['id']][0]
                    b = plc_list.pop(index)
                    config["data"]["Sensors"].append({"name": b["name"], "id": b["id"]})
                elif ("con" in i or "hmi" in i) and i in str(device_list):
                    config["children"].append(self.get_device_tree(i, device_list, plc_list))
                else:
                    raise Exception("Unknown device type %s" % i)
        return config

    # Method: Get Tree JSON
    # Description: Builds configuration file to be used with javascript maping frontend
    # Arguments: self: Initialized Database Driver Object
    #            device_list: List of all devices defined within the parent node or all devices defined default is none
    # Returns: json object map configuration of all device or sub devices of the device ID
    def get_tree_json(self, device_id=None):
        return self.get_device_tree(device_id, self.get_device_list(), self.get_sensor_list()+self.get_actuator_list())

    # Method: Get Root Node
    # Description: Returns the root node within the database. A root node is defined as a node within the device table
    # that does not have an ID with any other device's slave list
    # Arguments: None
    # Returns: string id of the root node
    def get_root_id(self):
        device_list = self.get_device_list()
        slave_list = []
        if 'his' in str(device_list):
            return [i['id'] for i in self.get_device_list() if 'his' in i['id']][0]
        else:
            for i in device_list:
                if "HISTORIAN" != i["id"]:
                    slave_list += i["slave_devices"]
        for i in device_list:
            if i["id"] not in str(slave_list) and i["id"] != "HISTORIAN":
                return i["id"]

    # Method: Get Dependant PLC Devices
    # Description: This function is used with status actuators and returns a list of id's of all devices that depend on
    # this actuator. If this actuator is in the off position then all sub devices will be turned off and vice versa.
    # Arguments: self: Initialized Database Driver Object
    #            aid: string representation of the actuator ID to look up
    # Returns: list of strings of id's dependent on the root actuator
    def get_dependant_plc_devices(self, aid):
        device_list = self.get_device_list()
        plc_list = self.get_all_plc_id()
        for i in range(0, len(device_list)):
            if aid in device_list[i]["slave_devices"]:
                d = device_list.pop(i)
                d_list = self.dependant_device_walk(device_list, d["slave_devices"])
                return [z for z in plc_list if z['id'] in d_list]

    # Method: Dependant Device Walk
    # Description: Recursive method to identify all plc devices dependent root node
    # Arguments: self: Initialized Database Driver Object
    #            device_list: List of all devices defined within the Device Table
    #            sub_devices: List of known dependent sub devices
    # Returns: list of strings of id's dependent on the root actuator
    def dependant_device_walk(self, device_list, sub_device):
        dependant_list = []
        while sub_device:
            d = sub_device.pop()
            if "dev" not in d:
                dependant_list.append(d)
            else:
                for i in range(0,len(device_list)):
                    if device_list[i]['id'] == d:
                        d = device_list.pop(i)
                        dependant_list += self.dependant_device_walk(device_list, d["slave_devices"])
                        break
        return dependant_list








