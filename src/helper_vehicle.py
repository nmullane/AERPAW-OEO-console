import proto.vehicle_information_pb2 as pb
import random
import zmq
import zmq.asyncio
import time
import asyncio
import dronekit
import paho.mqtt.client as mqtt
import json
import constants


class VehicleHelper:
    _dk_vehicle: dronekit.Vehicle

    def __init__(
        self,
        port=constants.DEFAULT_VEHICLE_AGENT_PORT,
        dt=0.1,
        downlink: str = None,
        id: str = None,
        broker_ip: str = "localhost",
    ):
        # TODO parse any configuration things in from a config file loaded by the agent
        self.dt = dt  # dt is delay between samples
        self.id = id

        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.bind(f"tcp://*:{port}")

        self.heartbeat = 0
        self.vehicle_information = pb.VehicleInformationData()

        self.start = time.time()

        assert downlink is not None
        self._dk_vehicle = dronekit.connect(downlink, wait_ready=True)
        self._dk_vehicle.commands.download()
        self._dk_vehicle.commands.wait_ready()

        self.vehicle_command_sub = mqtt.Client("vehicle_command_sub")

        try:
            self.vehicle_command_sub.connect(broker_ip, 1883)
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
        try:
            payload_data = json.loads(payload)
        except Exception as e:
            print(e)
            return
        if payload_data["node_id"] != str(self.id):
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
        mode = str(payload_data["data"]["mode"])
        mode = mode.upper()
        if mode not in ["GUIDED", "MANUAL", "ALT_HOLD"]:
            print("unsupported mode " + mode)
            return
        self._dk_vehicle.mode = {
            "GUIDED": "GUIDED",
            "MANUAL": "MANUAL",
            "ALT_HOLD": "ALT_HOLD",
        }[mode]

    def rtl_handler(self, _):
        self._dk_vehicle.mode = "RTL"

    def takeoff_handler(self, payload_data):
        altitude = payload_data["data"]["altitude"]
        self._dk_vehicle.simple_takeoff(alt=altitude)

    def land_handler(self, _):
        self._dk_vehicle.mode = "LAND"

    async def loop(self):
        self.vehicle_command_sub.loop_start()
        while True:
            self.update_data()
            await self.send_data()
            await asyncio.sleep(self.dt)

    def run(self):
        asyncio.run(self.loop())
