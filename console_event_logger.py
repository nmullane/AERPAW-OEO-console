"""This file is responsible for subscribing to mqtt messages
and generating events to log based on the messages received"""

from asyncio import events
from typing import Dict, List
import paho.mqtt.client as mqtt
import random
from threading import Thread
import asyncio
import json


class Handlers:
    def __init__(self):
        self.handlers = {"heartbeat": self.heartbeat_handler}
        self.heartbeat_seq: Dict[str, int] = {}
        self.heartbeat_num_missed_lossy = 3
        self.heartbeat_num_missed_bad = 20

    def get_handlers(self):
        """Return the dict of event_id keys mapped to defined handlers"""
        return self.handlers

    def heartbeat_handler(self, agent_id: str, heartbeat: int):
        """Check for missed sequence numbers"""
        # add an entry to heartbeat_seq for this agent if one does not exist
        if not agent_id in self.heartbeat_seq:
            self.heartbeat_seq[agent_id] = heartbeat
        else:
            num_missed = heartbeat - self.heartbeat_seq[agent_id]
            if num_missed > self.heartbeat_num_missed_bad:
                return f"Bad Connection to {agent_id}"
            elif num_missed > self.heartbeat_num_missed_lossy:
                return f"Lossy Connection to {agent_id}"


class EventLogger(Thread):

    # data to parse and store for every agent
    data_to_display = []
    # dict of data values for every display data type for each agent
    # data is displayed in a live table
    display_data_vals = {}

    # data to look for changes as events
    event_data_types = ["status", "heartbeat"]

    # create instance of event handlers class
    handlers = Handlers()
    # get dict of event handlers
    event_handlers = handlers.get_handlers()

    # dict of values for all event types for each agent
    # changes in the stored values are printed as events
    event_vals = {}

    def __init__(
        self, sub: mqtt.Client, q: asyncio.Queue, table, live, data_to_display: List
    ):
        Thread.__init__(self)
        self.q = q
        self.sub = sub
        self.table = table
        self.live = live
        self.data_to_display = data_to_display

        try:
            self.sub.connect("localhost", 1883)
            self.sub.subscribe("OEO/status")
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
        self.sub.on_message = self.on_message
        self.sub.loop_start()

    def data_from_status(self, data_type: str, status: List):
        """Look through every data within the status message of an agent for
        the given data_type and return the associated data"""
        try:
            return status[data_type]
        except:
            print("key not found")
        # for dict in status:
        #     if dict["type"] == data_type:
        #         return dict["data"]

    def on_message(self, client, userdata, message):
        """Adds to q using put_nowait. Could error"""
        msg: Dict = json.loads(message.payload)

        # Look for events
        # TODO this currently assumes every event is associated with an agent
        for agent_id, msg_contents in msg.items():
            for event_id in self.event_data_types:
                event_data = self.data_from_status(event_id, msg_contents)

                # if a handler exists for this event, call the handler with the
                # agent id and the new data point
                if event_id in self.event_handlers:
                    event_data = self.event_handlers[event_id](agent_id, event_data)

                # add an entry to event vals for this agent if one does not exist
                if not agent_id in self.event_vals:
                    agent_event_vals = {event_id: event_data}
                    self.event_vals[agent_id] = agent_event_vals

                    # the initial value of the event is an event
                    # event = (agent_id, event_str)
                    event = (agent_id, f"Agent {agent_id} is now {event_data}")
                    self.q.put_nowait(event)
                # add an entry to the agent's event vals for this event_id if one does not exist
                elif not event_id in self.event_vals[agent_id]:
                    self.event_vals[agent_id][event_id] = event_data

                    # the initial value of the event is an event
                    # event = (agent_id, event_str)
                    event = (agent_id, f"Agent {agent_id} is now {event_data}")
                    self.q.put_nowait(event)
                elif self.event_vals[agent_id][event_id] != event_data:
                    # event = (agent_id, event_str)
                    event = (agent_id, f"Agent {agent_id} is now {event_data}")
                    self.q.put_nowait(event)
                    # Update stored event value to match
                    self.event_vals[agent_id][event_id] = event_data
                else:
                    # do nothing if the status hasn't changed
                    pass

        # update data
        for agent_id, msg_contents in msg.items():
            for data_id in self.data_to_display:
                display_data = self.data_from_status(data_id, msg_contents)
                if not agent_id in self.display_data_vals:
                    agent_display_vals = {data_id: display_data}
                    self.display_data_vals[agent_id] = agent_display_vals
                else:
                    self.display_data_vals[agent_id][data_id] = display_data

        # print(self.agent_statuses)


async def main(status_q: asyncio.Queue, data_to_display):
    sub = mqtt.Client("console_status_sub")
    logger = EventLogger(sub, status_q, None, None, data_to_display)
    return logger


if __name__ == "__main__":
    main()

# def on_message(client, userdata, message):
#     msg = json.loads(message.payload)

#     # Assume msg is a dictionary and pass in all
#     # key-value pairs to the AgentData constructor
#     # this will need to be error checked in the future
#     agent_statuses[msg["id"]] = msg["data"]
