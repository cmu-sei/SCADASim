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


import yaml, sys

'''
@brief obtain input on parameters for linear behavior
'''
def linear_behavior_setup():
    dict = {}
    dict['variance'] = int(raw_input("Variance of linear function:\n"))
    dict['address'] = raw_input("Starting address for register(s) to control:\n")
    dict['time'] = int(raw_input("Frequency to update register values (in seconds):\n"))
    dict['count'] = int(raw_input("Number of registers to control:\n"))
    return dict


def linear_coil_dependent_setup():
    dict = {}
    dict = linear_behavior_setup()
    dict['max'] = int(raw_input("Max value of the register(s):\n"))
    dict['coil_address'] = int(raw_input("Address of the coil it is dependent on:\n"))
    dict['default_coil_value'] = int(raw_input("Default coil value - default state that would mean normal behavior:\n"))
    return dict

'''
@brief obtain input on parameters for random behavior
'''
def random_behavior_setup():
    dict = {}
    dict['min'] = int(raw_input("Minimum value the register can hold:\n"))
    dict['max'] = int(raw_input("Maximum value the register can hold:\n"))
    dict['address'] = raw_input("Starting address for register(s) to control:\n")
    dict['time'] = int(raw_input("Frequency to update register values (in seconds):\n"))
    dict['count'] = int(raw_input("Number of registers to control:\n"))
    return dict

def constant_behavior_setup():
    dict = {}
    dict['num'] = int(raw_input("Value that the coil register should try to stay constant at:\n"))
    dict['address'] = raw_input("Starting address for register(s) to control:\n")
    dict['time'] = int(raw_input("Frequency to update register values (in seconds):\n"))
    dict['count'] = int(raw_input("Number of registers to control:\n"))
    return dict
'''
@brief obtain input to setup the datastore
'''
def datastore_setup():
    datastore_dict = {'hr': {'start_addr': 1, 'values': [1, 2, 3]}, 'ir': {'start_addr': 1, 'values': [4, 4, 4]}, 'co': {'start_addr': 1, 'values': [0, 0, 0]}, 'di': {'start_addr': 1, 'values': [100, 250, 0]}}
    print("\n\nConfiguring Datastore\n")
    # holding reg setup
    start_addr = int(raw_input("Start addr for hr?\n"))
    values = raw_input("Initial values for hr?\n").split()
    values = map(int, values)
    datastore_dict['hr']['start_addr'] = start_addr
    datastore_dict['hr']['values'] = values
    for i in range(len(values)):
        datastore_dict['hr']['behavior_' + str(i+1)] = {}
        cur_behavior = raw_input("Linear, linear_coil_dependent, or random behavior?\n")
        datastore_dict['hr']['behavior_' + str(i+1)]['type'] = cur_behavior
        if cur_behavior == "linear":
            behavior_sub_dict = linear_behavior_setup()
        elif cur_behavior == "linear_coil_dependent":
            behavior_sub_dict = linear_coil_dependent_setup()
        elif cur_behavior == "random":
            behavior_sub_dict = random_behavior_setup()
        datastore_dict['hr']['behavior_' + str(i+1)].update(behavior_sub_dict)

    # input reg setup
    start_addr = int(raw_input("Start addr for ir?\n"))
    values = raw_input("Initial values for ir?\n").split()
    values = map(int, values)
    datastore_dict['ir']['start_addr'] = start_addr
    datastore_dict['ir']['values'] = values

    # coil reg setup
    start_addr = int(raw_input("Start addr for co?\n"))
    values = raw_input("Initial values for co?\n").split()
    values = map(int, values)
    datastore_dict['co']['start_addr'] = start_addr
    datastore_dict['co']['values'] = values
    for i in range(len(values)):
        datastore_dict['co']['behavior_' + str(i+1)] = {}
        cur_behavior = raw_input("constant or none behavior?\n")
        datastore_dict['co']['behavior_' + str(i+1)]['type'] = cur_behavior
        if cur_behavior == "constant":
            behavior_sub_dict = constant_behavior_setup()
            datastore_dict['co']['behavior_' + str(i+1)].update(behavior_sub_dict)

    # di reg setup
    start_addr = int(raw_input("Start addr for di?\n"))
    values = raw_input("Initial values for di?\n").split()
    values = map(int, values)
    datastore_dict['di']['start_addr'] = start_addr
    datastore_dict['di']['values'] = values
    return datastore_dict

'''
@brief obtain input on logging setup
'''
def logging_setup():
    logging_dict = {'logging_level': 'DEBUG', 'file': 'STDOUT', 'format': '%(asctime)-15s %(threadName)-15s %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s'}
    def_format = '%(asctime)-15s %(threadName)-15s %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s'
    print("\n\nConfiguring Logging\n")
    logging_dict['logging_level'] = raw_input("Enter logging level (CRITICAL, ERROR, WARNING, INFO, DEBUG, or NOTSET) :\n")
    logging_dict['file'] = raw_input("Enter STDOUT or valid filepath for logging destination:\n")
    logging_dict['format'] = raw_input("Enter NONE, DEFAULT (for '%(asctime)-15s %(threadName)-15s %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s'), or a valid format string:\n")
    if logging_dict['format'] == 'DEFAULT':
        logging_dict['format'] = def_format
    return logging_dict

'''
@brief obtain input on PyModbus Server setup
'''
def server_setup():
    server_dict = {'framer': 'RTU', 'type': 'serial', 'port': '/dev/ttyS1'}
    print("\n\nConfiguring Server\n")
    server_dict['type'] = raw_input("Enter type of PyModbus server (tcp, serial, etc):\n")
    server_dict['framer'] = raw_input("Enter type of framer (TCP, RTU, ASCII, etc):\n")
    server_dict['port'] = raw_input("Enter port used for server:\n")
    server_dict['address'] = raw_input("Enter address used for server (NONE if using serial server):\n")
    return server_dict

'''
@brief calls all of the other functions - encapsulates the setup of a PLC device
'''
def plc_setup():
    plc_config = {}
    plc_config['DATASTORE'] = datastore_setup()
    plc_config['LOGGING'] = logging_setup()
    plc_config['SERVER'] = server_setup()
    return plc_config

'''
@brief generates a master config file in YAML format
- Determines the number of PLC devices then calls plc_setup(), which in turn calls other functions, in order to finish it up and yaml.dump it to the config yaml file for later use
'''
def main():
    print("SCADASim 2.0 PLC config generator\n")

    config_dict = {'MASTER': {'num_of_PLC': 1}}
    num_devices = input("How many PLC devices? ")
    config_dict['MASTER']['num_of_PLC'] = int(num_devices)
    output_filename = raw_input("Enter the full path of the file the config should yaml.dump to OR enter 'DEFAULT': ")
    if output_filename == "DEFAULT":
        dump_filename = '/usr/local/bin/scadasim_pymodbus_plc/configs/test_generator_dump.yaml'
    else:
        dump_filename = output_filename

    if len(sys.argv) == 2:
      dump_filename = sys.argv[1]
    for i in range(int(num_devices)):
        print("\n\nConfiguring PLC " + str(i))
        config_dict["PLC " + str(i)] = plc_setup()
    print(config_dict)
    stream = open(dump_filename, 'w+')
    yaml.dump(config_dict, stream)
    stream.close()

if __name__ == "__main__":
    main()
