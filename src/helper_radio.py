import proto.radio_information_pb2 as pb
import random
import zmq
import zmq.asyncio
import time
import sys
import asyncio
import constants


class RadioHelper:
    def __init__(
        self,
        port=constants.DEFAULT_RADIO_AGENT_PORT,
        dt=0.1,
        broker_ip: str = "localhost",
    ):
        self.dt = dt

        # setup ZMQ context and socket
        self.context = zmq.asyncio.Context()
        # one-to-one bi-directional PAIR socket
        self.socket = self.context.socket(zmq.PAIR)
        # bind to the given port on any IP address
        self.socket.bind("tcp://*:%s" % port)

        self.heartbeat = 0
        self.radio_message_data = pb.RadioInformationData()

    def update_data(self):
        # TODO implement
        self.radio_message_data.compliant = True
        if random.random() < 0.01:
            self.radio_message_data.compliant = False

    async def send_data(self):
        data = self.radio_message_data.SerializeToString()
        self.socket.send(data)

    async def loop(self):
        while True:
            self.update_data()
            await self.send_data()
            await asyncio.sleep(self.dt)

    def run(self):
        asyncio.run(self.loop())
