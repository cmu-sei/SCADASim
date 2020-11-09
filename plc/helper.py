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
Helper functions AND functions to be used for register behavior.

(Reg behavior) Functions to be used to generate data variance for the plc devices.

These functions accept:
    minimum value
    maximom value
    slave context

These functions return:
    a set of values to be written to the slave context
'''
import sys, logging, yaml
from os import path
from threading import Thread
from time import *
from random import *
from datastore import *
from pymodbus.transaction import (ModbusRtuFramer,
                                  ModbusAsciiFramer,
                                  ModbusBinaryFramer)

'''
linear() will update registers/coils in a linear function
- It will continue to run until it receives 'ctrl+c' KeyboardInterrupt
'''

def linear(variance, time, address, slave_id, count, context, log, my_backup): 
    try:
        while(True):
            sleep(time)
            values = read_hr_register(context[0], slave_id, address, count)
            values = [v + variance for v in values]
            write_hr_register(context[0], slave_id, address, values)
            log.debug(values)
    except:
        sys.exit()

'''
linear_coil_dependent() will update registers/coils in a linear function until it reaches the max value specified
- Currently will not decrement if it will fall below 0
- Also will not increment if it goes past max
- It will continue to run until it receives 'ctrl+c' KeyboardInterrupt
- If the coil matches what the default_coil_value is, it will continue to add variance to the holding register normally
- Otherwise, it will negate the variance and add it to the holding register
- The holding register will be checked every 'time' seconds
'''
def linear_coil_dependent(variance, max, time, address, slave_id, count, context, log, my_backup, coil_address, default_coil_value):
    try:
        while(True):
            sleep(time)
            coil_reg = read_co_register(context[0], slave_id, coil_address, 1)
            # the datastore helper functions return a list, even if it is just one register being read
            coil_reg = coil_reg[0]
            # check the state of the coil
            if coil_reg == "false" or int(coil_reg) == 0:
                coil_val = 0
            elif coil_reg == "true" or int(coil_reg) == 1:
                coil_val = 1
            # compare the current state of the coil to the default coil value
            if coil_val == int(default_coil_value):
                values = read_hr_register(context[0], slave_id, address, count)
                # check to see if exceeded max value
                if(values[0] >= max):
                    values[0] = max
                else:
                    values[0] = values[0] + variance
                # values = [v + variance for v in values]
                write_hr_register(context[0], slave_id, address, values)
                log.debug(values)
            else: # not default coil value - negate variance and add it to holding register in order to do opposite behavior
                values = read_hr_register(context[0], slave_id, address, count)
                all_greaterthan_0 = True
                for v in values:
                    if v <= 0:
                        all_greaterthan_0 = False
                values = [v + (variance*-1) for v in values]
                if all_greaterthan_0:
                    write_hr_register(context[0], slave_id, address, values)
                log.debug(values)
    except:
        sys.exit()

'''
random_num() will update the registers/coils randomly
- Will only generate random values between 'min' and 'max'
- It will continue to run until it receives 'ctr+c' KeyboardInterrupt 
'''
def random_num(min, max, time, address, slave_id, count, context, log, my_backup):
    try:
        while(True):
            sleep(time)
            values = read_hr_register(context[0], slave_id, address, count)
            variance = randint(min, max)
            values = [(v*0) + variance for v in values]
            write_hr_register(context[0], slave_id, address, values)
            log.debug(values)
    except:
        sys.exit()

'''
random_coil_dependent() will update registers/coils in a linear function until it reaches the max value specified, then it will begin random data variance
- It will continue to run until it receives 'ctr+c' KeyboardInterrupt
'''
def random_coil_dependent(variance, max, rand_min, rand_max, time, address, slave_id, count, context, log, my_backup, coil_address, default_coil_value):
    try:
	# false until max is reached
	at_max = False
        while(True):
            sleep(time)
            coil_reg = read_co_register(context[0], slave_id, coil_address, 1)
            # the datastore helper functions return a list, even if it is just one register being read
            coil_reg = coil_reg[0]
	    values = read_hr_register(context[0], slave_id, address, count)
	    # checking to see if max value was reached to begin random data variance
	    if(values[0] >= max):
	        at_max = True
            # check the state of the coil
            if coil_reg == "false" or int(coil_reg) == 0:
                coil_val = 0
            elif coil_reg == "true" or int(coil_reg) == 1:
                coil_val = 1
            # compare the current state of the coil to the default coil value
            if coil_val == int(default_coil_value):
                # if at max select random int
		if(at_max == True):
		    values[0] = randint(rand_min, rand_max)
		# check to see if exceeded max                
		elif(values[0] >= max):
                    values[0] = max
                else:
                    values[0] = values[0] + variance
                # values = [v + variance for v in values]
                write_hr_register(context[0], slave_id, address, values)
                log.debug(values)
            else: # not default coil value - negate variance and add it to holding register in order to do opposite behavior
                values = read_hr_register(context[0], slave_id, address, count)
                all_greaterthan_0 = True
                for v in values:
                    if v <= 0:
                        all_greaterthan_0 = False
                if all_greaterthan_0:
		    # no longer at max value, do not do random variance
		    at_max = False
		    values = [v + (variance*-1) for v in values]
		    if(values[0] < 0):
		        values[0] = 0
                    write_hr_register(context[0], slave_id, address, values)
                log.debug(values)
    except:
        sys.exit()

'''
constant_num() will update the registers/coils with a constant value
- Will generate constant value to coil register
- It will continue to run until it receives 'ctr+c' KeyboardInterrupt
'''
def constant_num(num, time, address, slave_id, count, context, log, my_backup):
    try:
        while(True):
            sleep(time)
            values = read_co_register(context[0], slave_id, address, count)
            variance = num
            values = [(v*0) + variance for v in values]
            write_co_register(context[0], slave_id, address, values)
            log.debug(values)
    except:
        sys.exit()
        
def fuel_tank_behavior(min, max, time, address, slave_id, count, context, log, my_backup, coil_address):
    print( "Thread started for fuel_tank_behavior" )
    try:
        while True:
            for i in range(0, 2):
                # decrement behavior - decrement tank by 25% about every 15 min
                # open coil
                coil_values = read_co_register(context[0], slave_id, coil_address, 1)
                coil_values = [1 for v in coil_values]
                write_co_register(context[0], slave_id, address, coil_values)
                for j in range(0, 25): # take 25 seconds to decrement fuel tank level by 25%
                    values = read_hr_register(context[0], slave_id, address, count)
                    for v in values:
                        if v > min:
                            values = [(v-1) for v in values]
                    write_hr_register(context[0], slave_id, address, values)
                    log.debug(values)
                    sleep(1)

                # close coil
                coil_values = read_co_register(context[0], slave_id, coil_address, 1)
                coil_values = [0 for v in coil_values]
                write_co_register(context[0], slave_id, address, coil_values)

                sleep_val = 875
		# sleep for about 15 minutes, depending on whether we decremented or also incremented
                sleep(sleep_val)
                # increment behavior - refill tank to 100% about every hour
                if i == 1:
                    # open coil
                    log.debug("Increment behavior entered\n")
                    coil_values = read_co_register(context[0], slave_id, coil_address, 1)
                    coil_values = [1 for v in coil_values]
                    write_co_register(context[0], slave_id, address, coil_values)

                    for k in range(0, 100): # take 100 seconds to refill fuel tank back to 100
                        values = read_hr_register(context[0], slave_id, address, count)
                        for v in values:
                            if v < max:
                                values = [(v+1) for v in values]
                        write_hr_register(context[0], slave_id, address, values)
                        log.debug(values)
                        sleep(1)

                    # close coil
                    coil_values = read_co_register(context[0], slave_id, coil_address, 1)
                    coil_values = [0 for v in coil_values]
                    write_co_register(context[0], slave_id, address, coil_values)

                    sleep_val = 775
		    sleep(900)            
    except:
        sys.exit()


""" 
A worker process that runs every so often and
updates live values of the context. It should be noted
that there is a race condition for the update.

:param arguments: The input arguments to the call
"""

'''
updating_writer parses the DATASTORE section of the config for the calling PLC device
  to start threads for each holding register based on the type of behavior and the parameters
  specified
- Currently designed to have one thread per holding register
- Currently does not handle 'di' or 'ir' register types
'''
def updating_writer(context, config_list, time, log, backup_filename):
    # load in config list to generate thread behavior
    values = config_list['DATASTORE']['hr']['values']
    size = len(values)
    i = 0
    # loop through each holding register
    while(i < size):
        log.debug("updating the context")
        name = 'behavior_' + str(i + 1)
        slave_id = 0x00
        time = config_list['DATASTORE']['hr'][name]['time']
        address = config_list['DATASTORE']['hr'][name]['address']
        count = config_list['DATASTORE']['hr'][name]['count']
        target = ''
        args = ()

        # check to see what behavior to use
        if (config_list['DATASTORE']['hr'][name]['type'] == 'linear'):
            # collect values from master config
            variance = config_list['DATASTORE']['hr'][name]['variance']
            target = linear
            args = (variance, time, address, slave_id, count, context, log, backup_filename)

        elif (config_list['DATASTORE']['hr'][name]['type'] == 'linear_coil_dependent'):
            variance = config_list['DATASTORE']['hr'][name]['variance']
            coil_address = config_list['DATASTORE']['hr'][name]['coil_address']
            default_coil_value = config_list['DATASTORE']['hr'][name]['default_coil_value']
            maximum = config_list['DATASTORE']['hr'][name]['max']
            target = linear_coil_dependent
            args = (variance, maximum, time, address, slave_id, count, context, log, backup_filename, coil_address, default_coil_value)

        elif (config_list['DATASTORE']['hr'][name]['type'] == 'random'):
            # collect values from master config
            minimum = config_list['DATASTORE']['hr'][name]['min']
            maximum = config_list['DATASTORE']['hr'][name]['max']
            target = random_num
            args = (minimum, maximum, time, address, slave_id, count, context, log, backup_filename)
        
        elif (config_list['DATASTORE']['hr'][name]['type'] == 'random_coil_dependent'):
            variance = config_list['DATASTORE']['hr'][name]['variance']
            coil_address = config_list['DATASTORE']['hr'][name]['coil_address']
            default_coil_value = config_list['DATASTORE']['hr'][name]['default_coil_value']
            maximum = config_list['DATASTORE']['hr'][name]['max']
            rand_min = config_list['DATASTORE']['hr'][name]['rand_min']
            rand_max = config_list['DATASTORE']['hr'][name]['rand_max']
            target = random_coil_dependent
            args = (variance, maximum, rand_min, rand_max, time, address, slave_id, count, context, log, backup_filename, coil_address, default_coil_value)

        elif (config_list['DATASTORE']['hr'][name]['type'] == 'fuel_tank_behavior'):
            print( "successfully found fuel_tank_behavior" )
            minimum = config_list['DATASTORE']['hr'][name]['min']
            maximum = config_list['DATASTORE']['hr'][name]['max']
            coil_address = config_list['DATASTORE']['hr'][name]['coil_address']
            target = fuel_tank_behavior
            args = (minimum, maximum, time, address, slave_id, count, context, log, backup_filename, coil_address)


        # start thread
        thread = Thread(target=target, args=args)
        thread.daemon = True
        thread.start()

        # iterate to next thread
        i = i + 1

    # load in config list to generate thread behavior for coil registers
    co_values = config_list['DATASTORE']['co']['values']
    co_size = len(co_values)
    is_behavior = False	# Allow for us to add behaviors only for some coil registers if we want to
    j = 0
    while(j < co_size):
        log.debug("updating the context")
        name = 'behavior_' + str(j + 1)
        slave_id = 0x00
        # Moved time/address/count collection to if logic for constant
        # If we add more behaviors in the future for coils, can move it back up here and add logic
        # to check that behavior_N['type'] != 'none' before getting time/address/count values
        target = ''
        args = ()

        # check to see what behavior to use. If it does not match any, don't start a thread
        if (config_list['DATASTORE']['co'][name]['type'] == 'constant'):
            # collect values from master config
            time = config_list['DATASTORE']['co'][name]['time']
            address = config_list['DATASTORE']['co'][name]['address']
            count = config_list['DATASTORE']['co'][name]['count']
            num = config_list['DATASTORE']['co'][name]['num']
            target = constant_num
            args = (num, time, address, slave_id, count, context, log, backup_filename)
            is_behavior = True
        else:
            # invalid type name or no behavior
            is_behavior = False

        # start thread if it is a valid behavior
        if is_behavior:
            thread = Thread(target=target, args=args)
            thread.daemon = True
            thread.start()

        # iterate to the next coil register to check for behavior
        j = j + 1

'''
- @brief datastore_backup_on_start will run before the datablock/slave/server contexts are set up in order to start the server with the last known good state of the server context
- It updates the local datastore_config object with the corresponding values in backup_filename
- and then exits
'''
def datastore_backup_on_start(my_backup):
    if (path.exists(my_backup) == False or path.getsize(my_backup) == 0):
        return -1
    backup = open(my_backup, 'r')
    backup_file = yaml.safe_load(backup)
    backup.close()
    
    return backup_file['DATASTORE']

'''
- @brief datastore_backup_to_yaml will run continuously to READ from the context to update the entries in the datastore backup file in YAML format
- It should be run from async_plc.py as a thread to continuously run
- It should start running before the other threads (for register behavior) starts running, but after the datastore context has been setup
'''
def datastore_backup_to_yaml(context, my_backup):
    backup = open(my_backup, 'r')
    backup_file = yaml.safe_load(backup)
    backup.close()
    yaml_file = ''
    num_of_co = len(backup_file['DATASTORE']['co']['values'])
    num_of_di = len(backup_file['DATASTORE']['di']['values'])
    num_of_hr = len(backup_file['DATASTORE']['hr']['values'])
    num_of_ir = len(backup_file['DATASTORE']['ir']['values'])
    try:
        while(True):
            # Eventually change sleep value to a parameter - there are issues with the backup file if there is no sleep at all
            sleep(1)
            values = read_co_register(context[0], 0x00, 0x00, num_of_co)
            backup_file['DATASTORE']['co']['values'] = values
            values = read_di_register(context[0], 0x00, 0x00, num_of_di)
            backup_file['DATASTORE']['di']['values'] = values
            values = read_hr_register(context[0], 0x00, 0x00, num_of_hr)
            backup_file['DATASTORE']['hr']['values'] = values
            values = read_ir_register(context[0], 0x00, 0x00, num_of_ir)
            backup_file['DATASTORE']['ir']['values'] = values
            
            yaml_file = open(my_backup, 'w')
            yaml.dump(backup_file, yaml_file, default_flow_style=False)
            yaml_file.close()
    except:
        if(yaml_file.closed == False):
            yaml_file.close()
        sys.exit()

'''
Used to configure logging and clean up the code in async_plc.py
'''
def configure_logging_level(logging_level, log):
    # Expand on this logic
    if logging_level == 'CRITICAL':
        log.setLevel(logging.CRITICAL)
    elif logging_level == 'ERROR':
        log.setLevel(logging.ERROR)
    elif logging_level == 'WARNING':
        log.setLevel(logging.WARNING)
    elif logging_level == 'INFO':
        log.setLevel(logging.INFO)
    elif logging_level == 'DEBUG':
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.NOTSET)

'''
Used to configure the framer and clean up the code in async_plc.py
'''

def configure_server_framer(server_config):
    framer = None
    if server_config['type'] == 'tcp':
        # check framer to be rtu or none
        if server_config['framer'] == 'RTU':
            framer = ModbusRtuFramer
    elif server_config['type'] == 'serial':
        # framer can be rtu, ascii, or binary
        if server_config['framer'] == 'RTU':
            framer = ModbusRtuFramer
        elif server_config['framer'] == 'ASCII':
            framer = ModbusAsciiFramer
        elif server_config['framer'] == 'BINARY':
            framer = ModbusBinaryFramer
    return framer
