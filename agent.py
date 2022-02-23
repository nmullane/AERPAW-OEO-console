import paho.mqtt.client as mqtt
import time
import random
import sys
from agent_json_builder import AgentData, Data

id = int(sys.argv[1])
status = "disarmed"
velocity = [0.0, 0.0, 0.0]

broker = "localhost"

pub = mqtt.Client(f"agent_{id}_status_pub")
pub.connect(broker, 1883)
pub.loop_start()

start = time.time()
armed_delay = random.randrange(1, 20)

heartbeat = 0
while True:
    if time.time() > start + armed_delay:
        status = "ARMED"

    # modify velocity for interesting data
    dv = [
        (random.randrange(1, 10) - 5) / 10,
        (random.randrange(1, 10) - 5) / 10,
        (random.randrange(1, 10) - 5) / 10,
    ]
    for i in range(3):
        velocity[i] += dv[i]

    data_list = [
        Data("status", status),
        Data("velocity", velocity),
        Data("heartbeat", heartbeat),
    ]
    data = AgentData(id, data_list).to_json()

    pub.publish("cedalo/agent_status", data)
    heartbeat += 1
    time.sleep(0.1)
