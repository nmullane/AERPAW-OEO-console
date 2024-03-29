import proto.radio_information_pb2 as pb
import random
import zmq
import zmq.asyncio
import time
import sys
import asyncio


class RadioHelper:
    """Dummy class to create data as if it was a radio helper"""

    def __init__(self, port=5558, dt=0.1):
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


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print("HI")
    else:
        helper = RadioHelper()
        asyncio.run(helper.loop())
