# defines a generic service class which all microservices will implement
import paho.mqtt.client as mqtt
import itertools

from typing import List
from abc import ABC, abstractmethod


class Service(ABC):
    def __init__(
        self,
        subs: List[mqtt.Client],
        sub_topics: List[str],
        pub: mqtt.Client,
        pub_topic: str,
        host: str = "localhost",
        port: int = 1883,
    ):
        """Default constructor for a microservice. This will connect every
        subscriber to mqtt and subscribe them to each topic.
        Specific on_message and other logic needs to be handled in each
        microservice implementation run function"""

        self.subs = subs
        self.pub = pub
        try:
            # try to subscribe to every topic in sub_topics
            for (sub, topic) in zip(subs, sub_topics):
                sub.connect(host, port)
                sub.subscribe(topic)
        except ConnectionRefusedError as e:
            print(e)
            raise Exception("MQTT not running!")

    @abstractmethod
    def run(self):
        pass
