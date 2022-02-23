from asyncio import events
import asyncio


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
commands = ["add", "del"]
data_completer = WordCompleter(["status", "velocity", "heartbeat"])


def print_table_to_str(table) -> str:
    """Use rich to render the provided table using a dummy console.
    This is very hacky but seems to work so long as there is no color used."""
    console = Console(no_color=True)
    console.begin_capture()
    console.print(table)
    return console.end_capture()


def create_events_table(data_to_display):
    events_table = Table(title=None, width=100, header_style=None, footer_style=None)
    events_table.add_column("ID")
    for data in data_to_display:
        events_table.add_column(data)
    return events_table


class CliApp:
    # data type ids from agent statuses to display
    data_to_display = []
    # data_to_display = ["status", "velocity", "heartbeat"]
    # data_to_display = ["velocity"]
    # data_to_display = ["status"]

    def accept(self, buff):
        self.data_to_display = [self.input_field.text]
        self.logger.data_to_display = self.data_to_display

    def __init__(self):
        ## Setup Keybindings
        # app keybinds
        self.kb = KeyBindings()
        # keybinds within input buffer
        self.buffer_kb = KeyBindings()

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

    async def run_app(self):
        # start the event logger to publish events
        status_q = asyncio.Queue()
        self.logger = await console_event_logger.main(status_q, self.data_to_display)
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
        new_events_table = create_events_table(self.data_to_display)
        for agent_id, data_vals in self.logger.display_data_vals.items():
            vals = [val.__str__() for val in data_vals.values()]
            display_vals = []
            for data_id in self.data_to_display:
                try:
                    display_vals.append(str(data_vals[data_id]))
                except KeyError:
                    # TODO log this
                    self.print_event("KEY ERROR")
                    pass
            new_events_table.add_row(agent_id, *display_vals)

        # Get new table to display
        self.output_field.text = print_table_to_str(new_events_table)


if __name__ == "__main__":
    app = CliApp()
    asyncio.run(app.run_app())
