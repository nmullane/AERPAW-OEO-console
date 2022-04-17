import proto.computer_health_pb2 as pb_computer
import proto.radio_information_pb2 as pb_radio
import proto.vehicle_information_pb2 as pb_vehicle
import paho.mqtt.client as mqtt
import time
import random
import sys
import zmq.asyncio as zmq
import asyncio


class Agent:
    def __init__(
        self,
        id,
        vehicle_helper=False,
        vehicle_port=5556,
        computer_helper=False,
        computer_port=5557,
        radio_helper=False,
        radio_port=5558,
        broker="localhost",
        mqtt_port=1883,
    ):
        self.id = id
        self.broker = broker
        self.port = mqtt_port

        self.vehicle_helper = vehicle_helper
        self.computer_helper = computer_helper
        self.radio_helper = radio_helper

        # setup zmq context
        self.context = zmq.Context()

        if self.vehicle_helper:
            # connect to vehicle helper
            self.vehicle_socket = self.context.socket(zmq.PAIR)
            # assumes the vehicle helper is on localhost
            self.vehicle_socket.connect("tcp://localhost:%s" % vehicle_port)

            self.vehicle_information_pub = mqtt.Client(f"agent_{id}_vehicle_pub")
            self.vehicle_information_pub.connect(self.broker, self.port)
            self.vehicle_information_pub.loop_start()

            # Create an empty data variable for publishing
            self.vehicle_information_data = pb_vehicle.VehicleInformation()

        if self.radio_helper:
            # connect to radio helper
            self.radio_socket = self.context.socket(zmq.PAIR)
            # assumes the radio helper is on localhost
            self.radio_socket.connect("tcp://localhost:%s" % radio_port)

            self.radio_information_pub = mqtt.Client(f"agent_{id}_radio_pub")
            self.radio_information_pub.connect(self.broker, self.port)
            self.radio_information_pub.loop_start()

            # Create an empty data variable for publishing
            self.radio_information_data = pb_radio.RadioInformation()

        if self.computer_helper:
            # connect to computer helper
            self.computer_socket = self.context.socket(zmq.PAIR)
            # assumes the computer helper is on localhost
            self.computer_socket.connect("tcp://localhost:%s" % computer_port)

            self.computer_health_pub = mqtt.Client(f"agent_{self.id}_computer_pub")
            self.computer_health_pub.connect(self.broker, self.port)
            self.computer_health_pub.loop_start()

            # Create an empty data variable for publishing
            self.computer_health_data = pb_computer.ComputerHealth()

    async def vehicle_loop(self):
        while True:
            data = await self.vehicle_socket.recv()
            data = pb_vehicle.ParseFromString(data)

            # Construct a message containing the helper data
            message = pb_vehicle.VehicleInformation()
            message.id = self.id
            message.data = data
            self.vehicle_information_pub.publish("OEO/vehicle_information", message)

    async def radio_loop(self):
        while True:
            data = await self.radio_socket.recv()
            data = pb_radio.ParseFromString(data)

            # Construct a message containing the helper data
            message = pb_radio.RadioInformation()
            message.id = self.id
            message.data = data
            self.radio_information_pub.publish("OEO/radio_information", message)

    async def computer_loop(self):
        while True:
            data = await self.computer_socket.recv()
            data = pb_computer.ParseFromString(data)

            # Construct a message containing the helper data
            message = pb_computer.ComputerHealth()
            message.id = self.id
            message.data = data
            self.computer_health_pub.publish("OEO/node_health", message)

    async def loop(self):
        if self.vehicle_helper:
            vehicle_loop = asyncio.create_task(self.vehicle_loop())
        if self.radio_helper:
            radio_loop = asyncio.create_task(self.radio_loop())
        if self.computer_helper:
            computer_loop = asyncio.create_task(self.computer_loop())

    def run(self):
        """Function to run all of the necessary loops"""
        asyncio.run(self.loop())


class PortableAgent(Agent):
    """Wrapper class to construct an agent with the correct subset of helpers
    for a portable agent"""

    def __init__(self, *args):
        super(PortableAgent, self).__init__(
            *args, vehicle_helper=True, computer_helper=True, radio_helper=True
        )


class FixedAgent(Agent):
    """Wrapper class to construct an agent with the correct subset of helpers
    for a fixed agent"""

    def __init__(self, *args):
        super(FixedAgent, self).__init__(*args, computer_helper=True, radio_helper=True)


class CloudAgent(Agent):
    """Wrapper class to construct an agent with the correct subset of helpers
    for a cloud agent"""

    def __init__(self, *args):
        super(CloudAgent, self).__init__(*args, radio_helper=True)


id = sys.argv[1]

broker = "localhost"

node_health_pub = mqtt.Client(f"agent_{id}_health_pub")
node_health_pub.connect(broker, 1883)
node_health_pub.loop_start()


start = time.time()
armed_delay = random.randrange(1, 20)

heartbeat = 0

# not actually an error rate. used to randomly delay messages
error_rate = random.random()

dt = 0.1
while True:
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
        # Since mqtt works over tcp we will never be losing messages, so assume
        # this error rate behaves to add a random delay. only update the
        # heartbeat when a message is actually sent
        # update heartbeat
        heartbeat += 1
    time.sleep(dt)
