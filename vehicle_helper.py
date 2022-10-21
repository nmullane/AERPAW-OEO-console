import proto.vehicle_information_pb2 as pb
import random
import zmq
import zmq.asyncio
import time
import sys
import asyncio
import dronekit
import paho.mqtt.client as mqtt
import json


class VehicleHelper:
    """Dummy class to create data as if it was a vehicle helper"""

    def __init__(self, port=5556, dt=0.1, downlink: str=None):
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

    def run(self):
        asyncio.run(self.loop())


class VehicleHelperMikuMode:
    _dk_vehicle: dronekit.Vehicle
    
    def __init__(self, port=5556, dt=0.1, downlink: str=None, id: str=None):
        # TODO load vehicle type config from file of some sort
        self.dt = dt # dt is delay between samples -- TODO should conv from Hz in theory
        self.id = id

        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.bind(f"tcp://*:{port}")

        self.heartbeat = 0
        self.vehicle_information = pb.VehicleInformationData() # TODO we trust the zero values here

        self.start = time.time()

        assert downlink is not None
        self._dk_vehicle = dronekit.connect(downlink, wait_ready=True)
        self._dk_vehicle.commands.download()
        self._dk_vehicle.commands.wait_ready()

        self.vehicle_command_sub = mqtt.Client("vehicle_command_sub")

        try:
            self.vehicle_command_sub.connect("localhost", 1883)
            self.vehicle_command_sub.subscribe([("OEO/vehicle_command", 0)])
            self.vehicle_command_sub.on_message = self.receive_data_handler
        except ConnectionRefusedError as e:
            print(e)
            raise Exception("MQTT not running")
    
    def on_message_print_helper(self, client, userdata, message):
        """Deserialize vehicle information protobuf message"""
        print(message.payload)
    
    def update_data(self):
        # read in data from dronekit and populate fields on protobuf
        self.vehicle_information.status = 1 if self._dk_vehicle.armed else 0

        batt_info = self._dk_vehicle.battery
        self.vehicle_information.battery_voltage = batt_info.voltage
        self.vehicle_information.battery_current = batt_info.current
        self.vehicle_information.battery_percent = batt_info.level

        pos_global = self._dk_vehicle.location.global_relative_frame
        self.vehicle_information.latitude = pos_global.lat
        self.vehicle_information.longitude = pos_global.lon
        self.vehicle_information.altitude = pos_global.alt

        vx, vy, vz = self._dk_vehicle.velocity
        self.vehicle_information.velocity.x = vx
        self.vehicle_information.velocity.y = vy
        self.vehicle_information.velocity.z = vz
    
    async def send_data(self):
        data = self.vehicle_information.SerializeToString()
        self.socket.send(data)

    def receive_data_handler(self, client, userdata, message):
        # only care about message, which can be deserialized and read
        payload = message.payload
        print(payload)
        try:
            payload_data = json.loads(payload)
        except Exception as e:
            print(e)
            return
        print(payload_data, self.id)
        if payload_data["node_id"] != self.id:
            return
        verb = payload_data["verb"]
        handler = {
            "arm": self.arm_solo_handler,
            "disarm": self.disarm_handler,
            "mode": self.mode_handler,
            "rtl": self.rtl_handler,
            "land": self.land_handler,
            "takeoff": self.takeoff_handler,
        }.get(verb, None)
        if handler is None:
            print("received unknown command: " + payload)
            return
        handler(payload_data)

    def arm_handler(self, payload_data):
        armed = payload_data["data"]["armed"]
        if armed == True:
            self._dk_vehicle.armed = True
        elif armed == False:
            self._dk_vehicle.armed = False
    
    def arm_solo_handler(self, payload_data):
        self._dk_vehicle.armed = True

    def disarm_handler(self, payload_data):
        self._dk_vehicle.armed = False
    
    def mode_handler(self, payload_data):
        mode = payload_data["data"]["mode"]
        if mode not in ["GUIDED", "MANUAL", "ALT_HOLD"]:
            print("unsupported mode " + mode)
            return
        self._dk_vehicle.mode = {
            "GUIDED": "GUIDED",
            "MANUAL": "MANUAL",
            "ALT_HOLD": "ALT_HOLD",
        }[mode]
    
    def rtl_handler(self, payload_data):
        self._dk_vehicle.mode = "RTL"
    
    def takeoff_handler(self, payload_data):
        altitude = payload_data["data"]["altitude"]
        self._dk_vehicle.simple_takeoff(alt=altitude)

    def land_handler(self, payload_data):
        self._dk_vehiclek.mode = "LAND"
    
    async def loop(self):
        self.vehicle_command_sub.loop_start()
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
        helper = VehicleHelper()
        asyncio.run(helper.loop())
