## Example run

First make sure the mosquitto broker is running. Clone the repo here: https://github.com/nmullane/cedalo_platform and run `./start.sh`.

There are two main parts to running the OEO console. First is to run the console itself: `python3 console_cli.py`. Second is to launch some agents for the console to display data about: `python3 test_agent.py`. The test agent script will launch a few agents.

install reqs with pip install -r requirements.txt

## brief description of layout

* agent spawns helpers
* helpers sub to OEO topics
* helpers handle incoming messages / update protobuf
* helpers read directly from topic [!!! needs to be done through socket :(]
* helpers publish to internal socket
* agent links helpers to broker

## debugging tools

nmap mqtt integration: https://github.com/nmap/nmap/blob/master/scripts/mqtt-subscribe.nse

## launching mosquitto

requires mosquitto executable, distro-specific

use custom config file in this repo (mosquitto.conf)

`mosquitto -c mosquitto.conf`
