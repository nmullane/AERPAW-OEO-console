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

    STATUSES = ["excellent", "good", "poor", "disconnected"]
    # error rate cutoffs for each status type
    STATUS_ERROR_CUTOFFS = [
        0.05,  # good > 5% error
        # 0.001,  # good > 5% error
        0.5,  # poor > 50% error
        1,  # disconnected = 100% error
    ]
    # timeout in seconds for how long without packets to determine we are disconnected
    DISCONNECT_TIMEOUT = 3
    # Window to compute the current error rate for
    ERROR_RATE_WINDOW = 10

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
                str(type(self)) + " expects one subscriber and subscriber topic"
            )
        super().__init__(subs, sub_topics, pub, pub_topic, host, port)

    def run(self):
        # create custom name and handler for subscriber
        self.status_sub = self.subs[0]
        self.status_sub.on_message = self.on_message

        # initialize error rate and connection status list
        self.agent_data = {}
        # status data to publish
        self.pub_status_data = {}

        self.status_sub.loop_forever()

    def on_message(self, client, userdata, message):
        """"""
        msg: Dict = json.loads(message.payload)
        for agent_id, status in msg.items():
            heartbeat_data = 0
            for data in status:
                if data["type"] == "heartbeat":
                    heartbeat_data = data["data"]
                    break

            cur_time = time.time()
            if not agent_id in self.agent_data:
                # Create a new entry in the agent_data dict with error rate
                # initialized to 0, connection status "good" and current
                # heartbeat information
                self.agent_data[agent_id] = {
                    "last_heartbeat_num": heartbeat_data,
                    "last_heartbeat_time": cur_time,
                    "errors": [(cur_time, 0)],
                }
                self.pub_status_data[agent_id] = {
                    "error_rate": 0,
                    "connection_status": self.STATUSES[1],
                }
            else:
                agent_dict = self.agent_data[agent_id]
                pub_agent_dict = self.pub_status_data[agent_id]

                last_heartbeat_num = agent_dict["last_heartbeat_num"]
                cur_errors = heartbeat_data - last_heartbeat_num - 1
                agent_dict["errors"].append((cur_time, cur_errors))

                errors_list: List[Tuple[int, int]] = agent_dict["errors"]
                errors_total = 0
                # Remove old errors and calculate moving average error rate
                # number of deleted items
                di = 0
                for i in range(len(errors_list)):
                    error_time, error_val = errors_list[i - di]
                    if error_time < cur_time - self.ERROR_RATE_WINDOW:
                        errors_list.pop(i - di)
                        di += 1
                    else:
                        errors_total += errors_list[i - di][1]

                # the error rate is equal to the number of errors that occured
                # divided by the number of entries in errors list plus the total
                # errors.
                # len(error_list) = num received heartbeats
                # errors_total = num missed heartbeats
                # error_rate = (num missed) / (num received + num_missed)
                error_rate = errors_total / (len(errors_list) + errors_total)
                agent_dict["last_heartbeat_num"] = heartbeat_data
                agent_dict["last_heartbeat_time"] = cur_time
                # TODO update connection status
                # TODO update connection status
                # TODO update connection status
                # TODO update connection status
                for i in range(len(self.STATUS_ERROR_CUTOFFS)):
                    if error_rate < self.STATUS_ERROR_CUTOFFS[i]:
                        pub_agent_dict["connection_status"] = self.STATUSES[i]
                        break

                pub_agent_dict["error_rate"] = error_rate

        # construct message to publish
        self.pub.publish(self.pub_topic, json.dumps(self.pub_status_data))
        print(self.pub_status_data)


async def main():
    sub = mqtt.Client("connection_status_sub")
    pub = mqtt.Client("connection_status_pub")
    service = ConnectionStatusService(
        [sub], ["cedalo/status"], pub, "cedalo/connection_status"
    )
    service.run()


if __name__ == "__main__":
    asyncio.run(main())
