"""This file is responsible for subscribing to mqtt messages
and generating events to log based on the messages received"""
import proto.computer_health_pb2 as pb_computer
import proto.radio_information_pb2 as pb_radio
import proto.vehicle_information_pb2 as pb_vehicle

from protobuf_to_dict import protobuf_to_dict

from asyncio import events
from typing import Dict, List
import paho.mqtt.client as mqtt
import random
from threading import Thread
import asyncio
import json


class Handlers:
    def __init__(self):
        self.handlers = None

    def get_handlers(self):
        """Return the dict of event_id keys mapped to defined handlers"""
        return self.handlers


class EventLogger(Thread):

    # data to parse and store for every agent
    data_to_display = []
    # dict of data values for every display data type for each agent
    # data is displayed in a live table
    display_data_vals = {}

    # data to look for changes as events
    event_data_types = ["status", "connection_status", "radio_status"]

    # create instance of event handlers class
    handlers = Handlers()
    # get dict of event handlers
    event_handlers = handlers.get_handlers()

    # dict of values for all event types for each agent
    # changes in the stored values are printed as events
    event_vals = {}

    def __init__(
        self,
        q: asyncio.Queue,
        table,
        live,
        data_to_display: List,
        broker_ip: str = "localhost",
    ):
        Thread.__init__(self)
        self.q = q
        self.computer_helper_sub = mqtt.Client("computer_helper_sub")
        self.radio_helper_sub = mqtt.Client("radio_helper_sub")
        self.vehicle_helper_sub = mqtt.Client("vehicle_helper_sub")
        self.microservice_sub = mqtt.Client("console_status_sub")
        self.table = table
        self.live = live
        self.data_to_display = data_to_display

        try:
            self.computer_helper_sub.connect(broker_ip, 1883)
            self.radio_helper_sub.connect(broker_ip, 1883)
            self.vehicle_helper_sub.connect(broker_ip, 1883)
            self.microservice_sub.connect(broker_ip, 1883)

            self.computer_helper_sub.subscribe([("OEO/node_health", 0)])
            self.radio_helper_sub.subscribe([("OEO/radio_information", 0)])
            self.vehicle_helper_sub.subscribe([("OEO/vehicle_information", 0)])
            self.microservice_sub.subscribe([("OEO/connection_status", 0)])

            self.computer_helper_sub.on_message = self.on_message_computer_helper
            self.radio_helper_sub.on_message = self.on_message_radio_helper
            self.vehicle_helper_sub.on_message = self.on_message_vehicle_helper
            self.microservice_sub.on_message = self.on_message_json
        except ConnectionRefusedError as e:
            print(e)
            raise Exception("MQTT not running!")

    # asyncronously wait for a new event to publish
    async def get_event(self):
        """Returns (agent_id, event_str)"""
        # await asyncio.sleep(0.1)
        event = await self.q.get()
        self.q.task_done()
        return event

    async def run(self):
        self.computer_helper_sub.loop_start()
        self.radio_helper_sub.loop_start()
        self.vehicle_helper_sub.loop_start()
        self.microservice_sub.loop_start()

    def data_from_status(self, data_type: str, status: List):
        """Look through every data within the status message of an agent for
        the given data_type and return the associated data"""
        try:
            return status[data_type]
        except:
            pass

    def update_display_data_from_dict(self, agent_id, data):
        """Updates the table of display data based on the provided data dictionary
        Uses q.put_no_wait could error"""
        for event_id in self.event_data_types:
            try:
                event_data = data[event_id]
            except:
                # The event data type was not present
                # this is fine
                continue

            # if a handler exists for this event, call the handler with the
            # agent id and the new data point
            # if event_id in self.event_handlers:
            #     event_data = self.event_handlers[event_id](agent_id, event_data)

            # add an entry to event vals for this agent if one does not exist
            if not agent_id in self.event_vals:
                agent_event_vals = {event_id: event_data}
                self.event_vals[agent_id] = agent_event_vals

                # the initial value of the event is an event
                # event = (agent_id, event_str)
                event = (
                    agent_id,
                    f"{event_id} for Agent {agent_id} is now {event_data}",
                )
                # put this event in a queue for the cli to display from
                self.q.put_nowait(event)
            # add an entry to the agent's event vals for this event_id if event_vals exists
            # for the agent but the event_id does not exist yet for it
            elif not event_id in self.event_vals[agent_id]:
                self.event_vals[agent_id][event_id] = event_data

                # the initial value of the event is an event
                # event = (agent_id, event_str)
                event = (
                    agent_id,
                    f"{event_id} for Agent {agent_id} is now {event_data}",
                )
                self.q.put_nowait(event)
            elif self.event_vals[agent_id][event_id] != event_data:
                # event = (agent_id, event_str)
                event = (
                    agent_id,
                    f"{event_id} for Agent {agent_id} is now {event_data}",
                )
                self.q.put_nowait(event)
                # Update stored event value to match
                self.event_vals[agent_id][event_id] = event_data
            else:
                # do nothing if the status hasn't changed
                pass

        # update data
        for data_id in self.data_to_display:
            try:
                display_data = data[data_id]
            except:
                # This data id is not in the message
                # this is fine
                continue
            # it shouldn't be None if there was something in the message, but just to double check
            if display_data is not None:
                if not agent_id in self.display_data_vals:
                    agent_display_vals = {data_id: display_data}
                    self.display_data_vals[agent_id] = agent_display_vals
                else:
                    self.display_data_vals[agent_id][data_id] = display_data

    def parse_proto_msg(self, msg):
        """Extract the agent id and deserialize the required data field into a dict"""
        agent_id = str(msg.id)
        msg_data = msg.data
        msg_data_dict = protobuf_to_dict(msg_data, use_enum_labels=True)
        self.update_display_data_from_dict(agent_id, msg_data_dict)

    def on_message_computer_helper(self, client, userdata, message):
        """Deserialize computer health protobuf message"""
        msg = pb_computer.ComputerHealth()
        msg.ParseFromString(message.payload)
        self.parse_proto_msg(msg)

    def on_message_radio_helper(self, client, userdata, message):
        """Deserialize radio information protobuf message"""
        msg = pb_radio.RadioInformation()
        msg.ParseFromString(message.payload)
        self.parse_proto_msg(msg)

    def on_message_vehicle_helper(self, client, userdata, message):
        """Deserialize vehicle information protobuf message"""
        msg = pb_vehicle.VehicleInformation()
        msg.ParseFromString(message.payload)
        self.parse_proto_msg(msg)

    def on_message_print_helper(self, client, userdata, message):
        print(message.payload)

    # Load data from a microservice sending a JSON packet
    def on_message_json(self, client, userdata, message):
        """Adds to q using put_nowait. Could error"""
        msg: Dict = json.loads(message.payload)

        agent_id = msg["id"]
        msg_data_dict = msg["data"]
        self.update_display_data_from_dict(agent_id, msg_data_dict)
        # TODO this currently assumes every event is associated with an agent


async def main(status_q: asyncio.Queue, data_to_display, broker_ip: str = "localhost"):
    logger = EventLogger(status_q, None, None, data_to_display, broker_ip=broker_ip)
    return logger


if __name__ == "__main__":
    main()
