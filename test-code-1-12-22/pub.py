#!/usr/bin/env python
# -*- coding: utf-8 -*-

import paho.mqtt.client as mqtt
import time
import json

publish = True


def on_message(client, userdata, message):
    global publish
    print("received pause")
    publish = not publish


broker = "localhost"

pub = mqtt.Client("count_pub")
pub.connect(broker, 1883)
pub.loop_start()

sub = mqtt.Client("count_sub")
sub.connect(broker, 1883)
sub.subscribe("OEO/COUNT_PAUSE")
sub.on_message = on_message
sub.loop_start()

i = 0
while True:
    if publish:
        pub.publish("OEO/COUNT", json.dumps({"count": i, "timestamp": time.time()}))
        print("Publishing", i)
        i += 1
    time.sleep(1)
