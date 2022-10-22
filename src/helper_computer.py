from distutils.log import error
import proto.computer_health_pb2 as pb
import random
import zmq
import zmq.asyncio
import time
import sys
import asyncio
import psutil
import constants


class ComputerHelper:
    def __init__(self, port=constants.DEFAULT_COMPUTER_AGENT_PORT, dt=0.1):
        self.dt = dt

        # setup ZMQ context and sockets
        self.context = zmq.asyncio.Context()
        # one-to-one bi-directional PAIR socket
        self.socket = self.context.socket(zmq.PAIR)
        # bind to the given port on any IP address
        self.socket.bind("tcp://*:%s" % port)

        self.heartbeat = 0
        self.health_message_data = pb.ComputerHealthData()

    def update_data(self):
        self.heartbeat += 1

        self.health_message_data.heartbeat = self.heartbeat

        self.health_message_data.cpu_utilization = psutil.cpu_percent()
        self.health_message_data.memory_utilization = psutil.virtual_memory().percent

        # TODO useless unless we know what to look for on the e-vm
        # proposal: let experimenters use specific tags on the executables to tell ops what is what
        self.health_message_data.vehicle_script_running = False
        self.health_message_data.radio_script_running = False
        self.health_message_data.traffic_script_running = False

    async def send_data(self):
        data = self.health_message_data.SerializeToString()
        self.socket.send(data)

    async def loop(self):
        while True:
            # based on the error rate don't update data or send message
            self.update_data()
            await self.send_data()
            await asyncio.sleep(self.dt)

    def run(self):
        asyncio.run(self.loop())
