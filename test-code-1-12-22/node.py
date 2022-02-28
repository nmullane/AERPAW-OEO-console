#!/usr/bin/env python
# -*- coding: utf-8 -*-

import paho.mqtt.client as mqtt
import time
import json
import random
import sys

node_id = int(sys.argv[1])

# sleep for a random time before doing anything
time.sleep(random.randrange(1, 20))

broker = "localhost"

pub = mqtt.Client(f"heartbeat_pub_{node_id}")
pub.connect(broker, 1883)
pub.loop_start()

while True:
    pub.publish(
        "HEARTBEATS", json.dumps({"timestamp": time.time(), "node_id": node_id})
    )
    print(f"{node_id}: Publishing heartbeat")
    time.sleep(1)
