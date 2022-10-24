import proto.computer_health_pb2 as pb_computer
import proto.radio_information_pb2 as pb_radio
import proto.vehicle_information_pb2 as pb_vehicle
import paho.mqtt.client as mqtt
import zmq
import zmq.asyncio
import asyncio
from constants import *


class Agent:
    def __init__(
        self,
        id,
        vehicle_helper=False,
        vehicle_port=DEFAULT_VEHICLE_AGENT_PORT,
        computer_helper=False,
        computer_port=DEFAULT_COMPUTER_AGENT_PORT,
        radio_helper=False,
        radio_port=DEFAULT_RADIO_AGENT_PORT,
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
        self.context = zmq.asyncio.Context()

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
            parse_data = pb_vehicle.VehicleInformationData()
            parse_data.ParseFromString(data)

            # Construct a message containing the helper data
            message = pb_vehicle.VehicleInformation()
            message.id = self.id
            message.data.CopyFrom(parse_data)
            self.vehicle_information_pub.publish(
                "OEO/vehicle_information", message.SerializeToString()
            )

    async def radio_loop(self):
        while True:
            data = await self.radio_socket.recv()
            parse_data = pb_radio.RadioInformationData()
            parse_data.ParseFromString(data)

            # Construct a message containing the helper data
            message = pb_radio.RadioInformation()
            message.id = self.id
            message.data.CopyFrom(parse_data)
            self.radio_information_pub.publish(
                "OEO/radio_information", message.SerializeToString()
            )

    async def computer_loop(self):
        while True:
            data = await self.computer_socket.recv()
            parse_data = pb_computer.ComputerHealthData()
            parse_data.ParseFromString(data)

            # Construct a message containing the helper data
            message = pb_computer.ComputerHealth()
            message.id = self.id
            message.data.CopyFrom(parse_data)
            self.computer_health_pub.publish(
                "OEO/node_health", message.SerializeToString()
            )

    async def loop(self):
        loops = []
        if self.vehicle_helper:
            vehicle_loop = asyncio.create_task(self.vehicle_loop())
            loops.append(vehicle_loop)
        if self.radio_helper:
            radio_loop = asyncio.create_task(self.radio_loop())
            loops.append(radio_loop)
        if self.computer_helper:
            computer_loop = asyncio.create_task(self.computer_loop())
            loops.append(computer_loop)
        if len(loops) == 0:
            return
        await loops[0]

    def run(self):
        """Function to run all of the necessary loops"""
        asyncio.run(self.loop())
