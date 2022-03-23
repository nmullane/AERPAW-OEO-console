import paho.mqtt.client as mqtt
import time
import random
import sys
from agent_json_builder import AgentData

id = int(sys.argv[1])
status = "disarmed"
velocity = [0.0, 0.0, 0.0]
altitude = 0

batt_voltage = 13.0
batt_current = 0
batt_percent = 100

# random valid position
latitude = random.random() * 180 - 90
longitude = random.random() * 360 - 180


broker = "localhost"

node_health_pub = mqtt.Client(f"agent_{id}_health_pub")
node_health_pub.connect(broker, 1883)
node_health_pub.loop_start()

vehicle_information_pub = mqtt.Client(f"agent_{id}_vehicle_pub")
vehicle_information_pub.connect(broker, 1883)
vehicle_information_pub.loop_start()

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

    radio_compliant = True
    if random.random() < 0.05:
        radio_compliant = False
    data_dict = {"status": radio_compliant}
    radio_info_data = AgentData(id, data_dict).to_json()

    #####################################
    #### vehicle information message ####
    #####################################
    if time.time() > start + armed_delay:
        status = "ARMED"

    # modify velocity for interesting data
    dv = [
        (random.randrange(1, 10) - 5) * dt,
        (random.randrange(1, 10) - 5) * dt,
        (random.randrange(1, 10) - 5) * dt,
    ]
    altitude += velocity[2] * dt

    # reset current and calculate it based on velocity
    batt_current = 0.0

    # update velocity and calculate battery stuff
    for i in range(3):
        velocity[i] += dv[i]

        # modify battery voltage proportional to velocity because that kind of makes sense
        batt_voltage -= velocity[i] / 1000.0  # these are pointless magic numbers
        batt_current += velocity[i] / 10.0

    # what is this supposed to be?
    batt_percent = batt_voltage / 12.0

    data_dict = {
        "status": status,
        "velocity": velocity,
        "latitude": latitude,
        "longitude": longitude,
        "altitude": altitude,
        "battery_voltage": batt_voltage,
        "battery_current": batt_current,
        "battery_percent": batt_percent,
    }

    vehicle_info_data = AgentData(id, data_dict).to_json()

    #############################
    #### node health message ####
    #############################

    # random cpu between 0% and 40%
    cpu_utilization = random.random() * 40
    # random memory between 20% and 50%
    memory_utilization = random.random() * 30 + 20
    data_dict = {
        "heartbeat": heartbeat,
        "vehicle_script_running": True,
        "E-VM_script_running": True,
        "cpu_utilization": cpu_utilization,
        "memory_utilization": memory_utilization,
    }

    node_health_data = AgentData(id, data_dict).to_json()

    # don't publish error_rate percent of messages
    if random.random() > error_rate:
        node_health_pub.publish("OEO/node_health", node_health_data)
        vehicle_information_pub.publish("OEO/vehicle_information", vehicle_info_data)
        radio_information_pub.publish("OEO/radio_information", radio_info_data)
        # Since mqtt works over tcp we will never be losing messages, so assume
        # this error rate behaves to add a random delay. only update the
        # heartbeat when a message is actually sent
        # update heartbeat
        heartbeat += 1
    time.sleep(dt)
