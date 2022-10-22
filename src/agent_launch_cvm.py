from dataclasses import dataclass
from typing import List
from agent import *
from helper_computer import ComputerHelper
from helper_radio import RadioHelper
from helper_vehicle import VehicleHelper
import threading
import os
import time
import json
from argparse import ArgumentParser

DEFAULT_PORT = DEFAULT_BASE_AGENT_PORT  # 5550 from agent


@dataclass
class AgentConfig:
    """
    Agent config as parsed from file (ex below)
    {
        "helpers": {
            "vehicle": {"dronekit_link": "/dev/ttyACM0"},
            "radio": {},
            "computer": {}
        },
        "base_port": 17171,
        "id": "drone-1"
    }
    """

    oeo_server_ip: str = None
    agent_id: str = None
    base_port: int = DEFAULT_PORT

    vehicle_helper: bool = False
    dronekit_link: str = None

    radio_helper: bool = False

    computer_helper: bool = False

    def validate(self):
        if None in [self.agent_id, self.oeo_server_ip, self.base_port]:
            raise Exception(f"invalid AgentConfig provided: {self}")


@dataclass
class AgentConstruct:
    agent: Agent = None
    vehicle_helper: VehicleHelper = None
    computer_helper: ComputerHelper = None
    radio_helper: RadioHelper = None

    def start_threads(self):
        threading.Thread(target=self.agent.run).stat()
        for helper in [self.vehicle_helper, self.computer_helper, self.radio_helper]:
            if helper:
                threading.Thread(target=self.helper.run).start()


def generate_agent_from_config(config: AgentConfig) -> AgentConstruct:
    config.validate()

    agent = AgentConstruct()
    agent.agent = Agent(
        config.agent_id,
        vehicle_helper=config.vehicle_helper,
        vehicle_port=config.base_port + 1,
        computer_helper=config.computer_helper,
        computer_port=config.base_port + 2,
        radio_helper=config.radio_helper,
        radio_port=config.base_port + 3,
        broker=config.oeo_server_ip,
        mqtt_port=OEO_BROKER_PORT,
    )

    if config.vehicle_helper:
        agent.vehicle_helper = VehicleHelper(
            port=config.base_port,
            downlink=config.dronekit_link,
            id=f"{config.agent_id}",
        )
    if config.computer_helper:
        agent.computer_helper = ComputerHelper(port=config.base_port + 1)
    if config.radio_helper:
        agent.radio_helper = RadioHelper(port=config.base_port + 2)

    return agent


def _load_config_from_env() -> AgentConfig:
    """
    NOTE Expected environment variables to be set are below
    """
    config = AgentConfig()
    if "CVM_AGENT_ID" in os.environ:
        config.agent_id = os.environ["CVM_AGENT_ID"]
    if "CVM_AGENT_BASE_PORT" in os.environ:
        config.base_port = os.environ["CVM_AGENT_BASE_PORT"]
    if "CVM_AGENT_ENABLE_VEHICLE" in os.environ:
        config.vehicle_helper = True
        config.dronekit_link = os.environ["CVM_AGENT_VEHICLE_DRONEKIT_LINK"]
    if "CVM_AGENT_ENABLE_RADIO" in os.environ:
        config.radio_helper = True
    if "CVM_AGENT_ENABLE_COMPUTER" in os.environ:
        config.computer_helper = True
    return config


def _load_config(config_file: str) -> AgentConfig:
    with open(config_file, "r") as f:
        config_data = json.load(config_file)
        config = AgentConfig()

        helpers = config_data["helpers"]
        enabled_helpers = helpers.keys()
        if "vehicle" in enabled_helpers:
            config.vehicle_helper = True
            config.dronekit_link = helpers["vehicle"]["dronekit_link"]
        if "radio" in enabled_helpers:
            config.radio_helper = True
        if "computer" in enabled_helpers:
            config.computer_helper = True

        if "base_port" in config_data:
            config.base_port = config_data["base_port"]

        return config


if __name__ == "__main__":
    parser = ArgumentParser(
        description="cvm_agent - launch cvm agent helpers from config file"
    )
    parser.add_argument(
        "--config", required=False, dest="config_path", help="config file path"
    )

    args, _ = parser.parse_known_args()

    if args.config_path != None:
        config = _load_config(args["config_path"])
    else:
        # generate config from environment variables
        config = _load_config_from_env()
    agent = generate_agent_from_config(config)
    agent.start_threads()
