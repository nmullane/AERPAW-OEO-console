#!/usr/bin/env python
# -*- coding: utf-8 -*-

import paho.mqtt.client as mqtt
import time
import json
import sys

num_nodes = int(sys.argv[1])

heartbeat_monitor = {}
# Add the number of expected nodes to the packet
heartbeat_monitor["num_nodes"] = num_nodes

for node in range(num_nodes):
    heartbeat_monitor[node] = {"connected": False, "last_heartbeat": None}


def on_message(client, userdata, message):
    msg = json.loads(message.payload)
    print(msg)
    timestamp = msg["timestamp"]
    node_id = msg["node_id"]

    # Get entry in heartbeat monitors for this node
    monitor = heartbeat_monitor[node_id]
    # update entry for this node
    monitor["connected"] = True
    monitor["last_heartbeat"] = timestamp


broker = "localhost"

pub = mqtt.Client("heartbeat_monitor_pub")
pub.connect(broker, 1883)
pub.loop_start()

sub = mqtt.Client("heartbeat_monitor_sub")
sub.connect(broker, 1883)
sub.subscribe("OEO/HEARTBEATS")
sub.on_message = on_message
sub.loop_start()

i = 0
while True:
    pub.publish("OEO/HEARTBEAT_MONITOR", json.dumps(heartbeat_monitor))
    time.sleep(1)
