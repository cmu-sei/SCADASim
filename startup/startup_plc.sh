#!/bin/bash

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


# Check whether the template variable is used or not
# template_var would contain the full path of the config file to use
# If used, run master.py with the path supplied as an argument
TEMPLATE_VAR="$(vmtoolsd --cmd 'info-get guestinfo.template_variable')"
if [ "$TEMPLATE_VAR" = "" ]; then
    echo "No template variable found on the vmx file. Using hard-coded value"
    # load in data from master.py using hard-coded config textfile
    result=$(python /usr/local/bin/scadasim_pymodbus_plc/startup/master.py)
else
    # load in data from master.py using template_var as config textfile
    echo "Using template_var from vmx file"
    result=$(python /usr/local/bin/scadasim_pymodbus_plc/startup/master.py $TEMPLATE_VAR)
fi

# master.py will return the number of plc devices for this schema, and the path of the config file
results=( $result )

echo "$results"

# parse results
START=0
END=${results[0]}
name_of_config=${results[1]}

# loop and start plc devices with their ID and the path of the config file supplied as arguments
# run in background as async_plc will start off multiple threads
for (( c=$START; c<$END; c++ ))
do
        echo "Running async_plc.py with arg $c"
	python /usr/local/bin/scadasim_pymodbus_plc/plc/async_plc.py --n $c --c $name_of_config &	
done

# keep script alive so that async_plc programs continue to run
while true; do
    echo
done
