"""This file is responsible for subscribing to mqtt messages
and generating events to log based on the messages received"""

from typing import Dict
import paho.mqtt.client as mqtt
import random
from threading import Thread
import asyncio
import json


class EventLogger(Thread):
    agent_statuses = {}

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

    def on_message(self, client, userdata, message):
        """Adds to q using put_nowait. Could error"""
        msg: Dict = json.loads(message.payload)

        # Assume msg is a dictionary and pass in all
        # key-value pairs to the AgentData constructor
        # this will need to be error checked in the future
        # self.agent_statuses[msg["id"]] = msg["data"]
        for key, value in msg.items():
            # TODO this needs to be more generalized
            status = value[0]["data"]
            if not key in self.agent_statuses:
                # event = (agent_id, event_str)
                event = (key, f"Agent {key} is now CONNECTED and {status}")
                # print(event)
                self.q.put_nowait(event)
                # Update stored status to match
                self.agent_statuses[key] = status
            elif self.agent_statuses[key] != status:
                # event = (agent_id, event_str)
                event = (key, f"Agent {key} is now {status}")
                # print(event)
                self.q.put_nowait(event)
                # Update stored status to match
                self.agent_statuses[key] = status
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
