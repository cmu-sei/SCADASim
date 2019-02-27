#!/usr/bin/python

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


import subprocess
import random
import collections
import re
number_of_containers = 50


def process_docker_ps_line(line):

   if line == '':
      return None

   container = collections.namedtuple('container', 'c_id, imagename, command, created, status, name, ports')

   c_id = None
   imagename = None
   command = None
   created = None
   status = None
   name = None
   ports = None


   try:
       c_id, imagesname, command, created, status, name = re.split('\s{2,}', line)
   except:
       try:
           c_id, imagename, command, created, status, ports, name = re.split('\s{2,}', line)
       except Exception as e:
           print('still has exception in docker ps -a processing - %s\n line: %s' % (e, line))
           return None



   if name == "registry" or name == "registry:2":
       return None
   this_container = container(c_id=c_id, imagename=imagename, command=command, created=created, status=status, name=name, ports=ports)
   return this_container



def generate_network_list():
    networks_output = subprocess.check_output(["docker", "network", "ls"])
    split_output = networks_output.split('\n')
    networks = []
    for line in split_output[1:]:
        if line:
            dockerid, name, driver = line.split()
            if driver == 'bridge' and name != 'bridge':
                networks.append(name)
    return networks


def get_existing_containers():
    containers = []
    ps_output = subprocess.check_output(["docker", "ps", "-a"])
    ps_split = ps_output.split('\n')
    for line in ps_split[1:]:

        this = process_docker_ps_line(line)
        if this is not None:
            containers.append(this)
    return containers

def get_highest_container_number(prefix):

    containers = get_existing_containers()
    if not containers:
        return 0
    if isinstance(containers, list):
                
        sorted_list_of_numbers = sorted(map(lambda x: int(re.findall('\d+', x.name)[0]), containers))
        highest = int(sorted_list_of_numbers.pop())
        #print(sorted_list_of_numbers) 
        return highest
    else:
        
        return 1

    
    

if __name__ == '__main__':

    networks = generate_network_list()
    start_number = get_highest_container_number('raindrop')
    for number in xrange(start_number + 1, start_number + number_of_containers + 1):
        this_network = random.choice(networks)
        this_name = "raindrop" + str(number)
        print("spawning %s" % this_name) 
        this_output = subprocess.check_output(["docker", "run", "--dns=67.215.0.5", "--name", "%s" % this_name, "--net", "%s" % this_network, "-d", "raindrop"])
        #print(this_output)


