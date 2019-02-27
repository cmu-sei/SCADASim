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


# SEI SCADA System Simulation (4S) V1.0 PLC Engine Manager

import sys
import json
import getopt
import requests
import subprocess
import time


# Method: Generate Network
# Description: Generate Docker networks and attaches networks onto interfaces within the PLC Box
# Arguments: Name: String of the subsystem controller
#            Interface: String of the interface to attach to
#            Subnet: String of the subnet mask
#            Gateway: String of the gateway
# Returns: Boolean True is success and False if failure
def generate_network(name, interface, gateway):
    print "Generating Network: %s" % name
    s = gateway.split(".")
    try:
        subprocess.call("brctl addbr br-%s" % name, shell=True)
        subprocess.call("docker network create -o \"com.docker.network.bridge.name\"=\"br-%s\" --subnet %s --gateway %s %s" % (name, "%s.%s.%s.0/24" % (s[0], s[1], s[2]), "%s.%s.%s.254" % (s[0], s[1], s[2]), name), shell=True)
        subprocess.call("brctl addif br-%s %s" % (name, interface), shell=True)
        return True
    except subprocess.CalledProcessError as e:
        print e.output
        return False


# Method: Spawn Containers
# Description: Generate Docker containers defined bt the device dictionary object. The containers then will start the
# PLC Engine script
# Arguments: Device ID: Integer of the device being created
#            Device: Dictionary object of the device's configuration
# Returns: void
def spawn_containers(config, network):
    print("%s: spawning on Network %s" % (config["id"], network))
    if config["network"] == "localhost":
        return
    subprocess.call("docker run -t --name %s --net %s --ip %s -d plc -D %s -I %s -P %s" %
                    (config["id"], config["network"][:10], config["host_ip"], config["id"], network["ip"], network["port"]), shell=True)


# Method: Usage
# Description: displays CLI usage
# Arguments: None
# Returns: Void
def usage(full=False):
    """Terminal usage message for program"""
    print("[python] ./plc-launcher.py [-hv] [-f <config-file>] [-H [<hostname>]]")
    if full:
        print("""
        -h --help       : Print Help Message
        -v --version    : Print version Message
        -H --hostname   : Hostname of the Historian/Monitor/CentralController or
        just where ever you can pull the config file
        -f --file       : Uses stored local config file if no host server default = ./config.json
        -k --keep       : Keep existing docker containers
        """)


# Method: Main
# Description: Kicks off the HMI Server from CLI
# Arguments: See Usage
# Returns: Void
if __name__ == "__main__":
    # Default config file
    config = None
    host = None
    keep = True
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hkvf:n:", ["keep", "help", "version", "file=", "hostname="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(str(err))  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-V", "--version"):
            print("PLC Launcher, v1.0")
            sys.exit()
        elif o in ("-h", "--help"):
            usage(full=True)
            sys.exit()
        elif o in ("-f", "-file"):
            configfile = a
        elif o in ("-k", "-keep"):
            keep = False
        elif o in ("-n", "--hostname"):
            host = a
        else:
            assert False, "unhandled option"

    try:
        if config:
            config = json.loads(open(config, 'r').read())
        else:
            while True:
                try:
                    if requests.get("http://%s/api/" % host).status_code == 200:
                        config = requests.get("http://%s/api/controller/config" % host).json()
                        break
                except requests.ConnectionError as e:
                    print(e)
                    time.sleep(30)
        hmi_list = {}
        for i in config["hmi"]:
            hmi_list[i["id"][:10]] = {"ip": i["host_ip"], "port": i["host_port"]}
            if i["network"] == "localhost" or i["network"] == "127.0.0.1":
                continue
            else:
                if not generate_network(i["id"][:10], i["interface"], i["hmi_ip"]):
                    raise Exception("Please check your configuration file the "
                                "following network was unable to generate: %s" % i)
        for i in config["con"]:
            spawn_containers(i, hmi_list[i['network'][:10]])

        print("Press CTRL-C to shut down service")
        while True:
            continue
    except KeyboardInterrupt:
        print "Caught Interrupt, spinning down containers and exiting"
        exit()
    except Exception as e:
        print e.message
        sys.exit()
    except IOError:
        print("Error opening '%s': File Not Found" % config)
        sys.exit()
