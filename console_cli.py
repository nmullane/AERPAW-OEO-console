from asyncio import events
from re import A
from rich import print
from rich.layout import Layout
from rich.__main__ import make_test_card
from rich.console import Console, Group

import time
from rich.live import Live
from rich.table import Table

from console_event_logger import EventLogger
import console_event_logger
import asyncio


def create_events_table():
    events_table = Table()
    events_table.add_column("ID")
    events_table.add_column("Status")
    return events_table


events_table = create_events_table()


async def main():
    global events_table
    with Live(events_table, refresh_per_second=4) as live:

        async def status_consumer(q: asyncio.Queue):
            while True:
                agent_id, event_str = await logger.get_event()

                print(event_str)

        # data type ids from agent statuses to display
        data_to_display = ["status", "velocity"]

        def data_from_status(data_type: str, status):
            print(status)

        def status_to_table():
            """Convert agent statuses into data to be displayed in a live table"""
            # recreate events table
            # TODO update this to not have to update the entire table
            # doing this will require manipulating the cell data directly
            for agent_id, status in logger.agent_statuses.items():
                print(status)
                for type in data_to_display:
                    pass
            return
            new_events_table = create_events_table()
            for key, value in logger.agent_statuses.items():
                new_events_table.add_row(key, value)
            live.update(new_events_table)

        # start the event logger to publish events
        status_q = asyncio.Queue()
        logger = await console_event_logger.main(status_q)
        await logger.run()
        consumers = [asyncio.create_task(status_consumer(status_q)) for n in range(5)]

        while True:
            # update the table content repeatedly
            await asyncio.sleep(0.5)
            status_to_table()


if __name__ == "__main__":
    asyncio.run(main())
