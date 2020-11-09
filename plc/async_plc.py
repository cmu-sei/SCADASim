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


'''
Asynchronous PyModbus Server with Client Functionality
  Used for SCADASim 2.0
'''

# --------------------------------------------------------------------------- #
# import the modbus libraries we need
# --------------------------------------------------------------------------- #
from pymodbus.server.asynchronous import StartSerialServer
from pymodbus.server.asynchronous import StartTcpServer
from pymodbus.server.asynchronous import StartUdpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import ModbusRtuFramer, ModbusAsciiFramer, ModbusBinaryFramer

# --------------------------------------------------------------------------- #
# import the other libraries we need
# --------------------------------------------------------------------------- #
from datastore import *
from helper import *
from time import *
from threading import Thread
import logging, yaml
import sys, os, argparse


'''
@brief reads from backup, initializes the datastore, starts the backup thread and the register behavior threads, then starts the server
'''
def run_updating_server(config_list, backup_filename, log):
    # ----------------------------------------------------------------------- # 
    # initialize your data store
    # ----------------------------------------------------------------------- # 
    # Run datastore_backup_on_start to use the most recent values of the datablocks, as the layout in the master config will only reflect initial values
    # If this is the first time this is used, the backup file will match up with what is laid out in the master config (due to master.py)
    datastore_config = datastore_backup_on_start(backup_filename)
    if datastore_config == -1:
        print("Issue with backup file - either not created or empty. Exiting program.")
        sys.exit()
    
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(datastore_config['di']['start_addr'], datastore_config['di']['values']),
        co=ModbusSequentialDataBlock(datastore_config['co']['start_addr'], datastore_config['co']['values']),
        hr=ModbusSequentialDataBlock(datastore_config['hr']['start_addr'], datastore_config['hr']['values']),
        ir=ModbusSequentialDataBlock(datastore_config['ir']['start_addr'], datastore_config['ir']['values']))
    # Could have multiple slaves, with their own addressing. Since we have 1 PLC device handled by every async_plc.py, it is not necessary
    context = ModbusServerContext(slaves=store, single=True)

    # setup a thread with target as datastore_backup_to_yaml to start here, before other threads
    #     this will continuously read from the context to write to a backup yaml file
    backup_thread = Thread(target=datastore_backup_to_yaml, args=(context, backup_filename))
    backup_thread.daemon = True
    backup_thread.start()
 
    # start register behaviors. Updating writer is started off, which will spawn a thread for every holding register based on the config
    thread = Thread(target=updating_writer, args=(context, config_list, time, log, backup_filename))
    thread.daemon = True
    thread.start()

    # Starting the server
    server_config = config_list['SERVER']
    framer = configure_server_framer(server_config)
    if server_config['type'] == 'serial':
        StartSerialServer(context, port=server_config['port'], framer=framer)
    elif server_config['type'] == 'udp':
        StartUdpServer(context, identity=identity, address=(server_config['address'], int(server_config['port'])))
    elif server_config['type'] == 'tcp':
        if server_config['framer'] == 'RTU':
            StartTcpServer(context, identity=identity, address=(server_config['address'], int(server_config['port'])), framer=framer)
        else:
            StartTcpServer(context, address=(server_config['address'], int(server_config['port'])))

'''
@brief parse args, handle master config, setup logging, then call run_updating_server
'''
def main():
    # --- BEGIN argparse handling ---
    parser = argparse.ArgumentParser(description = "Main program for PLC device based off PyModbus")
    parser.add_argument("--n", "--num_of_PLC", help = "The number of the PLC device")
    parser.add_argument("--c", "--config_filename", help = "Name of the master config file")
    args = parser.parse_args()
    if args.n is None or args.c is None:
        print("Need to run async_plc.py with --n and --c arguments. Run 'python async_plc.py --h' for help")
        return
    print( args )
    num_of_PLC = args.n
    master_config_filename = args.c
    backup_filename = '/usr/local/bin/scadasim_pymodbus_plc/backups/backup_' + args.n + '.yaml'
    # --- END argparse handling ---

    stream = open(master_config_filename, 'r')
    config_list = yaml.safe_load(stream)
    stream.close()
    # Only get the current PLC's configuration dictionary
    config_list = config_list["PLC " + num_of_PLC]

    # --- BEGIN LOGGING SETUP ---
    FORMAT = config_list['LOGGING']['format']
    # Add logic based on whether a file is used or stdout
    #   AND whether a format string is used or not
    if config_list['LOGGING']['file'] == 'STDOUT':
        if FORMAT == 'NONE':
            logging.basicConfig()
        else:
            logging.basicConfig(format=FORMAT)
    else:
        if FORMAT == 'NONE':
            logging.basicConfig(filename=config_list['LOGGING']['file'])
        else:
            logging.basicConfig(format=FORMAT, filename=config_list['LOGGING']['file'])
    log = logging.getLogger()
    configure_logging_level(config_list['LOGGING']['logging_level'], log)
    # --- END LOGGING SETUP ---
    run_updating_server(config_list, backup_filename, log)


if __name__ == "__main__":
    main()
