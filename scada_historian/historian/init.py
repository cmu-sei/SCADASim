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

# SEI SCADA System Simulation (4S) V1.0 Initializes 4S derived from config file
from __future__ import print_function
import psycopg2
from psycopg2.extensions import AsIs
import random
import datetime
import json
import sys, getopt
import numbers
from IPy import IP
import time
# Global Variables
# Description: Global Variables to be utilized throughout application
# Arguments: Validate Device Types List of valid device types
#            Validate Sensor Types List of valid sensor types
#            Validate Actuator Types List of valid actuator types
#            Ip Address Dictionary Object of List of IP address for PLC devices
#            PLC List Dictionary Object of PLC configuration for PLC Storm Box
#            Network List Dictionary Object network list to be utilized with PLC List
valid_device_types = ["controller", "human-machine interface", "historian", "hmi"]
valid_sensor_types = ["locked", "enabled", "open", "temperature", "pressure", "humidity", "flow",
                      "position", "gps", "live-stream", "speed", "rotation", "power", "count", "motion"]
valid_actuator_types = ["locked", "enabled", "live-stream", "variable", "relational"]
ip_addr = {}
PLC_list = {}
network_list = {}
plc_count = 0
device_count = 0
port = 5020


# Method: Clear Existing Databases
# Description: Drops database and creates a new fresh instance of the database
# Arguments: cur Psycopg2 Cursor object to execute postgres system calls
#            d String name of Database to Re Create
#            u String username to grant permission to for Database
# Returns: Void
def clear_existing_db(cur, d, u):
    print("Deleting All Tables from Database %s" % d)
    cur.execute("DROP SCHEMA public CASCADE")
    cur.execute("CREATE SCHEMA public;")
    cur.execute("GRANT ALL ON SCHEMA public TO public;")
    cur.execute("GRANT ALL ON SCHEMA public TO %s;" % u)
    cur.execute("COMMENT ON SCHEMA public IS 'standard public schema';")
    print(" Done")


# Method: Generate Hash Value
# Description: create unique hash value for ID of the given device
# Arguments: prefix string representing the type of device requesting hash value
# Returns: String of Hash value
def generate_hash(prefix):
    """Generates a hopefully unique id for this item"""
    if prefix not in ['hmi_', 'sen_', 'act_', 'his_', 'con_']:
        print("Invalid prefix '%s'" % prefix)
        sys.exit(0)
    return prefix + hex(random.getrandbits(80))[2:18]


# Method: Create Main Table
# Description: Creates Device Table within the postgres database
# Arguments: cur Psycopg2 Cursor object to execute postgres system calls
# Returns: Void
def create_main_table(cur):
    """Create Master Table of devices"""
    cur.execute("""CREATE TABLE devices (
        device_num serial PRIMARY KEY,
        id VARCHAR UNIQUE,
        name VARCHAR,
        location VARCHAR,
        device_type VARCHAR,
        host_ip VARCHAR,
        hmi_ip VARCHAR,
        host_port integer,
        hmi_port integer,
        interface VARCHAR,
        network VARCHAR,
        gateway VARCHAR,
        slave_devices VARCHAR[]
        );""")


# Method: Create Main PLC Table
# Description: Creates PLC Table within the postgres database
# Arguments: cur Psycopg2 Cursor object to execute postgres system calls
# Returns: Void
def create_main_plc_table(cur):
    cur.execute("""CREATE TABLE PLC (
        device_num serial PRIMARY KEY,
        id VARCHAR UNIQUE,
        name VARCHAR,
        plc_type VARCHAR,
        type VARCHAR,
        units VARCHAR,
        initial_value DOUBLE PRECISION,
        variability DOUBLE PRECISION,
        relationship_id VARCHAR,
        relationship_type VARCHAR,
        threshold INTEGER[]);""",)


# Method: Add Device
# Description: Adds device to Device Table within the postgres database if an ID is not assigned it assign an ID
# Arguments: cur Psycopg2 Cursor object to execute postgres system calls
#            config Dictionary object of Device
# Returns: Dictionary Object of the updated configuration
def add_controller(cur, config):
    if 'device_num' not in config:
        global device_count
        device_count += 1
        config['device_num'] = device_count
    if config["device_type"].lower() == "historian":
        return add_historian(cur, config)
    cur.execute(
         """INSERT INTO devices (device_num, id, name, location, device_type, host_ip, host_port, hmi_ip, hmi_port,
            slave_devices, interface, gateway, network) VALUES (%(device_num_str)s,%(device_id)s, %(name_str)s,
            %(location_str)s, %(device_type_str)s, %(host_ip_str)s, %(host_port_int)s, %(hmi_ip_str)s, %(hmi_port_int)s,
            %(slave_devices_str)s,%(interface_str)s,%(gateway_str)s,%(network_str)s);""",
         {
         'device_num_str': config["device_num"],
         'device_id': config["id"],
         'name_str': config['name'].upper(),
         'location_str': config['location'],
         'device_type_str': config['device_type'],
         'host_ip_str': config['host_ip'] if "host_ip" in config else None,
         'host_port_int': config['host_port'] if "host_port" in config else None,
         'hmi_ip_str': config['hmi_ip'] if "hmi_ip" in config else None,
         'hmi_port_int': config['hmi_port'] if "hmi_ip" in config else None,
         'slave_devices_str': config['slave'] if "slave" in config else [],
         'interface_str': config['interface'] if "interface" in config else None,
         'network_str': config['network'] if "network" in config else None,
         'gateway_str': config['gateway'] if "gateway" in config else None
         })
    return config

# Method: Add Device
# Description: Adds device to Device Table within the postgres database if an ID is not assigned it assign an ID
# Arguments: cur Psycopg2 Cursor object to execute postgres system calls
#            config Dictionary object of Device
# Returns: Dictionary Object of the updated configuration
def add_historian(cur, config):
    cur.execute(
         """INSERT INTO devices (device_num, id, name, location, device_type, host_ip, host_port, slave_devices)
             VALUES (%(device_num_str)s, %(device_id)s, %(name_str)s, %(location_str)s, %(device_type_str)s,
            %(host_ip_str)s, %(host_port_int)s, %(slave_devices_str)s);""",
         {
         'device_num_str': config["device_num"],
         'device_id': config["id"],
         'name_str': config['name'].upper(),
         'location_str': config['location'],
         'device_type_str': config['device_type'],
         'host_ip_str': config['host_ip'],
         'host_port_int': config["port"],
         'slave_devices_str': config['slave'] if "slave" in config else []
         })
    return config


# Method: Add Actuator
# Description: Adds actuator device to PLC Table within the postgres database if an ID is not assigned it assign an ID
# next a table is created for the actuator device to log transactions
# Arguments: cur Psycopg2 Cursor object to execute postgres system calls
#            name String object of the name of the PLC Device
#            config Dictionary object of PLC device
# Returns: Dictionary Object of the updated configuration
def add_actuator(cur, name, config, device_name):
    if 'device_num' not in config:
        global plc_count
        plc_count += 1
        config['device_num'] = plc_count
    # Create data table for actuator
    cur.execute("""CREATE TABLE %(data_table_str)s (
        event_time timestamp PRIMARY KEY,
        value INTEGER,
        update_id VARCHAR,
        complete BOOLEAN);""",
        {
        'data_table_str': AsIs(config['id'])
        })
    # Add actuator to senact table
    cur.execute(
         """INSERT INTO plc (device_num, id, name, type, relationship_id, relationship_type, initial_value, plc_type)
            VALUES (%(device_num_str)s,%(device_id)s, %(name_str)s,  %(type_str)s,
             %(relationship_id_str)s, %(relationship_type_str)s, %(initial_value_str)s, %(plc_str)s);""",
         {
         'device_num_str': config['device_num'],
         'device_id': config['id'],
         'name_str': ("%s: %s" % (device_name, name)).upper(),
         'type_str': config['type'],
         'relationship_id_str' : config['RID'] if 'RID' in config else None,
         'relationship_type_str' :  config['relationship'] if 'relationship' in config else None,
         'initial_value_str' : config['initial_value'],
         'plc_str' : "actuator"
         })
    # If initial_value is specified, add it to the actuator
    if isinstance(config['initial_value'],(int,float)):
        cur.execute(
            """INSERT INTO %(data_table_str)s (event_time, value, update_id, complete)
                VALUES (%(time)s, %(value_int)s,%(update_id_str)s, TRUE);""",
            {
            'data_table_str': AsIs(config['id']),
            'time': datetime.datetime.now(),
            'value_int': int(config['initial_value']),
            'update_id_str' : "INITIAL"
            })

    # If succeeded
    return config


# Method: Add Sensor
# Description: Adds sensor device to PLC Table within the postgres database if an ID is not assigned it assign an ID
# next a table is created for the sensor device to log transactions
# Arguments: cur Psycopg2 Cursor object to execute postgres system calls
#            name String object of the name of the PLC Device
#            config Dictionary object of PLC device
# Returns: Dictionary Object of the updated configuration
def add_sensor(cur, name, config, device_name):
    if 'device_num' not in config:
        global plc_count
        plc_count += 1
        config['device_num'] = plc_count

    cur.execute("""CREATE TABLE %(data_table_str)s (
        event_time timestamp PRIMARY KEY,
        value double precision,
        update_id VARCHAR);""",
        {'data_table_str': AsIs(config['id'])})
    # Add actuator to senact table
    cur.execute(
         """INSERT INTO plc (device_num, id, name, type, units, variability, plc_type, initial_value, threshold) VALUES
            (%(device_num_str)s,%(device_id)s, %(name_str)s, %(type_str)s, %(units_str)s, %(variability_str)s,
            %(plc_str)s, %(initial_value_str)s, %(threshold_str)s);""",
         {
         'device_num_str': config['device_num'],
         'device_id': config['id'],
         'name_str': ("%s: %s" % (device_name, name)).upper(),
         'type_str': config['type'],
         'units_str': config['units'],
         'variability_str': config['variability'],
         'plc_str' : "sensor",
         'initial_value_str': int(config['initial_value']),
         'threshold_str': config['threshold'] if 'threshold' in config else []
         })
    # If initial_value is specified, add it to the actuator
    if isinstance(config['initial_value'], numbers.Real):
        cur.execute(
            """INSERT INTO %(data_table_str)s (event_time, value, update_id)
                VALUES (%(time)s, %(value_int)s,%(update_id_str)s);""",
            {
            'data_table_str': AsIs(config['id']),
            'time': datetime.datetime.now(),
            'value_int': int(config['initial_value']),
            'update_id_str' : "INITIAL"
            })
    return config


# Method: Sensor Check
# Description: Checks Sensor Dictionary Fields to ensure proper configuration if the sensor is valid and if a sub system
# then an IP address is assigned or else the ip address will be defined as localhost 127.0.0.1
# Arguments: Sensor Dictionary Object of the Sensor's configuration
#            Subnet Name String object representation of the sub systems sub net name default as None
# Returns: Dictionary Object of the updated configuration
def sensor_check(sensor):
    for i in sensor:
        b = sensor[i]
        b["id"] = generate_hash('sen_')
        if not {"type", "units", "initial_value", "variability"}.issubset(b.keys()) \
                or b["type"] not in valid_sensor_types \
                or not isinstance(b["initial_value"],(int,float)) \
                or not isinstance(b["variability"],(int,float)):
            raise Exception("Invalid or missing data for Sensor: %s\n Sensors must have defined: "
                            "type, units, initial_value, variability" % i)
        sensor[i] = b
    return sensor


# Method: Actuator Check
# Description: Checks Actuator Dictionary Fields to ensure proper configuration if the actuator is valid and if a
# sub system then an IP address is assigned or else the ip address will be defined as localhost 127.0.0.1
# Arguments: Actuator Dictionary Object of the Actuator's configuration
#            Subnet Name String object representation of the sub systems sub net name default as None
# Returns: Dictionary Object of the updated configuration
def actuator_check(actuator):
    for i in actuator:
        b = actuator[i]
        b["id"] = generate_hash('act_')
        if not {"type", "initial_value"}.issubset(b.keys()) \
                or b["type"] not in valid_actuator_types:
            raise Exception("Invalid or missing data for Actuator: %s\n Actuators must have defined: "
                            "type, initial_value" % i)
    return actuator


# Method: Device Check
# Description: Recursive Function that walks the configuration file and checks to ensure that all systems are defined
# properly. This method checks all sub devices, actuators, and sensors.
# Arguments: config Dictionary Object of device to check
#            subnet_name String object name of subnet if any default as None
# Returns: Dictionary Object of the updated configuration
def device_check(config, subnet_name=None):
    if hasattr(config, "keys"):
        if not {"name_system", "name", "location", "device_type"}.issubset(config.keys()) \
                or config["device_type"].lower() not in valid_device_types:
            raise Exception("Device %s is incorrectly defined devices must at least have: "
                            "name_system, name, location, device_type %s" % (config["name"], config.keys()))

        if config["device_type"].lower() == "human-machine interface":
            config = hmi_check(config)
            subnet_name = config["id"]

        elif config["device_type"].lower() == "controller":
            config = controller_check(config, subnet_name)

        if 'sensors' not in config:
            config['senors'] = {}
        elif hasattr(config['sensors'], "keys"):
            config['sensors'] = sensor_check(config['sensors'])

        if 'actuators' not in config:
            config['actuators'] = {}
        elif hasattr(config["actuators"], "keys"):
            config['actuators'] = actuator_check(config['actuators'])

        if 'sub_devices' not in config:
            config['sub_devices'] = {}

        if hasattr(config["sub_devices"], "keys"):
            for i in config["sub_devices"]:
                config["sub_devices"][i] = device_check(config["sub_devices"][i], subnet_name)
        return config
    return {}


def controller_check(config, subnet_name=None):
    config["id"] = generate_hash('con_')
    if subnet_name and subnet_name in ip_addr:
        config["hmi_ip"] = network_list[subnet_name]["hmi_ip"]
        config["host_ip"] = ip_addr[subnet_name].pop(0)
        config["hmi_port"] = port
        config["host_port"] = port
        config["interface"] = network_list[subnet_name]["interface"]
        config["network"] = network_list[subnet_name]["network"]
        config["gateway"] = network_list[subnet_name]["gateway"]
    else:
        config["hmi_ip"] = "127.0.0.1"
        config["host_ip"] = "127.0.0.1"
        config["hmi_port"] = port
        config["host_port"] = port + 1
        config["interface"] = "lo"
    return config


def hmi_check(config):
    config["id"] = generate_hash('hmi_')
    if "host_ip" not in config:
        config["host_ip"] = "127.0.0.1"

    if "hmi_ip" not in config:
        config["hmi_ip"] = "127.0.0.1"

    if "interface" not in config:
        config["interface"] = "lo"

    if config["host_ip"] == config["hmi_ip"]:
        config["host_port"] = port
        config["hmi_port"] = port + 1
    else:
        config["host_port"] = port
        config["hmi_port"] = port
    s = config["hmi_ip"].split(".")
    generate_ipaddr(s[0] + "." + s[1] + "." + s[2] + ".0/24", config['id'], config["interface"], config["hmi_ip"])
    return config


def historian_check(config):
    config['id'] = generate_hash('his_')
    if hasattr(config, "keys"):
        if not {"name_system","name","location","device_type"}.issubset(config.keys()) \
                or config["device_type"].lower() not in valid_device_types:
            raise Exception("Device %s is incorrectly defined devices must at least have: "
                            "name_system,name,location,device_type" % config["name"])
        if "port" in config and int(config["port"]):
            global port
            port = int(config["port"])
        if 'host_ip' not in config:
            config['host_ip'] = "127.0.0.1"

        if 'sensors' not in config:
            config['senors'] = {}

        if 'actuators' not in config:
            raise Exception("%s: Must at least have a status actuator" % config["name"])

        if 'sub_devices' not in config:
            raise Exception("%s: Must have at lease one sub device of type Human-Machine Interface" % config["name"])
        return config
    return {}


# Method: Generate IP Address
# Description: Create Subnet IP addresses as defined by the subnet String by using IPy utility and appends it yo the
# ip_addr dictionary
# Arguments: subnet String object of subnet definition ex: 1.2.3.0/24
#            name String object name of the subsystem
#            interface String representation of interface name for PLC Storm Box machine ex: ens32 eth0
# Returns: String object host IP Address which is always the first ip address of the subnet ex: 1.2.3.1
def generate_ipaddr(subnet, name, interface, hmi_ip):
    ip = IP(subnet)
    host_ip = None
    for i in ip:
        if name not in ip_addr:
            ip_addr[name] = []
        elif not host_ip:
            host_ip = i.strNormal()
        elif i.strNormal() == hmi_ip:
            continue
        else:
            ip_addr[name].append(i.strNormal())
    network_list[name] = {"interface": interface, "gateway": host_ip, "hmi_ip": hmi_ip, "network": name}


# Method: Tree Walk
# Description: Once the configuration has completed validation, the system will be written to the postgres database.
# This method recursively walks through the configuration file and writes to the device and plc tables and creates
# the plc sub device tables
# Arguments: cur Psycopg2 Cursor object to execute postgres system calls
#            config Dictionary object of Device
# Returns: Dictionary Object of the updated configuration
def tree_walk(cur, config):
    try:
        slave = []
        if hasattr(config["sub_devices"], "keys") and config["sub_devices"].keys():
            for i in config["sub_devices"]:
                config["sub_devices"][i] = tree_walk(cur, config["sub_devices"][i])
                slave.append(config["sub_devices"][i]['id'])
        if hasattr(config["sensors"], "keys"):
            for i in config["sensors"]:
                config["sensors"][i] = add_sensor(cur, i, config["sensors"][i], config["name"])
                slave.append(config["sensors"][i]['id'])
        if hasattr(config["actuators"], "keys"):
            for i in config["actuators"]:
                if config["actuators"][i]["type"] == "variable":
                    if not hasattr(config["sensors"], "keys"):
                        raise Exception("%s has a type of variable but has no Sensor within this device. "
                                        "Their must be a sensor defined in order have a type of variable." % i)
                    else:
                        config["actuators"][i]["RID"] = config["sensors"][config["actuators"][i]["master"]]["id"]

                elif config["actuators"][i]["type"] == "relational":
                    if not hasattr(config["sensors"], "keys"):
                        raise Exception("%s has a type of relational but has no Sensor within this device. "
                                        "Their must be a sensor defined in order have a type of relational" % i)
                    else:
                        config["actuators"][i]["RID"] = config["sensors"][config["actuators"][i]["master"]]["id"]

                elif config["actuators"][i]["type"] == "locked" or config["actuators"][i]["type"] == "live-stream":
                    if not hasattr(config["sensors"], "keys"):
                        raise Exception("%s has a type of relational but has no Sensor within this device. "
                                        "Their must be a sensor defined in order have a type of locked" % i)
                    else:
                        config["actuators"][i]["RID"] = config["sensors"][config["actuators"][i]["master"]]["id"]
                        config["actuators"][i]['relationship'] = "reflective"

                config["actuators"][i] = add_actuator(cur, i, config["actuators"][i], config["name"])
                slave.append(config["actuators"][i]['id'])
        config["slave"] = slave
        config = add_controller(cur, config)
        return config
    except KeyError as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print('KeyError - Reason: %s Line: %s' % (e,exc_tb.tb_lineno))
        sys.exit()


# Method: Initialize
# Description: Validates configuration file, creates and writes to postgres databases, and creates the PLC configuration
# file
# Arguments: cur Psycopg2 Cursor object to execute postgres system calls
#            filename String object of path to the configuration file
# Returns: Dictionary Object of updated file Configuration
def init(filename,cur):
    """Initialize SCADA database based on config file"""
    try:
        config = json.loads(open(filename, 'r').read())

        if 'Historian' not in config:
            raise Exception("No root controller description found.")

        config = config["Historian"]

        if not hasattr(config["sub_devices"], "keys") \
                and not hasattr(config["sensors"], "keys") \
                and not hasattr(config["actuators"], "keys"):
            raise Exception("Only root node is defined and no actual SCADA devices")

        print("Initializing Device Map for:", config['name_system'])

        cur.execute("select exists(select * from information_schema.tables where table_name=%(table_str)s)",
                    {'table_str': "devices"})

        if cur.fetchone()[0]:
            print("Devices table already exists. Leaving it there")
        else:
            print("Devices table doesn't exist. Creating new one")
            create_main_table(cur)
            create_main_plc_table(cur)

        config = historian_check(config)
        config = device_check(config)
        config = tree_walk(cur, config)

        return config
    except IOError as e:
        print("Error opening '%s': File Not Found" % filename)
        print(e.message)
        sys.exit()
    except json as e:
        print("ERROR in processing JSON: Formatting error: %s at pos: %s line: %s column: %s" %
              (e.msg, e.pos, e.lineno, e.colno))
        sys.exit()
    except KeyError as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print('KeyError - Reason: %s Line: %s' % (e, exc_tb.tb_lineno))
        sys.exit()
    except Exception as e:
        print(e)
        sys.exit()


# Method: Check Sub System
# Description: Checks if connection to the defined sub system is possible
# Arguments: config Dictionary Object of validated configuration
#            connection String object of connection string all except the host definition
# Returns: Boolean value if all sub systems have valid connection
def check_sub_systems(config, connection):
    r = True
    for i in config["sub_devices"]:
        if "host_ip" in i:
            try:
                c = psycopg2.connect(connection + config["sub_devices"]["host_ip"])
                print("Sub System: %s was successfully connected." % i["name"])
                c = r.cursor()
                c.close()
                r.close()
            except Exception as e:
                print("Failure to connect to Sub System %s with error: \n %s" % (i["name"], str(e)))
                r = False
    return r


# Method: Initialize
# Description: Creates and writes to postgres databases to sub system machines
# Arguments: config Dictionary Object of validated configuration
#            cur Psycopg2 Cursor object to execute postgres system calls
#            d String object of database name
#            u String object of database User Name
# Returns: Void
def subsystem_init(config, cur, d, u):
    print("Subsystem: %s is being connected" % config["name"])
    clear_existing_db(cur, d, u)
    create_main_table(cur)
    create_main_plc_table(cur)
    tree_walk(cur, config)


# Method: Usage
# Description: Displays how to use CLI when user uses -h argument
# Arguments: full boolean object and defines if to display entire usage or just partial
# Returns: Void
def usage(full=False):
    """Terminal usage message for program"""
    print("[python] ./init.py [-hkvV] [-f <config-file>] [-d <database-name>] [-u <db-username>] ")
    if full:
        print("""
        -h --help      : Print Help Message
        -v --version    : Print version Message
        -k --keep       : Don't wipe old db before rebuilding
        -f --infile     : Config file to use
        -s --sub-system : Contains subsystems on external machines. Must have a defined connection_string within the configuration file.
        -d --database   : Which database to use
        -u --username   : Which database user to log in as
        -p --password   : User's password to access the database (Required on windows systems)
        """)


# Method: Sub System Error
# Description: Displays basic trouble shooting string to help users utilize the sub system function of the application
# Arguments: None
# Returns: Void
def subsystem_error():
    print("""
        An error occurred attempting to connect to the defined sub systems. Two possible issues are either
        the inability to connect to the sub system via network connection or the in ability to log into the sub system's
        postgres instance. Ensure network connectivity and the username supplied with the command line arguments is an
        established account the sub-system machine with permissions to CREATEDB.""")
    sys.exit()


# Method: Main
# Description: Main Function takes in CLI arguments and validates the user input and if valid initializes the
# application's functions to create the base for the PLC Simulation
# Arguments: See Usage Method for Arguments
# Returns: Void
if __name__ == '__main__':
    # Default config file
    inputfile = None
    clear_db = True
    dbname = None
    dbusername = None
    dbpw = None
    sub = False
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvksf:d:u:p:", ["help", "version", "infile=", "database=",
                                                                  "username=", "password=", "sub-system"])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(str(err))  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-v", "--version"):
            print("CERT Scada Simulator, Initialization v1.1")
            sys.exit()
        elif o in ("-h", "--help"):
            usage(usage(full=True))
            sys.exit()
        elif o in ("-s", "--sub-system"):
            sub = True
        elif o in ("-t", "--hostname"):
            host = a
        elif o in ("-k", "--keep"):
            clear_db = False
        elif o in ("-f", "--infile"):
            inputfile = a
        elif o in ("-d", "--database"):
            dbname = a
        elif o in ("-u", "--username"):
            dbusername = a
        elif o in ("-p", "--password"):
            dbpw = a
        else:
            assert False, "unhandled option"
    
    if not dbname or not dbusername or not inputfile:
        usage(usage(full=True))
        sys.exit()

    try:
        print("########### Doing a dry run to check for errors ###########")
        db_connect = psycopg2.connect("dbname=%s user=%s password=%s" % (dbname, dbusername, dbpw))
        db_connect.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cur = db_connect.cursor()

        if clear_db:
            clear_existing_db(cur, dbname, dbusername)

        config = init(inputfile, cur)
        if sub:
            config["id"] = "HISTORIAN"
            config["ip"] = config["host_ip"]
            check_connect=True
            while check_connect:
                check_connect=False
                for i in config["sub_devices"]:
                    try:
                        b = config["sub_devices"][i]
                        c = psycopg2.connect("dbname=%s user=%s password=%s host=%s" % (dbname, dbusername, dbpw, b["host_ip"]))
                        c.close()
                        check_connect = False if not check_connect else True
                    except psycopg2.Error:
                        print("Unable to Connect to %s" % b["host_ip"])
                        check_connect=True
                        time.sleep(10)
                        break
        
            for i in config["sub_devices"]:
                print("Now I am here")
                b = config["sub_devices"][i]
                if "host_ip" in b:
                    if check_sub_systems(b, "dbname=%s user=%s password=%s host=%s" %
                            (dbname, dbusername, dbpw, b["host_ip"])):
                            c = psycopg2.connect("dbname=%s user=%s password=%s host=%s" %
                                                 (dbname, dbusername, dbpw, b["host_ip"]))
                            c.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
                            r = c.cursor()
                            subsystem_init(b, r, dbname, dbusername)
                            add_controller(r, config)
                            r.close()
                            c.close()
                    else:
                        subsystem_error()

    except psycopg2.Error as e:
        print("Unable to connect to Postgres Database: %s" % e.pgerror)
        sys.exit()

    db_connect.close()
    print("Connection to database closed")
