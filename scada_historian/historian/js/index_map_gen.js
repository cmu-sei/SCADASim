// SCADA Simulator
//
// Copyright 2018 Carnegie Mellon University. All Rights Reserved.
//
// NO WARRANTY. THIS CARNEGIE MELLON UNIVERSITY AND SOFTWARE ENGINEERING INSTITUTE MATERIAL IS FURNISHED ON AN "AS-IS" BASIS. CARNEGIE MELLON UNIVERSITY MAKES NO WARRANTIES OF ANY KIND, EITHER EXPRESSED OR IMPLIED, AS TO ANY MATTER INCLUDING, BUT NOT LIMITED TO, WARRANTY OF FITNESS FOR PURPOSE OR MERCHANTABILITY, EXCLUSIVITY, OR RESULTS OBTAINED FROM USE OF THE MATERIAL. CARNEGIE MELLON UNIVERSITY DOES NOT MAKE ANY WARRANTY OF ANY KIND WITH RESPECT TO FREEDOM FROM PATENT, TRADEMARK, OR COPYRIGHT INFRINGEMENT.
//
// Released under a MIT (SEI)-style license, please see license.txt or contact permission@sei.cmu.edu for full terms.
//
// [DISTRIBUTION STATEMENT A] This material has been approved for public release and unlimited distribution.  Please see Copyright notice for non-US Government use and distribution.
// This Software includes and/or makes use of the following Third-Party Software subject to its own license:
// 1. Packery (https://packery.metafizzy.co/license.html) Copyright 2018 metafizzy.
// 2. Bootstrap (https://getbootstrap.com/docs/4.0/about/license/) Copyright 2011-2018  Twitter, Inc. and Bootstrap Authors.
// 3. JIT/Spacetree (https://philogb.github.io/jit/demos.html) Copyright 2013 Sencha Labs.
// 4. html5shiv (https://github.com/aFarkas/html5shiv/blob/master/MIT%20and%20GPL2%20licenses.md) Copyright 2014 Alexander Farkas.
// 5. jquery (https://jquery.org/license/) Copyright 2018 jquery foundation.
// 6. CanvasJS (https://canvasjs.com/license/) Copyright 2018 fenopix.
// 7. Respond.js (https://github.com/scottjehl/Respond/blob/master/LICENSE-MIT) Copyright 2012 Scott Jehl.
// 8. Datatables (https://datatables.net/license/) Copyright 2007 SpryMedia.
// 9. jquery-bridget (https://github.com/desandro/jquery-bridget) Copyright 2018 David DeSandro.
// 10. Draggabilly (https://draggabilly.desandro.com/) Copyright 2018 David DeSandro.
// 11. Business Casual Bootstrap Theme (https://startbootstrap.com/template-overviews/business-casual/) Copyright 2013 Blackrock Digital LLC.
// 12. Glyphicons Fonts (https://www.glyphicons.com/license/) Copyright 2010 - 2018 GLYPHICONS.
// 13. Bootstrap Toggle (http://www.bootstraptoggle.com/) Copyright 2011-2014 Min Hur, The New York Times.
// DM18-1351

var actuator_list = [];
var acttype = JSON.parse('{"variable": ["OFF","DECREASE","MAINTAIN","INCREASE"],'+
                         '"relational":["OFF","LOW","MEDIUM","HIGH"],' +
                         '"locked": ["LOCKED", "UNLOCKED"],' +
                         '"enabled": ["DISABLED","ENABLED"],' +
                         '"default": ["OFF","ON"]}');
/*
* Function:
* Description:
* Arguments:
* Returns:
* */
function init(root_id){
    $.getJSON("/api/device/tree/" + root_id, generate_map);
    $.getJSON("/api/sensors/", sensor_list);
}

/*
* Function: Generate Map
* Description: Generates device map derived from HMI data server http get json file. Updates onclick
* Arguments: json: json object of the device map configuration
* Returns: void
* */
function generate_map(json){
    var st = new $jit.ST({
            injectInto: 'infovis',
            duration: 400,
            transition: $jit.Trans.Quart.easeInOut,
            levelDistance: 50,
            Navigation: {
              enable:true,
              panning:true
            },
            Node: {
                height: 70,
                width: 60,
                type: 'rectangle',
                color: '#aaa',
                overridable: true
            },
            Edge: {
                type: 'bezier',
                overridable: true
            },

            onCreateLabel: function(label, node){
                label.id = node.id;
                label.innerHTML = node.name;
                label.onclick = function(){
                    st.setRoot(node.id, 'animate');
                };
                var style = label.style;
                style.width = 60 + 'px';
                style.height = 17 + 'px';
                style.cursor = 'pointer';
                style.color = '#333';
                style.fontSize = '0.8em';
                style.textAlign= 'center';
                style.paddingTop = '3px';
            },

            onBeforePlotNode: function(node){
                if (node.id === st.root){
                    for (i = 0; i < actuator_list.length; i++){
                        document.getElementById("actuator_" + i).innerHTML = "";
                        document.getElementById("root_node").innerHTML = "";
                    }
                    actuator_list = [];
                    for(i = 0; i < node.data.Actuators.length; i++){
                        actuator_list.push(node.data.Actuators[i].id);
                    }
                    var title = document.createElement('h3');
                    title.innerHTML = node.name + " Actuator Controls";
                    document.getElementById("root_node").appendChild(title);
                    add_actuator(node.data.Actuators, node.name);
                }
                if (node.selected) {
                    node.data.$color = "#ff7";
                }
                else {
                    delete node.data.$color;
                    if(!node.anySubnode("exist")) {
                        var count = 0;
                        node.eachSubnode(function(n) { count++; });
                        node.data.$color = ['#aaa', '#baa', '#caa', '#daa', '#eaa', '#faa'][count];
                    }
                }
            },

            onBeforePlotLine: function(adj){
                if (adj.nodeFrom.selected && adj.nodeTo.selected) {
                    adj.data.$color = "#eed";
                    adj.data.$lineWidth = 3;
                }
                else {
                    delete adj.data.$color;
                    delete adj.data.$lineWidth;
                }
            }
        });
        st.loadJSON(json);
        st.compute();
        st.geom.translate(new $jit.Complex(-200, 0), "current");
        st.onClick(st.root);
}

/*
* Function: Add Actuator
* Description: Generates Actuator containers reflected on the base node of the device map. Onclick posts the new
* state to the HMI's database
* Arguments: Actuator List: String List of actuator ID's of base node
*            Device: String of root node name
* Returns: void
* */
function add_actuator(actuator_list, device){
    for(j = 0; j < actuator_list.length; j++)
    {
        node = actuator_list[j];
        var var_list = [];
        if (acttype.hasOwnProperty(node.type)){
            var_list = acttype[(node.type)];
        }else{
            var_list = acttype.default;
        }

        var group = document.createElement("div");
        group.setAttribute('class', "btn-group");
        group.setAttribute('data-toggle', "buttons");
        group.id = node.id;

        var title = document.createElement("p");
        title.setAttribute("align", "center");
        title.innerHTML = device + ": " + node.name;
        $.getJSON("/api/actuators/" + node.id, function (data) {
            node.value = data.value;
        });

        for(i = 0; i < var_list.length; i++) {
            var button = document.createElement('label');
            var button_input = document.createElement('input');
            button.setAttribute("id", node.id + "#" + i);
            button.onclick=function(){
                update_actuator(this.id);
            };
            if(node.type === "variable"){
                button.setAttribute("style", "font-size:10px");
            }
            if(i == node.value){
                button.className = "btn btn-primary active";
                button_input.checked = true;
            }else{
                button.className = "btn btn-primary";
            }
            button_input.type = "radio";
            button_input.setAttribute("name", "options");
            button_input.setAttribute("autocomplete", "off");

            button.innerHTML = var_list[i];
            button.appendChild(button_input);
            group.appendChild(button);

        }
        document.getElementById("actuator_" + j).appendChild(title);
        document.getElementById("actuator_" + j).appendChild(group);
    }
}

/*
* Function: Sensor List
* Description: Generates all Sensors defined within the HMI
* Arguments: Data: json object list of sensors defined with the HMI database
* Returns: void
* */
function sensor_list(list){
    for(i = 0; i < list.length; i++){
        var re = $.getJSON("/api/sensors/" + list[i].id + "/1");
        re.done(function(data){
            var dps = [];
            for (var j = 0; j < data.data.length; j++){
                dps.push({x: new Date(data.data[j].event_time.replace(/ /g, 'T')), y: data.data[j].value});
	    }
            add_sensor(data.id, dps);
        });
    }
}

/*
* Function: Add Sensor
* Description: Generates a Sensor Graph container and uses http gets on the HMI data server to update
* the graph every 300 ms
* Arguments: Sensor: json Object representation of the sensor's configuration
* Returns: void
* */
function add_sensor(sen, datapoints) {
    var dps = datapoints; // dataPoints
    var updateInterval = 30000;
    var dataLength = 500; // number of dataPoints visible at any point
    var chart = new CanvasJS.Chart(sen.id, {
        title: {
            text: sen.name
        },
        data: [{
            type: "line",
            dataPoints: dps
        }]
    });
    chart.render();

    $.getJSON("/api/sensors/" + sen.id + "/1", function (data) {
        for (var j = 0; j < data.length; j++){
            dps.push({
                x: new Date(data[j].event_time), 
                y: data[j].value
            });
	};
    });

    var updateChart = function () {
        $.getJSON("/api/sensors/" + sen.id, function (data) {
            dps.push({
                x: new Date(),
                y: data.value
            });
       });
        if (dps.length > dataLength)
        {
            dps.shift();
        }
        chart.render();
    };
        // generates first set of dataPoints

    // update chart after specified time.
   setInterval(function () {updateChart()}, updateInterval); 
}

/*
* Function: Update Actuator
* Description: Sends HTTP Post to HMI's data server to update current actuator values
* Arguments: Selection: json object that reflects the actuators configuration
* Returns: void
* */
function update_actuator(selection){
    var select = selection.split("#");

    var update_act = new XMLHttpRequest();
    var formData = new FormData();
    formData.append('newValue', select[1]);
    formData.append('name', select[0]);
    update_act.open("POST", "/api/actuators/" + select[0], true);
    update_act.send(formData);
}
