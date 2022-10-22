# TODO this generally works when run on a local machine, but breaks on ssh terminals/remote sessions
# is there a better framework that we could use to make the GUI?

from argparse import ArgumentParser
from asyncio import events
import asyncio
import json
import zmq
import zmq.asyncio
import paho.mqtt.client as mqtt
import re

import console_event_logger

from prompt_toolkit import Application, PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import (
    HSplit,
    VSplit,
    Window,
    FloatContainer,
    Float,
)
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.widgets import TextArea, Frame, Label
from prompt_toolkit.document import Document

from rich.console import Console
from rich.table import Table

# the autocompleter words
commands = ["add", "del", "command"]
data_completer = WordCompleter(
    [
        "status",
        "velocity",
        "heartbeat",
        "error_rate",
        "connection_status",
        "latitude",
        "longitude",
        "battery_voltage",
        "battery_current",
        "battery_percent",
        "radio_status",
        "altitude",
        "vehicle_script_running",
        "E-VM_script_running",
        "cpu_utilization",
        "memory_utilization",
    ]
)


def print_table_to_str(table) -> str:
    """Use rich to render the provided table using a dummy console.
    This is very hacky but seems to work so long as there is no color used."""
    console = Console(no_color=True)
    console.begin_capture()
    console.print(table)
    return console.end_capture()


def create_events_table(data_to_display):
    """Create a Rich Table with a column for every data id specified in the list
    data_to_display. Returns the created table that can now be filled with data."""
    events_table = Table(title=None, width=100, header_style=None, footer_style=None)
    events_table.add_column("ID")
    for data in data_to_display:
        events_table.add_column(data)
    return events_table


def _serialize_command(id, verb, params):
    _serialize_arm_solo_data = lambda _: {}
    _serialize_disarm_data = lambda _: {}
    _serialize_mode_data = lambda params: {"mode": params[0]}
    _serialize_rtl_data = lambda _: {}
    _serialize_takeoff_data = lambda params: {"altitude": int(params[0])}

    data_serializer = {
        "arm": _serialize_arm_solo_data,
        "disarm": _serialize_disarm_data,
        "mode": _serialize_mode_data,
        "rtl": _serialize_rtl_data,
        "takeoff": _serialize_takeoff_data,
    }.get(verb, None)

    if data_serializer is None:
        return None
    return {
        "node_id": id,
        "verb": verb,
        "data": data_serializer(params),
    }


class CliApp:
    # data type ids from agent statuses to display
    data_to_display = []

    def accept(self, buff):
        self.data_to_display = [self.input_field.text]
        self.logger.data_to_display = self.data_to_display

    def __init__(self):
        ## Setup Keybindings
        # app keybinds
        self.kb = KeyBindings()
        # keybinds within input buffer
        self.buffer_kb = KeyBindings()

        self.mqtt_client = None

        self.connected_agents = {}  # id: {idk}

        @self.kb.add("c-d")
        def _exit(event):
            """
            Pressing Ctrl-Q will exit the user interface.

            Setting a return value means: quit the event loop that drives the user
            interface and return this value from the `Application.run()` call.
            """
            event.app.exit()

        @self.buffer_kb.add("c-m")
        def _handle_input(event):
            buf: BufferControl = self.input_field.content

            input_text = buf.buffer.text
            cmds = input_text.split()

            def _handle_command(agent, cmds):
                try:
                    _, verb = cmds[1:3]
                    params = cmds[3:]
                    serialized = _serialize_command(agent, verb, params)
                    if serialized == None:
                        self.print_event("INPUT COMMAND INVALID")
                        return
                    self.mqtt_client.publish(
                        "OEO/vehicle_command", json.dumps(serialized)
                    )
                except Exception as e:
                    print(e)

            if len(cmds) < 2:
                self.print_event("INPUT COMMAND MUST INCLUDE AN ARGUMENT")
                return

            if cmds[0] == "add":
                self.data_to_display += [cmds[1]]
            elif cmds[0] == "del":
                try:
                    self.data_to_display.remove(cmds[1])
                except:
                    # TODO log the error
                    pass
            elif cmds[0] == "command":
                _handle_command(cmds[1], cmds)
            elif cmds[0] == "all":
                # forward command to all agents
                for agent_id in self.logger.display_data_vals.keys():
                    _handle_command(agent_id, [""] + cmds)
            else:
                # default to assuming that it's a command with a preceding vehicle identifier
                for agent_id in self.logger.display_data_vals.keys():
                    if agent_id == cmds[0]:
                        cmds_extend = [""] + cmds
                        _handle_command(agent_id, cmds_extend)
                        break

            self.logger.data_to_display = self.data_to_display
            # reset buffer contents
            buf.buffer.reset()

        self.events_table = create_events_table(self.data_to_display)

        # The input buffer with autocompletion
        self.buffer = Buffer(completer=data_completer, complete_while_typing=True)

        self.output_field = Label(text="")
        self.output_field.text = print_table_to_str(self.events_table)

        self.events_field = TextArea(
            read_only=True, scrollbar=True, focusable=False, height=10
        )

        self.input_field = Window(
            BufferControl(buffer=self.buffer, key_bindings=self.buffer_kb),
            height=1,
            dont_extend_height=True,
            ignore_content_height=True,
        )
        # self.input_field = TextArea(
        #     height=1,
        #     prompt=">>> ",
        #     style="class:input-field",
        #     multiline=False,
        #     wrap_lines=False,
        #     focus_on_click=True,
        # )
        # self.input_field.accept_handler = self.accept

        root_container = FloatContainer(
            content=HSplit(
                [
                    self.events_field,
                    # Display the text 'Hello world' on the top.
                    self.output_field,
                    # A horizontal line in the middle. We explicitly specify the height, to
                    # make sure that the layout engine will not try to divide the whole
                    # width by three for all these windows. The window will simply fill its
                    # content by repeating this character.
                    Window(height=1, char="-"),
                    # One window that holds the BufferControl with the default buffer on
                    # the bottom.
                    self.input_field,
                ]
            ),
            floats=[
                Float(
                    xcursor=True,
                    ycursor=True,
                    content=CompletionsMenu(max_height=5, scroll_offset=1),
                )
            ],
        )

        self.layout = Layout(root_container)

        self.app = Application(
            key_bindings=self.kb,
            layout=self.layout,
            full_screen=True,
            mouse_support=True,
        )

    async def run_app(self, broker_ip: str = "localhost"):
        # start the event logger to publish events

        self.broker = broker_ip
        self.port = 1883
        self.mqtt_client = mqtt.Client(f"oeo_vehicle_cmd_pub")
        self.mqtt_client.connect(self.broker, self.port)
        self.mqtt_client.loop_start()

        status_q = asyncio.Queue()
        self.logger = await console_event_logger.main(
            status_q, self.data_to_display, broker_ip=self.broker
        )
        await self.logger.run()
        consumers = [asyncio.create_task(self.status_consumer()) for n in range(5)]
        table_updater = asyncio.create_task(self.update_table())
        app = asyncio.create_task(self.app.run_async())
        await app
        # session = PromptSession()
        # x = await session.prompt_async()
        # self.print_event(x)

    # TODO this isn't threadsafe
    def print_event(self, msg: str):
        self.events_field.text += "\n" + msg
        self.events_field.buffer._set_cursor_position(len(self.events_field.text))

    async def status_consumer(self):
        while True:
            agent_id, event_str = await self.logger.get_event()
            self.events_field.text += "\n" + event_str
            self.events_field.buffer._set_cursor_position(len(self.events_field.text))

    async def update_table(self):
        while True:
            # update the table content repeatedly
            await asyncio.sleep(0.5)
            self.status_to_table()
            self.app.invalidate()

    def status_to_table(self):
        """Convert agent statuses into data to be displayed in a live table"""
        # recreate events table
        # TODO update this to not have to update the entire table
        # doing this will require manipulating the cell data directly
        # for agent_id, status in logger.agent_statuses.items():
        #     print(status)
        #     for type in data_to_display:
        #         pass
        # return

        # Sort the agent ids to display the table in a consistent order
        # TODO this sorting is done in a hacky way
        # Create an empty table with the necessary columns
        new_events_table = create_events_table(self.data_to_display)
        agent_ids = list(map(lambda id: int(id), self.logger.display_data_vals.keys()))
        agent_ids.sort()
        agent_ids = [str(id) for id in agent_ids]
        for agent_id in agent_ids:
            data_vals = self.logger.display_data_vals[agent_id]
            vals = [val.__str__() for val in data_vals.values()]
            display_vals = []
            for data_id in self.data_to_display:
                try:
                    display_vals.append(str(data_vals[data_id]))
                except KeyError:
                    # if there isn't a data val for this agent_id and data_id
                    # append empty string to the table to maintain proper ordering
                    display_vals.append("")
                    # TODO log this
                    # self.print_event("KEY ERROR")
                    pass
            new_events_table.add_row(agent_id, *display_vals)

        # Get new table to display
        self.output_field.text = print_table_to_str(new_events_table)


if __name__ == "__main__":
    parser = ArgumentParser(description="console CLI tool for aerpaw oeo")
    parser.add_argument(
        "--broker-ip",
        required=False,
        dest="broker_ip",
        help="broker ip address (defaults to localhost)",
        default="localhost",
    )
    args, _ = parser.parse_known_args()

    app = CliApp()
    asyncio.run(app.run_app(broker_ip=args.broker_ip))
