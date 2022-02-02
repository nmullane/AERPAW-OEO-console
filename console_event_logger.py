"""This file is responsible for subscribing to mqtt messages
and generating events to log based on the messages received"""

from asyncio import events
from typing import Dict, List
import paho.mqtt.client as mqtt
import random
from threading import Thread
import asyncio
import json


class EventLogger(Thread):
    agent_statuses = {}
    # data to parse and store for every agent
    data_to_display = ["status", "velocity"]
    # data to look for changes as events
    event_data_types = ["status"]
    # dict of values for all event types for each agent
    # changes in the stored values are printed as events
    event_vals = {}

    def __init__(self, sub: mqtt.Client, q: asyncio.Queue, table, live):
        Thread.__init__(self)
        self.q = q
        self.sub = sub
        self.table = table
        self.live = live

        self.sub.connect("localhost", 1883)
        self.sub.subscribe("cedalo/status")

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
        for dict in status:
            if dict["type"] == data_type:
                return dict["data"]

    def on_message(self, client, userdata, message):
        """Adds to q using put_nowait. Could error"""
        msg: Dict = json.loads(message.payload)

        # Look for events
        # TODO this currently assumes every event is associated with an agent
        for agent_id, status in msg.items():
            for event_id in self.event_data_types:
                event_data = self.data_from_status(event_id, status)
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

        # print(self.agent_statuses)


async def main(status_q: asyncio.Queue):
    sub = mqtt.Client("console_status_sub")
    logger = EventLogger(sub, status_q, None, None)
    return logger


if __name__ == "__main__":
    main()

# def on_message(client, userdata, message):
#     msg = json.loads(message.payload)

#     # Assume msg is a dictionary and pass in all
#     # key-value pairs to the AgentData constructor
#     # this will need to be error checked in the future
#     agent_statuses[msg["id"]] = msg["data"]
