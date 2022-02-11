from asyncio import events
import asyncio

from sqlalchemy import true

import console_event_logger

from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import HSplit, VSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.widgets import TextArea, Frame, Label
from prompt_toolkit.document import Document

from rich.console import Console
from rich.table import Table


def print_table_to_str(table) -> str:
    """Use rich to render the provided table using a dummy console.
    This is very hacky but seems to work so long as there is no color used."""
    console = Console(no_color=true)
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
    data_to_display = ["status", "velocity", "status"]
    def __init__(self):


async def main():
    # data type ids from agent statuses to display
    data_to_display = ["status", "velocity", "status"]
    # data_to_display = ["velocity"]
    # data_to_display = ["status"]

    ## Setup Keybindings
    kb = KeyBindings()

    @kb.add("c-d")
    def _exit(event):
        """
        Pressing Ctrl-Q will exit the user interface.

        Setting a return value means: quit the event loop that drives the user
        interface and return this value from the `Application.run()` call.
        """
        event.app.exit()

    def accept(buff):
        data_to_display = [input_field.text]
        logger.data_to_display = data_to_display

    events_table = create_events_table(data_to_display)

    output_field = Label(text="")
    output_field.text = print_table_to_str(events_table)

    events_field = TextArea(read_only=True, height=5, scrollbar=True, focusable=False)

    input_field = TextArea(
        height=1,
        prompt=">>> ",
        style="class:input-field",
        multiline=False,
        wrap_lines=False,
        focus_on_click=True,
    )
    input_field.accept_handler = accept

    root_container = HSplit(
        [
            events_field,
            # Display the text 'Hello world' on the top.
            output_field,
            # A horizontal line in the middle. We explicitly specify the height, to
            # make sure that the layout engine will not try to divide the whole
            # width by three for all these windows. The window will simply fill its
            # content by repeating this character.
            Window(height=1, char="-"),
            # One window that holds the BufferControl with the default buffer on
            # the bottom.
            input_field,
        ]
    )

    layout = Layout(root_container)

    app = Application(
        key_bindings=kb, layout=layout, full_screen=True, mouse_support=True
    )

    # TODO this isn't threadsafe
    def print_event(msg: str):
        events_field.text += "\n" + msg
        events_field.buffer._set_cursor_position(len(events_field.text))

    async def status_consumer():
        while True:
            agent_id, event_str = await logger.get_event()
            events_field.text += "\n" + event_str
            events_field.buffer._set_cursor_position(len(events_field.text))

    async def update_table():
        while True:
            # update the table content repeatedly
            await asyncio.sleep(0.5)
            status_to_table()
            app.invalidate()

    def status_to_table():
        """Convert agent statuses into data to be displayed in a live table"""
        # recreate events table
        # TODO update this to not have to update the entire table
        # doing this will require manipulating the cell data directly
        # for agent_id, status in logger.agent_statuses.items():
        #     print(status)
        #     for type in data_to_display:
        #         pass
        # return
        new_events_table = create_events_table(data_to_display)
        for agent_id, data_vals in logger.display_data_vals.items():
            vals = [val.__str__() for val in data_vals.values()]
            display_vals = []
            for data_id in data_to_display:
                try:
                    display_vals.append(str(data_vals[data_id]))
                except KeyError:
                    # TODO log this
                    print_event("KEY ERROR")
                    pass
            new_events_table.add_row(agent_id, *display_vals)

        # Get new table to display
        output_field.text = print_table_to_str(new_events_table)

    # start the event logger to publish events
    status_q = asyncio.Queue()
    logger = await console_event_logger.main(status_q, data_to_display)
    await logger.run()
    consumers = [asyncio.create_task(status_consumer()) for n in range(5)]
    table_updater = asyncio.create_task(update_table())
    await app.run_async()


if __name__ == "__main__":
    asyncio.run(main())
