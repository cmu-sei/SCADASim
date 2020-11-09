#!/usr/bin/env python

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


import sys
import yaml
from os import path

# (Default) open txt file to get config.yaml file name IF path of config file was not supplied as argument to master.py
# strip any trailing /n from string
if len(sys.argv) == 1:
    f = open("/usr/local/bin/scadasim_pymodbus_plc/startup/config_file_name.txt", 'r')
    file_name = f.read()
    file_name = file_name.rstrip()
    f.close()
else:
    file_name = sys.argv[1]

# open yaml config file, build object
config_file = open(file_name, 'r')
config_yaml = yaml.safe_load(config_file)
config_file.close()

# get number of plc devices from MASTER section of the config file
num_of_plc = config_yaml['MASTER']['num_of_PLC']
# create backup files if they do not already exist - 1 for each PLC device
i = 0
while(i < num_of_plc):
    num = str(i)
    plc_device_name = 'PLC ' + num
    # keep in the src repo, in format of "backup_N.yaml", where N is the ID of the PLC device
    backup_file_name = '/usr/local/bin/scadasim_pymodbus_plc/backups/backup_' + num + '.yaml'
    
    # collect num of register/coils for each plc device
    hr_values = config_yaml[plc_device_name]['DATASTORE']['hr']['values']
    co_values = config_yaml[plc_device_name]['DATASTORE']['co']['values']
    di_values = config_yaml[plc_device_name]['DATASTORE']['di']['values']
    ir_values = config_yaml[plc_device_name]['DATASTORE']['ir']['values']

    # check if file exists
    if (path.exists(backup_file_name) == False or path.getsize(backup_file_name) == 0):
        # create file - only storing the register starting address and values 
        backup_dict = {}
        backup = open(backup_file_name, 'w+')
        backup_dict['DATASTORE'] = {'hr': {'start_addr': 1, 'values': hr_values}, 'ir': {'start_addr': 1, 'values': ir_values}, 'co': {'start_addr': 1, 'values': co_values}, 'di': {'start_addr': 1, 'values': di_values}}
        yaml.dump(backup_dict, backup)
        backup.close()
    i = i + 1

# return number of backup files created and the config filepath to bash startup script
print str(num_of_plc) + ' ' + file_name

