# JA SCADA Production Representation - JASPR

## Security Testing and Training

SCADA sensor networks is an industry wide problem in securuing an originization's network. Programmable Logic Controllers(PLC) are lightweight causing the difficulty to withstand additional layers of security. This causes communications between PLC and Human-Managment Interfaces (HMI) to be unencrypted, simple, and with little to no authentication. Further more cyber security professionals rarely have the ability to interact and identify SCADA traffic. This applications using pymodbus allow individuals the opertunity to view Modbus traffic, by allowing orginizations to train on identifing malicous traffic amoung standard traffic. JASPR fully encompasses a basic SCADA network and allows 1 to N PLC devices attached to HMIs all feading to a central Historian. With the use of a simple json configuration file orginizations can make as simple or as complex a sensor network in order to drive training to fullfill the desired objectives.

## Getting Started
The following is a tutorial to deploy JASPR from a non-configured machine. If all systems are configured correctly skip to step 4
#<center> Table of Contents</center>
1. [Pull JASPR code](#Pull-JASPR-Source-Code)
2. [Install Dependencies](#Install-Dependencies)
3. [Setup Postgres DB](#Setup-Postgres-DB-for-Deployment)
4. [Initilize JASPR](#Initilize-JASPR)
5. [Local Deployment](#Local-Deployment)
6. [Historian Deployment](#Historian-Deployment)
7. [HMI Deployment](#HMI-Deployment)
8. [PLC Box Deployment](#PLC-Box-Deployment)
9. [Configuration file format](#Configuration-file-format)
10. [Install and Configure Docker](#Install-and-Configure-Docker)

## 1. <a name="Pull-JASPR-Source-Code"></a>Pull JASPR Source Code
```bash
$ git clone https://gitlab.sky.cert.org/jacklin/JASPR.git
$ cd JASPR
```
## 2. <a name="Install-Dependencies"></a>Install Dependencies
```bash
$ yum - $ xargs yum -y install < yum_requirements.txt # Centos
$ apt-get - $ xargs apt-get-y install < yum_requirements.txt # Ubuntu
$ yum group install "Development Tools"
$ python ./get-pip.py
$ pip install -r requirements.txt
```
## 3. <a name="Setup-Postgres-DB-for-Deployment"></a>Setup Postgres DB for Deployment
```bash
$ sudo -i -u postgres
$ createuser  -s -W <db-username>
$ createdb --owner <db-username> <database-name>
$ exit
$ systemctl start postgresql && systemctl enable postgresql
```
(for help with setting up postgres the following link is a great resource https://www.digitalocean.com/community/tags/postgresql?type=tutorials)
## 4. <a name="Initialize-JASPR"></a>Initialize JASPR
[Please see the configurations section for proper configurations json file.](#Configuration-file-format)
```bash
$ python ./init.py --help # Help CLI arguments
$ python ./init.py -f path/to/config.json -u <db-username> -d <db-name> -w <db-password> # Local
$ python ./init.py -s -f path/to/config.json -u <db-username> -d <db-name> -w <db-password> # Distrobuted
```
Troubleshoot 1: Make sure if you have a distributed SCADA network that you can connect to HMIs defined in the configuration file.

Troubleshoot 2: Ensure the postgres service is on and the pg_hba.conf file allows for users to connect remotely to the defined HMIs.
## 5. <a name="Local-Deployment"></a>Local Deployment - Open three terminals and navigate to JASPR home directory
<center>**Data Server - Terminal 1**</center>
```bash
$ python ./dataserver.py --help # Help CLI arguments
$ python ./dataserver.py -u <db-username> -d <db-name> -w <db-password>
```
Open browser and go to http://localhost:5000

Troubleshoot 1: Default port is port 5000 ensure that the firewall allows communication over port 5000.

<center>**HMI Server - Terminal 2**</center>
```bash
$ python ./HMI_Server.py --help # Help CLI arguments
$ python ./HMI_Server.py -p 5001 -u <db-username> -d <db-name> -w <db-password>
```
Troubleshoot 1: Ensure that the Data Server is started and currently running.

Troubleshoot 2: Ensure firewall allows communication over port 5001 local

<center>**PLC Engine - Terminal 3**</center>
```bash
$ python ./PLC_manager.py --help # Help CLI arguments
$ python ./PLC_manager.py -f path/to/config.json
```
Troubleshoot 1: Ensure that the Data Server is started and currently running.

Troubleshoot 2: Ensure firewall allows communication over port 5001 local.

## 6. <a name="Historian-Deployment"></a>Historian Deployment - Only the Data Server is required for the historian

<center>**Data Server - Terminal 1**</center>
```bash
$ python ./dataserver.py --help # Help CLI arguments
$ python ./dataserver.py -i <host-ip> -p <host-port> -u <db-username> -d <db-name> -w <db-password>
```
Troubleshoot 1: Ensure that the firewall allows communication over the defined port. If the port number is low then sudo may be required.
## 7. <a name="HMI-Deployment"></a>HMI Deployment - Open two terminals and navigate to JASPR home directory.

<center>**Data Server - Terminal 1**</center>
```bash
$ python ./dataserver.py --help # Help CLI arguments
$ python ./dataserver.py -i <host-ip> -p <host-port> -u <db-username> -d <db-name> -w <db-password>
```
Troubleshoot 1: Ensure that the firewall allows communication over the defined port. If the port number is low then sudo may be required.
<center>**7b. HMI Server - Terminal 2**</center>
```bash
$ python ./HMI_Server.py --help # Help CLI arguments
$ python ./HMI_Server.py -i <host-ip> -p <host-port> -u <db-username> -d <db-name> -w <db-password>
```
Troubleshoot 1: Ensure that the Data Server is started and currently running.

Troubleshoot 2: Ensure that the firewall allows communication over the defined port. If the port number is low then sudo may be required.

## 8. <a name="PLC-Box-Deployment"></a>PLC Box Deployment
This requires docker with an image that supports pymodbus module see [PLC Box configurations](#Install-and-Configure-Docker) section, and in this section it is assumed that you have properly configured PLC Box and the docker image contains the arduino.py engine
``` bash
$ python ./PLC_engine.py --help - For CLI arguments
$ python ./PLC_engine.py -H http://<host-ip>:<host-port>/api/modbus-config
```

## 9. <a name="Configuration-File-Standard"></a>Configuration File Standard
* 9a. JASPR simulates a SCADA System that has three unique parts: Histoian, HMI, and PLC device. The Historian is the central repository for all of the Human-Managment Interfaces. The Historian poles the HMIs to gather a historiacal picture of what the HMIs are seeing. The default poling interval is 30 seconds, if the poling interval should be larger or shorter then the sleep time in HMI_Server.py/historina_handler can be changed up or down. The HMIs are a real time view of the PLC devices readings. This allows users to identify real time issues associated with each individual PLC devices. The HMI unlike the Historian only maintains records of the last 1000 readings pulled from the PLC devices. Finally the PLC devices are modled off of the arduino controller archetecture. Each ardunino has its own unique IP address and allows two way communication. These modules are comprised of actuators and sensors with the actuators having direct relationship with the sesnors, meaning if a heater actuator is turned up the temperture sensor will start rising in value. The next couple of sections will walk you through how to properly configure the json configuration file in order to correctly map your SCADA System.
* **9b. Historian**
   * 9b.1 The required keys are: name_system, name, location, actuators, and sub_devices. The default IP address is 127.0.0.1 and listening port is 5020
   * 9b.2 Sub Devices are HMIs or Controllers(PLC Device) the Historian cannot have any controller devices and must have atleaset one HMI
   * 9b.3 The "Status" Actuator is required for all devices this allows users to turn on and off services that the device provides as well as all services dependant on the device ex: if the Historian is disabled then all HMIs will be disabled and all PLC devices relying on the HMI.
   * 9b.4 The Historian only has one Actuator and cannot have any additional sensors or actuators.
   * 9b.5 Below is an example of the Hisorian Configuration:

<center>**Example Historian Configuration**</center>
```json
{
    "Historian": {
        "name_system": <SCADA SYSTEM NAME>,
        "name": <Historian NAME>,
        "location": <Location>,
        "device_type": "Historian",
        "host_ip" : "1.2.3.4",
        "port" : 5020,
        "actuators": {
            "Status": {
                "type": "enabled",
                "initial_value": 1
                }
        },
        "sub_devices" : {}
}
```

* **9c. HMI**
   * 9c.1 The required keys are: name_system, name, location, actuators, and sub_devices. The default Host and HMI IP address is 127.0.0.1 and listening port for the host is 5020 and HMI is 5021
   * 9c.2 The Host IP address is the web page front end for the HMI while the HMI IP address is the interface communicating with the PLC devices
   * 9c.3 The HMI only has one Actuator and cannot have any additional sensors or actuators.
   * 9c.4 The HMI Identifier is a unique string that identifies the HMI. This is what will be used to bind PLC devices to the HMI and can be any unique string

<center>**Example HMI Configuration**</center>
```json
<HMI Identifier> : {
    "name_system": <HMI System Name>,
    "name": <HMI Name>,
    "location": <Location>,
    "device_type": "Human-Machine Interface",
    "host_ip" : <Host IP Address>,
    "hmi_ip" : <HMI IP Address>,
    "interface" : <Interface Name>,
    "actuators": {
        "Status": {
            "type": "enabled",
            "initial_value": 1
        }
    },
    "sensors": {},
    "sub_devices": {}
}
```
* **9d. Controller**
   * 9d.1 The required keys are: name_system, name, location, and sub_devices.
   * 9d.2 The IP address will be assigned during the initilization phase of deployment
   * 9d.3 The controller can have as many actuators and sensors necessary but, must have atleaset one actuator or sensor.
   * 9d.4 The PLC Identifier is a unique string that identifies the HMI. This is what will be used to bind PLC devices to the HMI and can be any unique string

<center>**Example Controller Configuration**</center>
```json
<PLC Identifier> : {
    "name_system": <PLC System Name>,
    "name": <PLC Name>,
    "location": <Location>,
    "device_type": "Controller",
    "actuators": {},
    "sensors": {},
    "sub_devices": {}
}
```
* **9e. Sensor**
   * 9e.1 The required keys are: type, units, initial_value, and variability.
   * 9e.2 The variability is the how far +- the sensor readings will flucuate from the current_value
   * 9e.3 The valid types are: "locked", "enabled", "open", "temperature", "pressure", "humidity", "flow", "live-stream", "speed", "rotation", "power", "motion"
   * 9e.4 The threshold is optional if not defined the PLC will only fail if the controller tells it to fail. Otherwise the Sensors Controller will fail/shutoff if the sensor reads below the min or above the max

<center>**Example Sensor Configuration**</center>
```json
<Sensor Identifier>: {
    "type": <PLC Type>,
    "units": <Unit of Measure>,
    "initial_value": <Initial Value>,
    "variability": <Variability>,
    "threshold": [<Min>,<Max>]
}
```
* **9f. Actuator**
   * 9f.1 The required keys are: type, and initial_value.
   * 9f.2 The relationship can be as follows: positive - The value increases, negative - The value decreases, and variable - The value can both increase or decrease according to the current value (0 OFF 1 Decrease 2 Maintian 3 Increase)
   * 9f.3 The valid types are: "locked", "enabled", "live-stream", "variable", "relational" with locked, enabled and live-stream will have sensors the reflect the actuator current value
   * 9f.4 Type with Variable will have a relationship of positive or negative while relational will have a relationship of variable
   * 9f.5 The master field must have the sensor identifier of which sensor that will reflect the changes spawned from the actuator

<center>**Example Actuator Configuration**</center>
```json
<Actuaror Identifier>: {
    "type": <PLC Type>,
    "initial_value": <Initial Value>,
    "master" : <Sensor Identifier>,
    "relationship": <Relationship Type>
}
```
* **9e. Complete Example:**

<center>**Example**</center>
```json
{
  "Historian": {
    "name_system": "SCADA System",
    "name": "Historian",
    "location": "Building A",
    "device_type": "Historian",
    "host_ip" : "1.2.3.4",
    "port" : 5020,
    "actuators": {
          "Status": {
            "type": "enabled",
            "initial_value": 1
          }
        },
    "sensors": {},
    "sub_devices" : {
        "AC" : {
            "name_system": "AC System",
            "name": "AC",
            "location": "AV Location",
            "device_type": "Human-Machine Interface",
            "host_ip" : "1.2.3.5",
            "hmi_ip" : "1.2.4.4",
            "interface" : "eth0",
            "actuators": {
                "Status" : {
                    "type": "enabled",
                    "initial_value": 1
                }
            },
            "sensors": {},
            "sub_devices": {
                "Temp" : {
                    "name_system": "Temperature System",
                    "name": "Temperature",
                    "location": "Temp Location",
                    "device_type": "Controller",
                    "actuators": {
                        "status" : {
                            "type": "enabled",
                            "initial_value": 1
                        },
                        "Heater" : {
                            "type": "relational",
                            "initial_value": 0,
                            "relationship": "POSITIVE",
                            "master": "Facility Temperature"
                        },
                        "Air" : {
                            "type": "relational",
                            "initial_value": 0,
                            "relationship": "NEGATIVE",
                            "master": "Facility Temperature"
                        }
                    },
                    "sensors": {
                        "Facility Temperature" : {
                            "name": "Facility Temp",
                            "type": "temperature",
                            "units": "F",
                            "initial_value": 68,
                            "variability": 2,
                            "threshold": [0,210]
                        }
                    },
                    "sub_devices": {}
                },
                "Gen" : {
                    "name_system": "Power System",
                    "name": "power",
                    "location": "Generator Control Console",
                    "device_type": "Controller",
                    "actuators": {
                        "Primary Generator Control": {
                            "type": "variable",
                            "initial_value": 2,
                            "master" : "Generator Load Reading",
                            "relationship": "variable"
                        }
                    },
                    "sensors": {
                        "Generator Load Reading": {
                            "type": "power",
                            "units": "kW",
                            "initial_value": 5000,
                            "variability": 150,
                            "threshold": [0,10000]
                        }
                    },
                    "sub_devices": {}
                    }
                }
            }
        }
    }
}
```

## 10. <a name="Install and Configure Docker"></a>Install and Configure Docker
To install Docker on your PLC Box follow the instructions in the following Link: https://docs.docker.com/engine/installation/, however this guide will be going over how to install on a CentOS 5 or above.
<center>**Download and Install Docker (you must be in the JASPR home directory)**</center>
```bash
$ cp ./docker.repo /etc/yum.repos.d
$ sudo yum update && sudo yum install docker-engine
$ sudo systemctl enable docker.service
$ sudo systemctl start docker.service
```

<center>**Prepare docker image for ardunio engine**</center>
```bash
```

## Application Author

CERT at SEI, Cyber Workforce Development
Written by Joshua Acklin <jacklin@sei.cmu.edu>

## Copyright and License
Copyright 2016, Software Engineering Institute

Revised Version: November 2016
