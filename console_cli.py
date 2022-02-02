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

        # start the event logger to publish events
        status_q = asyncio.Queue()
        logger = await console_event_logger.main(status_q)
        await logger.run()
        consumers = [asyncio.create_task(status_consumer(status_q)) for n in range(5)]

        while True:
            await asyncio.sleep(0.5)
            # recreate events table
            # TODO update this to not have to update the entire table
            # doing this will require manipulating the cell data directly
            new_events_table = create_events_table()
            for key, value in logger.agent_statuses.items():
                new_events_table.add_row(key, value)
            live.update(new_events_table)
        # await asyncio.sleep(4)

        # for i in range(12):
        #     print(f"Doing something #{i}")
        #     events_table.add_row(f"{i}: content so cool")
        #     time.sleep(0.4)


if __name__ == "__main__":
    asyncio.run(main())


# with Live(table, refresh_per_second=4) as live:  # update 4 times a second to feel fluid
#     for row in range(12):
#         live.console.print(f"Working on row #{row}")
#         time.sleep(0.4)
#         table.add_row(f"{row}", f"description {row}", "[red]ERROR")


# layout = Layout()

# layout.split_column(Layout(name="upper"), Layout(Console(), name="lower"))
# layout["upper"].ratio = 3
# layout["lower"].ratio = 1
# print(layout)

# console =
# with console.pager():
#     console.print(make_test_card())
