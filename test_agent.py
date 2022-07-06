from agent import *
from computer_helper import ComputerHelper
from radio_helper import RadioHelper
from vehicle_helper import VehicleHelper
import threading


# Create some portable agents and the necessary helpers
for i in range(5):
    portable = PortableAgent(i)
    vehicle_helper = VehicleHelper(port=PORT + i * 3)
    computer_helper = ComputerHelper(port=PORT + i * 3 + 1)
    radio_helper = RadioHelper(port=PORT + i * 3 + 2)
    threading.Thread(target=portable.run).start()
    threading.Thread(target=vehicle_helper.run).start()
    threading.Thread(target=computer_helper.run).start()
    threading.Thread(target=radio_helper.run).start()


# Create some fixed agents and the necessary helpers
for i in range(5, 8):
    fixed = FixedAgent(i)
    computer_helper = ComputerHelper(port=PORT + i * 3)
    radio_helper = RadioHelper(port=PORT + i * 3 + 1)
    threading.Thread(target=fixed.run).start()
    threading.Thread(target=computer_helper.run).start()
    threading.Thread(target=radio_helper.run).start()

# Create some cloud agents and the necessary helpers
for i in range(8, 10):
    cloud = CloudAgent(i)
    computer_helper = ComputerHelper(port=PORT + i * 3)
    threading.Thread(target=cloud.run).start()
    threading.Thread(target=computer_helper.run).start()

print("Finished launching agents")
