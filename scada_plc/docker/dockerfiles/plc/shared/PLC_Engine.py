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

# SEI SCADA System Simulation (4S) V1.0 PLC Device Engine used on docker images

from pymodbus.client.sync import ModbusTcpClient
from pymodbus.exceptions import ConnectionException

import sys
import random
import time
import subprocess


# Class: PLC
# Description: Base class for PLC device to communicate with the HMI and simulates modbus traffice between PLC and HMI
class PLC:

    # Method: Constructor
    # Description: Initializes the PLC device
    # Arguments: self: Initialized PLC object
    #            a: String IP address of HMI
    #            p: Integer port number to communicate with the HMI
    #            i: Float Initial value of PLC device
    #            t: List of float Threshold value at which the device will fail
    #            v: Integer Variance value
    # Returns: PLC object of initialized PLC Device
    def __init__(self, a, p, s):
        print "Client IP: %s Port: %s" % (a,p)
        self.client = ModbusTcpClient(a, port=p)
        self.status_reg_num = s

    # Method: Connect
    # Description: Connects PLC device with HMI
    # Arguments: self: Initialized PLC object
    # Returns: Void
    def connect(self):
        connected = False
        while not connected:
            try:
                connected = self.client.connect()
            except Exception as e:
                print "Connection Error %s" % e
                time.sleep(30)

    # Method: Disconnect
    # Description: Disconnects PLC device from HMI
    # Arguments: self: Initialized PLC object
    # Returns: Void
    def disconnect(self):
        self.client.close()
        sys.exit(0)

    # Method: Read Register
    # Description: Modbus Read register request
    # Arguments: Reg: Modbus connection between PLC device and HMI Server
    #            ID: integer id number of device
    # Returns: Integer value of register requested
    def read_reg(self, reg_num):
        return int(self.client.read_holding_registers(int(reg_num)).registers[0])

    # Method: Write Register
    # Description: Modbus Write register request
    # Arguments: Reg: Modbus connection between PLC device and HMI Server
    #            ID: integer id number of device
    #            Value: integer value to write to register
    # Returns: void
    def write_reg(self, reg_num, value):
        print "Reg Num: %s Value: %s" % (reg_num, value)
        self.client.write_register(reg_num, value)

    def status(self):
        return False if hex(self.read_reg(self.status_reg_num)) == "0xffff" else True


# Class: Actuator extends PLC
# Description: Actuator objects that simulates traffic between HMI and actuator PLC device
class Actuator:
    def __init__(self, i, n, s=False):
        self.value = int(i)
        self.reg_num = n
        self.sleep = s


# Class: Sensor extends PLC
# Description: Sensor objects that simulates traffic between HMI and sensor PLC device
class Sensor:
    def __init__(self, i, n, t, v, y, p=None, g=None, s=False):
        self.value = i
        self.reg_num = n
        self.tolerance = t
        self.variability = v
        self.type = y
        self.pos = p
        self.neg = g
        self.sleep = s

    def update(self, p, n):
        if self.sleep:
            return 0
        if self.type == ["open", "locked", "enabled"]:
            return 0 if self.value == 1 and random.randint(0, 100000) == 1 else 1
        if p and random.randint(0, 100000) == 1:
            self.value += random.randint(0, p - n) if p - n > 0 else random.randint(p - n, 0)
        v = self.value + random.randint(-self.variability, self.variability)
        if self.tolerance and (v < self.tolerance[0] or v > self.tolerance[1]):
            return -1
        else:
            return v



