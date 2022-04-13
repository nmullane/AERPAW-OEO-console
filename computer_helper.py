import proto.computer_health_pb2 as pb
import random


class ComputerHelper:
    """Dummy class to create data as if it was a computer helper"""

    def __init__(self):
        self.heartbeat = 0
        self.health_message_data = pb.ComputerHealthData()

    def get_message(self):
        self.heartbeat += 1

        self.health_message_data.heartbeat = self.heartbeat
        # random cpu between 0% and 40%
        self.health_message_data.cpu_utilization = random.random() * 40
        # random memory between 20% and 50%
        self.health_message_data.memory_utilization = random.random() * 30 + 20

        self.health_message_data.vehicle_script_running = False
        self.health_message_data.evm_script_running = True
