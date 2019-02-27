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


import requests
import random
import time


SLEEP_LOWER_BOUND = 1
SLEEP_UPPER_BOUND = 5
SITELIST_FILE = 'websites.list'
USER_AGENTS_FILE = 'user-agents.list'




class weighted_random_picker(object):
    def __init__(self, weighted_tuples):
        self.__values = []
        self.__index = []
        for value, weight in weighted_tuples:
             self.__values.append(value)
             self.__index.append(float(weight))

    def choice(self):
        random_number = random.random() * sum(self.__index)
        for index_number, weight in enumerate(self.__index):
            random_number -= weight
            if random_number < 0:
                 return self.__values[index_number]


def generate_weighted_tuple_list_from_file(filepath):
    fd = open(filepath, 'r')
    return_list = []
    for line in fd:
        if '>' in line:
            value, weight = line.split('>')
            tup = (value, weight.strip())
            return_list.append(tup)
    return return_list


def generate_request_headers(useragents):
    ua = useragents.choice()
    headers = {'User-Agent' : ua}
    return headers
    
    
def do_nothing(website, headers):
    print "doing nothing"

def browse_website(website, headers):
    try:
        response = requests.get(website, headers=headers)
        print("browsing %s as User-Agent %s" % (website, headers["User-Agent"]))
    except:
        print ("exception")
        return 0
    if len(response.links.keys()) > 0:
        for url_link in response.links.keys():
             url = response.links[url_link]['url']
             if url not in sites:
                 sites.append(url)


if __name__ =="__main__":
    ## read in variables
    sitelist = open(SITELIST_FILE, 'r')
    sites = sitelist.read().split('\n')
    useragents_t = generate_weighted_tuple_list_from_file(USER_AGENTS_FILE)
    useragents_picker = weighted_random_picker(useragents_t)

    weighted_actions = [(browse_website, 90), (do_nothing, 10)]    
    actions = weighted_random_picker(weighted_actions)
    headers = generate_request_headers(useragents_picker) 
    continue_to_act = True
    while continue_to_act is True:
        this_website = random.choice(sites)
        actions.choice()(this_website, headers)
        sleep_length = random.randint(SLEEP_LOWER_BOUND,SLEEP_UPPER_BOUND)
        time.sleep(sleep_length)
