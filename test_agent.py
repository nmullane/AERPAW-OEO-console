from typing import List
from agent import *
from computer_helper import ComputerHelper
from radio_helper import RadioHelper
from vehicle_helper import VehicleHelper, VehicleHelperMikuMode
import threading
import os
from argparse import ArgumentParser

def _launch_agents(n_portable: int=0, n_fixed: int=0, n_cloud: int=0, portable_addrs: List[str]=None):
    # Create some portable agents and the necessary helpers
    for i in range(n_portable):
        portable = PortableAgent(i)
        # vehicle_helper = VehicleHelper(port=PORT + i * 3)
        if portable_addrs is not None:
            vehicle_helper = VehicleHelperMikuMode(port=PORT + i * 3, downlink=portable_addrs[i])
        else:
            vehicle_helper = VehicleHelper(port=PORT + i * 3)
        computer_helper = ComputerHelper(port=PORT + i * 3 + 1)
        radio_helper = RadioHelper(port=PORT + i * 3 + 2)
        threading.Thread(target=portable.run).start()
        threading.Thread(target=vehicle_helper.run).start()
        threading.Thread(target=computer_helper.run).start()
        threading.Thread(target=radio_helper.run).start()


    # Create some fixed agents and the necessary helpers
    for i in range(n_portable, n_portable+n_fixed):
        fixed = FixedAgent(i)
        computer_helper = ComputerHelper(port=PORT + i * 3)
        radio_helper = RadioHelper(port=PORT + i * 3 + 1)
        threading.Thread(target=fixed.run).start()
        threading.Thread(target=computer_helper.run).start()
        threading.Thread(target=radio_helper.run).start()

    # Create some cloud agents and the necessary helpers
    for i in range(n_portable+n_fixed, n_portable+n_fixed+n_cloud):
        cloud = CloudAgent(i)
        computer_helper = ComputerHelper(port=PORT + i * 3)
        threading.Thread(target=cloud.run).start()
        threading.Thread(target=computer_helper.run).start()

    print("Finished launching agents")

if __name__ == "__main__":
    parser = ArgumentParser(description="test_agent - launch test agents for OEO")
    parser.add_argument("--n-portable", required=False, default=0, dest="n_portable")
    parser.add_argument("--n-fixed", required=False, default=0, dest="n_fixed")
    parser.add_argument("--n-cloud", required=False, default=0, dest="n_cloud")

    parser.add_argument("--use-sitl", required=False, default=None, dest="run_sitl_py",
            help="create sitl instances using run_sitl.py (if provided a path where run_sitl/the top level tooling dir is). this is a script in aerpawlib-tooling for dev testing")
    
    args, _ = parser.parse_known_args()

    vehicle_downlinks = []

    if args.run_sitl_py != None:
        base_launch_cmd = f"cd {args.run_sitl_py} && python run_sitl.py"

        launch_cmds = []
        exit_commands = []
        for vehicle_idx in range(int(args.n_portable)):
            v_prefix = f"oeotest_vehicle_{vehicle_idx}"
            launch_cmds.append(f"{base_launch_cmd} --sitl-instance {vehicle_idx+1} --screen-base {v_prefix}")
            exit_commands.extend([f"screen -S {v_prefix}_{service} -X quit" for service in ["sitl", "mavproxy"]])
            vehicle_downlinks.append(f"127.0.0.1:{14570 + 10*vehicle_idx}")

        for cmd in launch_cmds:
            os.system(cmd)
            print("--------------------")
            print("")
        
    _launch_agents(int(args.n_portable), int(args.n_fixed), int(args.n_cloud), portable_addrs=vehicle_downlinks)
    
    if args.run_sitl_py != None:
        print("press enter to quit:")
        input()
        for cmd in exit_commands:
            os.system(cmd)

    print("press ctrl-c to quit background threads")