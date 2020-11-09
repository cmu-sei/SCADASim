SCADA Simulator

Copyright 2018 Carnegie Mellon University. All Rights Reserved.

NO WARRANTY. THIS CARNEGIE MELLON UNIVERSITY AND SOFTWARE ENGINEERING INSTITUTE MATERIAL IS FURNISHED ON AN "AS-IS" BASIS. CARNEGIE MELLON UNIVERSITY MAKES NO WARRANTIES OF ANY KIND, EITHER EXPRESSED OR IMPLIED, AS TO ANY MATTER INCLUDING, BUT NOT LIMITED TO, WARRANTY OF FITNESS FOR PURPOSE OR MERCHANTABILITY, EXCLUSIVITY, OR RESULTS OBTAINED FROM USE OF THE MATERIAL. CARNEGIE MELLON UNIVERSITY DOES NOT MAKE ANY WARRANTY OF ANY KIND WITH RESPECT TO FREEDOM FROM PATENT, TRADEMARK, OR COPYRIGHT INFRINGEMENT.

Released under a MIT (SEI)-style license, please see license.txt or contact permission@sei.cmu.edu for full terms.

[DISTRIBUTION STATEMENT A] This material has been approved for public release and unlimited distribution.  Please see Copyright notice for non-US Government use and distribution.
This Software includes and/or makes use of the following Third-Party Software subject to its own license:
1. Packery (https://packery.metafizzy.co/license.html) Copyright 2018 metafizzy.
2. Bootstrap (https://getbootstrap.com/docs/4.0/about/license/) Copyright 2011-2018  Twitter, Inc. and Bootstrap Authors.
3. JIT/Spacetree (https://philogb.github.io/jit/demos.html) Copyright 2013 Sencha Labs.
4. html5shiv (https://github.com/aFarkas/html5shiv/blob/master/MIT%20and%20GPL2%20licenses.md) Copyright 2014 Alexander Farkas.
5. jquery (https://jquery.org/license/) Copyright 2018 jquery foundation.
6. CanvasJS (https://canvasjs.com/license/) Copyright 2018 fenopix.
7. Respond.js (https://github.com/scottjehl/Respond/blob/master/LICENSE-MIT) Copyright 2012 Scott Jehl.
8. Datatables (https://datatables.net/license/) Copyright 2007 SpryMedia.
9. jquery-bridget (https://github.com/desandro/jquery-bridget) Copyright 2018 David DeSandro.
10. Draggabilly (https://draggabilly.desandro.com/) Copyright 2018 David DeSandro.
11. Business Casual Bootstrap Theme (https://startbootstrap.com/template-overviews/business-casual/) Copyright 2013 Blackrock Digital LLC.
12. Glyphicons Fonts (https://www.glyphicons.com/license/) Copyright 2010 - 2018 GLYPHICONS.
13. Bootstrap Toggle (http://www.bootstraptoggle.com/) Copyright 2011-2014 Min Hur, The New York Times.
DM18-1351


# scadasim_pymodbus_plc

## Brief:
- Simulates a SCADA system
- Uses PyModbus to create custom PLC devices
- Simulates Modbus TCP/RTU traffic

## Installation:
Experienced issues installing pymodbus using pip, so instead the github repo was used for pymodbus and pip install for any additional dependencies
- `git clone git://github.com/bashwork/pymodbus.git`
- `cd pymodbus`
- `python setup.py install`
- `pip install twisted cryptography bcrypt pyasn1 service_identity`
    - Note that for the systemd service, you want sudo permissions to be able to start the PyModbus server and do other things. In that case, you probably have two primary options:
        - pip install globally so that root will have access to the required packages (not recommended due to security concerns if there is a bad package)
        - Specify in the systemd service config that you want to use a non-root user to run the program (need to figure out how to get that user the privilege to start running a server and other actions)

## Initial Setup
- You will first want to generate a master config file to customize the functionality of your PLC devices
    - `cd /<scadasim_working_dir>/configs`
    - `python plc_config_gen.py`

- After you have created your master config file, add the full filepath to `config_file_name.txt`

- The filepaths used throughout the project begin with `/usr/local/bin`. To use this with your current working directory, run the following to make a symlink to this project
    - `ln -s <full path to your working directory of this project> /usr/local/bin/scadasim_pymodbus_plc`

- Next, run your async plc server/client
    - `cd /<scadasim_working_dir>/startup`
    - `sudo ./startup_plc.sh`
    - startup_plc.sh has a while loop with an empty echo to be used as a systemd service without ending prematurely. If you wish to run the .sh script manually, remove the loop

- Finally, if you want to use a new config file or start your PLCs from scratch, make sure you clear your backups.
    - `sudo rm /<scadasim_working_dir>/backups/backup_*`

- Follow the README_startup_service.md instructions on setting up the systemd job to avoid manually running ./startup_plc.sh each time.
    - Make sure that the while loop with the empty echo at the end is there if you are setting it up using systemd

## Description:

### Uses:
- Python 2.7.10
- Pymodbus 2.2.0
- twisted 19.7.0
- cryptography 2.7
- bcrypt 3.1.7
- pyasn1 0.4.6

### Project Overview:

#### backups
- contain(s) backup_[n].yaml files - to store up to date values for n PLC devices to be able to restart and not start over again 

#### configs

##### plc_config_gen.py
- This is used to generate a master config file, accomplished by command line questions

##### *_config.yaml
- Master yaml config files to be used in configuring the PLC devices to simulate


#### logging
- contain(s) logging_[n].yaml files - to log based on the logging configuration specified in the currently used master yaml configuration

#### old
- store old files that are not used anymore but good for reference

#### plc

##### async_plc.py
- async_plc.py serves as the main asynchronous Pymodbus server with client functionality

##### datastore.py
- datastore.py has wrapper functions that are used to read from/write to the datastore

##### helper.py
- helper.py has wrapper functions that are used to generate data variance for the plc devices and to reduce code in async_plc.py


#### startup

##### README_startup_service.md
- Read this to get this code working on startup using systemd!

##### config_file_name.txt
- If no config file name is provided using the vmx template_var, it will look for the file name in this text file

##### master.py
- master.py initializes the backup files and returns config information to startup_plc.sh

##### plc_startup_service.servcie
- This is used to run the plc devices on startup
- Refer to the README on adding this to your local systemd

##### startup_plc.sh
- startup_plc.sh serves as the main startup script to initialize the PLC devices based off of the master config file

