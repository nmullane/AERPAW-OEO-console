from asyncio import events
import asyncio

from rich import print
from rich.layout import Layout
from rich.__main__ import make_test_card
from rich.console import Console, Group, group
from rich.panel import Panel
from rich.live import Live
from rich.table import Table

from console_event_logger import EventLogger

from prompt_toolkit import PromptSession
from prompt_toolkit.input import create_input
from prompt_toolkit.keys import Keys
from prompt_toolkit.patch_stdout import patch_stdout


import console_event_logger


# data type ids from agent statuses to display
data_to_display = ["status", "velocity", "status"]
# data_to_display = ["velocity"]
# data_to_display = ["status"]


def create_events_table():
    events_table = Table()
    events_table.add_column("ID")
    for data in data_to_display:
        events_table.add_column(data)
    return events_table


events_table = create_events_table()
display_str = "Subscribe: "


async def main():
    global events_table
    global display_str

    @group()
    def get_panels(table, disp_str):
        """Construct panels to display in console. Currently this is called to
        recreate the entire display on every update which should be improved."""
        yield Panel(table, style="on blue")
        yield Panel(disp_str, style="on red")

    # Create the first panel group
    panel_group = Panel(get_panels(events_table, display_str))
    with Live(panel_group, refresh_per_second=10) as live:

        def update_live():
            """Update the live display from the global variables"""
            global events_table, display_str
            live.update(Panel(get_panels(events_table, display_str)))

        # async def prompt_coroutine():
        #     session = PromptSession()
        #     while True:
        #         result = await session.prompt_async("Say something: ")
        #         # print(result)

        async def prompt_coroutine() -> None:
            done = asyncio.Event()
            input = create_input()

            def keys_ready():
                global display_str

                input_text = ""
                for key_press in input.read_keys():
                    # update display str and then live display
                    input_text += key_press.data
                    display_str += key_press.data
                    if key_press.key == Keys.Enter:
                        done.set()
                        display_str = "Subscribe: "
                    update_live()
                    if key_press.key == Keys.ControlC:
                        raise KeyboardInterrupt()
                return input_text

            with input.raw_mode():
                with input.attach(keys_ready):
                    while True:
                        await done.wait()
                        done.clear()

        async def status_consumer(q: asyncio.Queue):
            while True:
                agent_id, event_str = await logger.get_event()
                print("HI")
                print(event_str)

        def status_to_table():
            """Convert agent statuses into data to be displayed in a live table"""
            global events_table
            # recreate events table
            # TODO update this to not have to update the entire table
            # doing this will require manipulating the cell data directly
            # for agent_id, status in logger.agent_statuses.items():
            #     print(status)
            #     for type in data_to_display:
            #         pass
            # return
            new_events_table = create_events_table()
            for agent_id, data_vals in logger.display_data_vals.items():
                vals = [val.__str__() for val in data_vals.values()]
                new_events_table.add_row(agent_id, *vals)
            # Update global variable before updating live display
            events_table = new_events_table
            update_live()

        # start the event logger to publish events
        status_q = asyncio.Queue()
        logger = await console_event_logger.main(status_q, data_to_display)
        await logger.run()
        consumers = [asyncio.create_task(status_consumer(status_q)) for n in range(5)]
        # start the io handler
        prompt = asyncio.create_task(prompt_coroutine())

        while True:
            # update the table content repeatedly
            await asyncio.sleep(0.5)
            status_to_table()


if __name__ == "__main__":
    asyncio.run(main())
