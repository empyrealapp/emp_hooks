import os
from collections.abc import Awaitable, Callable

from eth_rpc import Event, set_alchemy_key
from eth_rpc.types import BLOCK_STRINGS, Network

from ..aws import DynamoKeyValueStore
from .hooks import onchain_hooks


def on_event(
    event: Event,
    network: type[Network],
    start_block: int | BLOCK_STRINGS | None = None,
):
    set_alchemy_key(os.environ["ALCHEMY_KEY"])
    kv_store = DynamoKeyValueStore()
    item = kv_store.get(f"{event.name}-{network}-offset")

    if not item and start_block:
        kv_store.set(f"{event.name}-{network}-offset", str(start_block))

    def wrapper(func: Callable[[Event], Awaitable[None] | None]):
        onchain_hooks.add_thread(
            func,
            event,
            network,
        )
        return func

    return wrapper
