#!/usr/local/bin/python
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

# SEI SCADA System Simulation (4S) V1.0 Data Server Web front end interface

from flask import Flask, url_for, send_from_directory, request, render_template, jsonify
from gevent import wsgi
from DB_Driver import DatabaseDriver
import sys
import getopt
import time

# Global Variables
# Description: Global Variables to be utilized throughout application
# Arguments: App Flask Object as engine of Flask Server
#            UID String object of user ID of data server defined as parent node configuration
#            DB Object Database Driver Object to read and write to local Database
app = Flask(__name__, static_url_path='')
uid = None
db_obj = None


# Method: API
# Description: Displays the SEI Scada Simulation System(4S) version number. This is the base for the API system calls
# for 4S.
# Arguments: None
# Returns: Renders web page with version number
@app.route("/api/")
@app.route("/api")
def api():
    return "{'name':'CERT SCADA -- Buildings and Embedded Networks Defense Simulator, v1.0'}"


@app.route("/api/controller/config/")
@app.route("/api/controller/config")
def plc_manager_config(sub_system=None):
    return jsonify(db_obj.get_device_config())


# Method: Base Configuration
# Description: Returns a JSON object by default of the entire SCADA System defined by the config file. This is generated
# from the database created by the init file. If a sub system name is supplied then this method returns only the config
# for the defined sub system.
# Arguments: Sub System: String name for the desired sub system
# Returns: Renders/Returns the json object of the desired configurations
@app.route("/api/config/")
@app.route("/api/config")
@app.route("/api/config/<sub_system>")
@app.route("/api/config/<sub_system>/")
def base_config(sub_system=None):
    return jsonify(db_obj.build_config_file(sub_system))


# Method: PLC List
# Description: Returns a json object of all PLC devices which is used to troubleshoot the configuration file and to
# display all PLC device information on the INIT screen.
# Arguments: None
# Returns: Renders/Returns the json object of only PLC Devices
@app.route("/api/plc/")
@app.route("/api/plc")
def plc_list():
    return jsonify(db_obj.get_all_plc_list())


# Method: Device List
# Description: Returns a json object by default all Controller Devices or a specific device which is used to
# troubleshoot the configuration file
# Arguments: Device ID: String representation of the Hash ID stored in the database to return the devices configuration
# by default is None which return all devices.
# Returns: Renders/Returns the json object of only PLC Devices
@app.route("/api/devices/")
@app.route("/api/devices")
@app.route("/api/devices/<device_id>/")
@app.route("/api/devices/<device_id>")
def device_list(device_id=None):
    return jsonify(db_obj.get_device_list(device_id))


# Method: Sensor List
# Description: Returns a list with configuration of all Sensor devices or a specific Sensor device
# Arguments: Sensor ID: String representation of the Hash ID stored in the database to return the devices configuration
# Returns: Renders/Returns a list of all sensors' or a specific sensor's current configuration
@app.route("/api/sensors/")
@app.route("/api/sensors")
def sensors_list(sensor_id=None):
        return jsonify(db_obj.get_sensor_list(sensor_id))


# Method: Sensor Current
# Description: Allows users to insert an entry in the sensors or return the current value of a specific sensor
# Arguments: Sensor ID: String representation of the Hash ID stored in the database to return the devices configuration
#            FORM['newValue']: string representation of the newest sensor value
#            FORM['uid']: string representation of the HMI's id
# Returns: GET: Renders/Returns the current sensor information defined by Sensor ID
#          POST: Renders/Returns a string informing the user of the status of the attempted transaction
@app.route("/api/sensors/<sensor_id>/", methods=['GET', 'POST'])
@app.route("/api/sensors/<sensor_id>", methods=['GET', 'POST'])
@app.route("/api/sensors/<sensor_id>/<count>", methods=['GET', 'POST'])
@app.route("/api/sensors/<sensor_id>/<count>/", methods=['GET', 'POST'])
def sensor_current(sensor_id, count=0):
    if request.method == 'POST':
        if 'uid' in request.form and 'newValue' in request.form and \
                db_obj.set_sensor_value(sensor_id, float(request.form['newValue']), request.form['uid']):
            return "received %s update" % request.form['uid']
        else:
            return "FAILED %s update" % request.form['uid']
    if request.method == 'GET':
        if count:
            return jsonify({"id": db_obj.get_sensor_list(sensor_id)[0],
                            "data": db_obj.get_sensor_data(sensor_id, False)})
        else:
            return jsonify(db_obj.get_sensor_data(sensor_id))


# Method: Actuator List
# Description: Returns a list with configuration of all Actuators devices or a specific Actuator
# Arguments: Actuator ID: String representation of the Hash ID stored in the database to return the devices
# configuration
# Returns: Renders/Returns a list of all actuators' or a specific actuator's configuration
@app.route('/api/actuators/')
@app.route('/api/actuators')
def actuator_list():
    return jsonify(db_obj.get_actuator_list(actuator_id))


# Method: Actuator Current
# Description: Allows users to insert an entry in the actuator or return the current value of a specific sensor
# Arguments: Sensor ID: String representation of the Hash ID stored in the database to return the devices configuration
#            FORM['newValue']: string representation of the newest sensor value
#            FORM['uid']: string representation of the HMI's id
# Returns: GET: Renders/Returns the current sensor information defined by Sensor ID
#          POST: Renders/Returns a string informing the user of the status of the attempted transaction
@app.route('/api/actuators/<actuator_id>/', methods=['GET', 'POST'])
@app.route('/api/actuators/<actuator_id>', methods=['GET', 'POST'])
def actuator_value(actuator_id=None):
    if request.method == 'POST':
        print request.form
        if 'uid' in request.form and 'newValue' in request.form and \
                db_obj.set_actuator_value(actuator_id, float(request.form['newValue']), request.form['uid']):
            return "received %s update" % request.form['uid']
        else:
            return "FAILED %s update" % request.form['uid']
    if request.method == 'GET':
        return jsonify(db_obj.get_actuator_value(actuator_id))


# Method: Get Device Tree
# Description: Returns the configuration file for the javascript tree of all devices within the SCADA network
# Arguments: Device ID: string of the hash value of the device id if a sub devices is required default None returns
# all devices defined
# Returns: Render/Returns device tree configuration file as a json object
@app.route('/api/device/tree')
@app.route('/api/device/tree/')
@app.route('/api/device/tree/<device_id>')
@app.route('/api/device/tree/<device_id>/')
def get_device_tree(device_id=None):
    return jsonify(db_obj.get_tree_json(device_id))

# Method: JavaScript Path
# Description: returns javascipt directory
# Arguments: path for path to return
# Returns: javascript files to be used for application
@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('js', path)


# Method: Images Path
# Description: returns Images directory
# Arguments: path for path to return
# Returns: images files to be used for application
@app.route('/images/<path:path>')
def send_images(path):
    return send_from_directory('images', path)


# Method: Fonts Path
# Description: returns the path to the fonts directory
# Arguments: path for path to return
# Returns: fonts files to be used for application
@app.route('/fonts/<path:path>')
def send_fonts(path):
    return send_from_directory('fonts', path)


# Method: CSS Path
# Description: returns the path to the javascipt directory
# Arguments: path for path to return
# Returns: javascript files to be used for application
@app.route('/css/<path:path>')
def send_css(path):
    return send_from_directory('css', path)


# Method: Index
# Description: Catch All Route redirects undefined routes to the index page
# Arguments: None
# Returns: Renders index.html file
@app.route('/')
@app.route('/index/')
@app.route('/index')
@app.route('/index.html')
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def homepage():
    return render_template('index.html',
                           system_name=db_obj.get_device_list(db_obj.get_root_id())[0]['name'],
                           root_id=db_obj.get_root_id(),
                           sensor_list=db_obj.get_sensor_list())


# Method: Usage
# Description: displays CLI usage
# Arguments: None
# Returns: Void
def usage():
    """Terminal usage message for program"""
    print("[python3] ./dataserver.py [-hVv] [-p <port-num>] [-d <database-name>] [-u <db-username>] ")
    print("""        -h --help      : Print Help Message
    -V --version   : Print version Message
    -i --ip        : IP to listen on (default='localhost')
    -p --port      : Web server port to use (default='5000').
                     Using a low-numbered port (e.g. 80) may require sudo
    -d --database  : Which database to use
    -u --username  : Which database user to log in as
    -w --password  : User's password to access the database (Required on windows systems)
        """)

# Method: Main
# Description: Kicks off the data server from CLI
# Arguments: See Usage
# Returns: Void
if __name__ == "__main__":
    # Default Values
    ipaddr = '127.0.0.1'
    port = 5000
    verbose = False
    dbname = None
    dbusername = None
    dbpw = None
    actuators_in_network_map = True

    # Process options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvVaAi:p:d:u:w:", ["help", "verbose", "version", "show-actuators", "ipaddr=", "port=", "database=", "username=", "password="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(str(err))  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-v", "--verbose"):
            verbose = True
        elif o in ("-V", "--version"):
            print("CERT Scada Simulator, Web Server v1.0")
            sys.exit()
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        if o in ("-p", "--port"):
            port = int(a)
        elif o in ("-i", "--ipaddr"):
            ipaddr = a
        elif o in ("-d", "--database"):
            dbname = a
        elif o in ("-u", "--username"):
            dbusername = a
        elif o in ("-w", "--password"):
            dbpw = a
        elif o in ("-a", "--show-actuators"):
            actuators_in_network_map = True
        elif o in ("-A", "--hide-actuators"):
            actuators_in_network_map = False
        else:
            assert False, "unhandled option"
    if not dbusername or not dbname:
        usage()
        sys.exit()
    try:
        db_obj = DatabaseDriver(dbname, dbusername, dbpw)
	db_obj.connect()
        while not db_obj.database_populated():
            print("Database has not been initiated")
            time.sleep(10)
        l = db_obj.get_device_list()
        for i in l:
            if "his" in i:
                uid = i['id']
                break
            l.pop()
            for j in l:
                if i["id"] in j["slave_devices"]:
                    break
            uid = i['id']
            break

        print("Serving application on '%s:%s'" % (ipaddr, port))
        with app.test_request_context():
            print("API located at '%s:%s%s'" % (ipaddr, port, url_for('api')))
        print("\n")
        server = wsgi.WSGIServer((ipaddr, port), app)
        server.serve_forever()
    except Exception as e:
        print(e)
