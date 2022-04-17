import proto.computer_health_pb2 as pb
import random
import zmq.asyncio as zmq
import time


class ComputerHelper:
    """Dummy class to create data as if it was a computer helper"""

    def __init__(self, port=5557, dt=0.1):
        self.dt = dt

        # setup ZMQ context and sockets
        self.context = zmq.Context()
        # one-to-one bi-directional PAIR socket
        self.socket = self.context.socket(zmq.PAIR)
        # bind to the given port on any IP address
        self.socket.bind("tcp://*:%s" % port)

        self.heartbeat = 0
        self.health_message_data = pb.ComputerHealthData()

    def update_data(self):
        self.heartbeat += 1

        self.health_message_data.heartbeat = self.heartbeat
        # random cpu between 0% and 40%
        self.health_message_data.cpu_utilization = random.random() * 40
        # random memory between 20% and 50%
        self.health_message_data.memory_utilization = random.random() * 30 + 20

        self.health_message_data.vehicle_script_running = False
        self.health_message_data.evm_script_running = True

    async def send_data(self):
        data = self.health_message_data.SerializeToString()
        self.socket.send(data)

    async def loop(self):
        while True:
            self.update_data()
            await self.send_data()
            await time.sleep(self.dt)
