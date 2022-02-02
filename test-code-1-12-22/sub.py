#!/usr/bin/env python
# -*- coding: utf-8 -*-

import paho.mqtt.client as mqtt
import time


def on_message(client, userdata, message):
    print("received message: ", str(message.payload.decode("utf-8")))

broker = "127.0.0.1"

client = mqtt.Client("count_sub_test")
client.connect(broker, 1883)

client.subscribe("cedalo/COUNT_PAUSE")
#client.subscribe("cedalo/powerplant/plants/windmill")
client.on_message=on_message

client.loop_forever()
