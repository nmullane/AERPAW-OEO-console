# microservice built to monitor the connection status of every agent
# subscribes to  cedalo/agent_status
# publishes to cedalo/connection_status
# for each agent publishes:
#   qualitative status (excellent, good, poor, disconnected)
#   numeric error rate (lost heartbeats)

from asyncio import events
from cProfile import run
import time
from typing import Dict, List, Tuple
import paho.mqtt.client as mqtt
import random
from threading import Thread
import asyncio
import json

from pytest import raises

from service import Service


class ConnectionStatusService(Service):
    """Service that subscribes to agent statuses and publishes connection
    status"""

    STATUSES = ["connected", "disconnected"]
    # timeout in seconds for how long without packets to determine we are disconnected
    DISCONNECT_TIMEOUT = 3

    def __init__(
        self,
        subs: List[mqtt.Client],
        sub_topics: List[str],
        pub: mqtt.Client,
        pub_topic: str,
        host: str = "localhost",
        port: int = 1883,
    ):
        if len(subs) != 1 or len(sub_topics) != 1:
            raise Exception(
                str(type(self)) + " expects one subscriber and publisher topic"
            )
        super().__init__(subs, sub_topics, pub, pub_topic, host, port)

    def run(self):
        # create custom name and handler for the one subscriber we use
        self.status_sub = self.subs[0]
        self.status_sub.on_message = self.on_message

        # initialize error rate and connection status list
        self.agent_data = {}
        # status data to publish
        self.pub_status_data = {}

        self.pub.loop_start()
        self.status_sub.loop_forever()

    def on_message(self, client, userdata, message):
        """"""
        msg: Dict = json.loads(message.payload)
        agent_id = msg["id"]
        msg_data = msg["data"]
        try:
            heartbeat_data = msg_data["heartbeat"]
        except:
            print("heartbeat not found")

        cur_time = time.time()
        if not agent_id in self.agent_data:
            # Create a new entry in the agent_data dict with error rate
            # initialized to 0, connection status "good" and current
            # heartbeat information
            self.agent_data[agent_id] = {
                "last_heartbeat_num": heartbeat_data,
                "last_heartbeat_time": cur_time,
            }
            self.pub_status_data[agent_id] = {
                "connection_status": self.STATUSES[0],
            }
        # update error rate if we have a new heartbeat
        else:
            if heartbeat_data == self.agent_data[agent_id]["last_heartbeat_num"]:
                print("We didn't get a new heartbeat number for some reason.")
            elif heartbeat_data != self.agent_data[agent_id]["last_heartbeat_num"] + 1:
                print(
                    "New heartbeat is not in sequence with the previous one for some reason."
                )
            else:
                agent_dict = self.agent_data[agent_id]
                pub_agent_dict = self.pub_status_data[agent_id]

                agent_dict["last_heartbeat_num"] = heartbeat_data
                agent_dict["last_heartbeat_time"] = cur_time

                # update connection status
                pub_agent_dict["connection_status"] = self.STATUSES[0]

        # Check time of last heartbeat received to find disconnected agents
        disconnect_cuttoff = time.time() - self.DISCONNECT_TIMEOUT
        for agent_id, agent_data in self.agent_data.items():
            if agent_data["last_heartbeat_time"] < disconnect_cuttoff:
                self.pub_status_data[agent_id]["connection_status"] = self.STATUSES[-1]

        # construct message to publish
        # TODO at the moment this is going to send a separate message for every agent
        # every time that it receives a message from any agent
        # this is a lot of extra pointless messages, but I need a way to send
        # a disconected message when we aren't getting messages from an agent
        # and this is the best way to do that at the moment
        for agent_id, status_dict in self.pub_status_data.items():
            self.pub.publish(
                self.pub_topic,
                json.dumps({"id": agent_id, "data": self.pub_status_data[agent_id]}),
            )
        # print(self.pub_status_data)


async def main():
    sub = mqtt.Client("connection_status_sub")
    pub = mqtt.Client("connection_status_pub")
    service = ConnectionStatusService(
        [sub], ["OEO/node_health"], pub, "OEO/connection_status"
    )
    service.run()


if __name__ == "__main__":
    asyncio.run(main())
