import json
from typing import List


class Data:
    def __init__(self, type, data):
        self.type = type
        self.data = data


class AgentData:
    """Class for encoding arbitrary data in a unified JSON format"""

    def __init__(self, id, data: List[Data]):
        self.id = id
        self.data = [d.__dict__ for d in data]

    def to_json(self):
        return json.dumps(self.__dict__)


# The design of this will depend on how sophisticated this needs to be
# This could be more heavily integrated into the server design with
# a connected database and storing and retrieving lots of data or
# this could be as simple as a list of each message, or a dict with
# timestamp as the keys and the messages as the values

# class AgentDataLog:
#     """Class for storing every data message sent by an agent"""

#     def __init__(self, id):
#         self.data_log = []

#     def add(self, new_data):
#         self.data_log.append(new_data)


if __name__ == "__main__":
    data = [
        Data("status", "armed"),
        Data("velocity", [0.0, 1.0, 0.6]),
        Data("name", "Niall's Favorite Drone"),
    ]
    print(json.dumps(AgentData("1", data).__dict__))
