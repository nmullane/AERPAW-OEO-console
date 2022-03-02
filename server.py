import paho.mqtt.client as mqtt
import time
import json
import sys
from agent_json_builder import AgentData, Data

# num_nodes = int(sys.argv[1])

agent_statuses = {}


def on_message(client, userdata, message):
    msg = json.loads(message.payload)

    # if there is no agent status dict for this id create an empty one
    if msg["id"] not in agent_statuses:
        agent_statuses[msg["id"]] = {}
    # update every piece of data in the agent status dict present in this message
    for data in msg["data"]:
        agent_status = agent_statuses[msg["id"]]
        agent_status[data["type"]] = data["data"]


broker = "localhost"

pub = mqtt.Client("server_status_pub")
pub.connect(broker, 1883)
pub.loop_start()

sub = mqtt.Client("server_status_sub")
sub.connect(broker, 1883)
sub.subscribe("OEO/agent_status")
sub.on_message = on_message
sub.loop_start()

while True:
    print(agent_statuses)
    pub.publish("OEO/status", json.dumps(agent_statuses))
    time.sleep(0.1)
