import proto.vehicle_information_pb2 as pb
import random
import zmq
import zmq.asyncio
import time
import sys
import asyncio


class VehicleHelper:
    """Dummy class to create data as if it was a vehicle helper"""

    def __init__(self, port=5556, dt=0.1):
        self.dt = dt

        # setup ZMQ context and sockets
        self.context = zmq.asyncio.Context()
        # one-to-one bi-directional PAIR socket
        self.socket = self.context.socket(zmq.PAIR)
        # bind to the given port on any IP address
        self.socket.bind("tcp://*:%s" % port)

        self.heartbeat = 0
        self.vehicle_information = pb.VehicleInformationData()

        ## Dummy data initialization
        self.start = time.time()

        self.armed_delay = random.randrange(1, 20)
        self.batt_current = 0.0
        self.velocity = [0.0, 0.0, 0.0]
        self.vehicle_information.altitude = 0

        self.vehicle_information.status = 0

        self.vehicle_information.battery_voltage = 13.0
        self.vehicle_information.battery_current = 0
        self.vehicle_information.battery_percent = 100

        # random valid position
        self.vehicle_information.latitude = random.random() * 180 - 90
        self.vehicle_information.longitude = random.random() * 360 - 180

    def update_data(self):
        if time.time() > self.start + self.armed_delay:
            self.vehicle_information.status = 1

        # modify velocity for interesting data
        dv = [
            (random.randrange(1, 10) - 5) * self.dt,
            (random.randrange(1, 10) - 5) * self.dt,
            (random.randrange(1, 10) - 5) * self.dt,
        ]
        self.vehicle_information.altitude += self.velocity[2] * self.dt

        # reset current and calculate it based on velocity
        self.vehicle_information.battery_current = 0.0

        # update velocity and calculate battery stuff
        for i in range(3):
            self.velocity[i] += dv[i]

            # modify battery voltage proportional to velocity because that kind of makes sense
            self.vehicle_information.battery_voltage -= (
                self.velocity[i] / 1000.0
            )  # these are pointless magic numbers
            self.vehicle_information.battery_current += self.velocity[i] / 10.0

        self.vehicle_information.velocity.x = self.velocity[0]
        self.vehicle_information.velocity.y = self.velocity[1]
        self.vehicle_information.velocity.z = self.velocity[2]

        # what is this supposed to be?
        self.vehicle_information.battery_percent = (
            self.vehicle_information.battery_voltage / 12.0
        )

    async def send_data(self):
        data = self.vehicle_information.SerializeToString()
        self.socket.send(data)

    async def loop(self):
        while True:
            self.update_data()
            await self.send_data()
            await asyncio.sleep(self.dt)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print("HI")
    else:
        helper = VehicleHelper()
        asyncio.run(helper.loop())
