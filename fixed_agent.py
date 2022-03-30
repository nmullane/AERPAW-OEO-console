import paho.mqtt.client as mqtt
import time
import random
import sys
from agent_json_builder import AgentData

id = sys.argv[1]

broker = "localhost"

node_health_pub = mqtt.Client(f"agent_{id}_health_pub")
node_health_pub.connect(broker, 1883)
node_health_pub.loop_start()

radio_information_pub = mqtt.Client(f"agent_{id}_radio_pub")
radio_information_pub.connect(broker, 1883)
radio_information_pub.loop_start()

start = time.time()
armed_delay = random.randrange(1, 20)

heartbeat = 0

# not actually an error rate. used to randomly delay messages
error_rate = random.random()

dt = 0.1
while True:
    ###################################
    #### radio information message ####
    ###################################

    radio_status = "compliant"
    if random.random() < 0.01:
        radio_status = "not compliant"
    data_dict = {"radio_status": radio_status}
    radio_info_data = AgentData(id, data_dict).to_json()

    #############################
    #### node health message ####
    #############################

    # random cpu between 0% and 40%
    cpu_utilization = random.random() * 40
    # random memory between 20% and 50%
    memory_utilization = random.random() * 30 + 20
    data_dict = {
        "heartbeat": heartbeat,
        "vehicle_script_running": False,
        "E-VM_script_running": True,
        "cpu_utilization": cpu_utilization,
        "memory_utilization": memory_utilization,
    }

    node_health_data = AgentData(id, data_dict).to_json()

    # don't publish error_rate percent of messages
    if random.random() > error_rate:
        node_health_pub.publish("OEO/node_health", node_health_data)
        radio_information_pub.publish("OEO/radio_information", radio_info_data)
        # Since mqtt works over tcp we will never be losing messages, so assume
        # this error rate behaves to add a random delay. only update the
        # heartbeat when a message is actually sent
        # update heartbeat
        heartbeat += 1
    time.sleep(dt)
