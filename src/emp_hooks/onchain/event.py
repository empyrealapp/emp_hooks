import asyncio
import os
from collections.abc import Awaitable, Callable
from threading import Thread

from eth_rpc import Event, set_alchemy_key
from eth_rpc.types import BLOCK_STRINGS, Network

from ..aws import DynamoKeyValueStore


async def event_generator(
    func: Callable[[Event], None | Awaitable[None]],
    event: Event,
    network: type[Network],
    sleep_time: int = 8,
):
    while True:
        await _event_generator(func, event, network)
        await asyncio.sleep(sleep_time)


async def _event_generator(
    func: Callable[[Event], None | Awaitable[None]],
    event: Event,
    network: type[Network],
):
    kv_store = DynamoKeyValueStore()
    offset_value = kv_store.get(f"{event.name}-{network}-offset")

    async for event_data in event[network].backfill(start_block=offset_value):
        if asyncio.iscoroutinefunction(func):
            await func(event_data)
        else:
            func(event_data)

        if event_data.log.block_number != offset_value:
            offset_value = str(event_data.log.block_number)
            kv_store.set(f"{event.name}-{network}-offset", str(offset_value))

    offset_value = str(event_data.log.block_number)
    kv_store.set(f"{event.name}-{network}-offset", str(offset_value))


def on_event(
    event: Event,
    network: type[Network],
    start_block: int | BLOCK_STRINGS | None = None,
    daemon: bool = False,
):
    set_alchemy_key(os.environ["ALCHEMY_KEY"])
    kv_store = DynamoKeyValueStore()
    item = kv_store.get(f"{event.name}-{network}-offset")

    if not item and start_block:
        kv_store.set(f"{event.name}-{network}-offset", str(start_block))

    def wrapper(func: Callable[[Event], Awaitable[None] | None]):
        thread = Thread(
            target=asyncio.run,
            args=(event_generator(func, event, network),),
            daemon=daemon,  # keep the program running until the hook is stopped
        )
        thread.start()

        return func

    return wrapper
