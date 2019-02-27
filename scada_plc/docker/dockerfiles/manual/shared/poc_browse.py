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
import os
import re

### user defined variables
SLEEP_LOWER_BOUND = 15
SLEEP_UPPER_BOUND = 200
SITELIST_FILE = 'websites.list'
#SITELIST_WEBSITE = 'http://43.105.98.110/sites/websites.txt'
USER_AGENTS_FILE = 'user-agents.list'
VISIT_LINKS_UPPER = 10
VISIT_LINKS_LOWER = 1
PING_THIS = "67.215.0.5"
SOURCE_CHAR_DIVIDER = 100000
MAX_BROWSE_TIME = 20
POST_STRINGS_FILE = 'post-strings.list'


###


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


def decide_how_many_links_to_visit():
    links_to_click = random.randint(VISIT_LINKS_LOWER, VISIT_LINKS_UPPER)
    return links_to_click

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

def sleep_while_browsing(pagesource):
    if len(pagesource) > 1:
        sleep_for_this_long = len(pagesource) / SOURCE_CHAR_DIVIDER
        if sleep_for_this_long > MAX_BROWSE_TIME:
            sleep_for_this_long = MAX_BROWSE_TIME / random.randint(1,5)
        time.sleep(sleep_for_this_long)


def post_website(website, headers):
    ses = requests.session()
    if website.endswith('/'):
        this_website = website
    else:
        this_website = website + '/'
    post_suffix = post_strings_picker.choice()
    data = {'form' : 'value'}
    print("posting %s as User-Agent %s" % (this_website + post_suffix, headers['User-Agent']))
    try:
        r = ses.post(this_website + post_suffix, headers=headers, data=data, verify=False)
    except:
        print("post failed to %s" % (this_website + post_suffix))
   

def browse_website(website, headers):
    linkre = re.compile('<a\s*href=[\'|"](.*?)[\'"].*?>')
    httpre = re.compile("\w+/\w+.*|http.*")
    try:
        ses = requests.session()
        response = ses.get(website, headers=headers, verify=False)
        print("browsing %s as User-Agent %s" % (website, headers["User-Agent"]))
    except:
        print ("exception, get failed to %s" % website)
        return 0
    these_links = []
     
    links = re.findall(linkre, response.text)
    flinks = map( lambda x: re.findall(httpre, x), links)
    these_links += [item[0] for item in flinks if item]
    
    if these_links and len(these_links) > VISIT_LINKS_LOWER:
        links_visited = 0
        link_count = decide_how_many_links_to_visit()
        keep_visiting = True
        while keep_visiting is True and links_visited < link_count:
            try:
                this_website = random.choice(these_links)
                if this_website.startswith("htt"):
                    print("browsing %s as User-Agent %s" % (this_website, headers["User-Agent"]))
                    response = ses.get(this_website, headers=headers, verify=False)
                    links_visited += 1
                    sleep_while_browsing(response.text)
                else:
                    this_website = website + this_website
                    print("browsing %s as User-Agent %s" % (this_website, headers["User-Agent"]))
                    response = ses.get(this_website, headers=headers, verify=False)
                    links_visited += 1
                    sleep_while_browsing(response.text)
            except:
                keep_visiting = False

#routing issue talking back to host, didn't look into yet, need to fix, using file for now
def generate_site_list(SITELIST_WEBSITE):
    response = requests.get(SITELIST_WEBSITE)
    raw_sites = response.text.encode('utf-8').split('\n')
    sites = [item for item in raw_sites if item]
    return sites



if __name__ =="__main__":
    ## read in variables
    sitelist = open(SITELIST_FILE, 'r')
    raw_sites = sitelist.read().split('\n')
    sites = [item for item in raw_sites if item]

    ping_interface = os.system("ping -c 40 " + PING_THIS + " > /dev/null 2>&1")   

    #sites = generate_site_list(SITELIST_WEBSITE)
    useragents_t = generate_weighted_tuple_list_from_file(USER_AGENTS_FILE)
    useragents_picker = weighted_random_picker(useragents_t)
    post_strings_t = generate_weighted_tuple_list_from_file(POST_STRINGS_FILE)
    post_strings_picker = weighted_random_picker(post_strings_t)

    ping_interface = os.system("ping -c 40 " + PING_THIS + " > /dev/null 2>&1")

    weighted_actions = [(browse_website, 80), (do_nothing, 5), (post_website, 15)]    
    actions = weighted_random_picker(weighted_actions)
    headers = generate_request_headers(useragents_picker) 
    continue_to_act = True
    while continue_to_act is True:
        sleep_length = random.randint(SLEEP_LOWER_BOUND,SLEEP_UPPER_BOUND)
        time.sleep(sleep_length)
        this_website = random.choice(sites)
        actions.choice()(this_website, headers)
