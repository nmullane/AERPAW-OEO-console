sudo systemctl stop mosquitto
 ./start.sh

## Example run
First make sure the mosquitto broker is running. Clone the repo here: https://github.com/nmullane/cedalo_platform and run `./start.sh`.

There are two main parts to running the OEO console. First is to run the console itself: `python3 console_cli.py`. Second is to launch some agents for the console to display data about: `python3 test_agent.py`. The test agent script will launch a few agents.