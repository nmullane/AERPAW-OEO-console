import paho.mqtt.client as mqtt
import time
import json
import sys
from agent_json_builder import AgentData, Data

# num_nodes = int(sys.argv[1])

agent_statuses = {}


def on_message(client, userdata, message):
    msg = json.loads(message.payload)

    # Assume msg is a dictionary and pass in all
    # key-value pairs to the AgentData constructor
    # this will need to be error checked in the future
    agent_statuses[msg["id"]] = msg["data"]


broker = "localhost"

pub = mqtt.Client("server_status_pub")
pub.connect(broker, 1883)
pub.loop_start()

sub = mqtt.Client("server_status_sub")
sub.connect(broker, 1883)
sub.subscribe("agent_status")
sub.on_message = on_message
sub.loop_start()

while True:
    print(agent_statuses)
    pub.publish("status", json.dumps(agent_statuses))
    time.sleep(0.1)
