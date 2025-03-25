import os
from collections.abc import Awaitable, Callable

from eth_rpc import Event, set_alchemy_key
from eth_rpc.types import BLOCK_STRINGS, HexAddress, Network

from emp_hooks.utils import DynamoKeyValueStore

from .hooks import onchain_hooks


def on_event(
    event: Event,
    network: type[Network],
    start_block: int | BLOCK_STRINGS | None = None,
    address: list[HexAddress] | HexAddress | None = None,
    addresses: list[HexAddress] = [],
    force_set_block: bool = False,
):
    set_alchemy_key(os.environ["ALCHEMY_KEY"])
    kv_store = DynamoKeyValueStore()
    item = kv_store.get(f"{event.name}-{network}-offset")

    if address:
        if isinstance(address, str):
            addresses.append(address)
        else:
            addresses.extend(address)

    if addresses:
        event = event.set_filter(addresses=addresses)

    if (not item and start_block) or force_set_block:
        kv_store.set(f"{event.name}-{network}-offset", str(start_block))

    def wrapper(func: Callable[[Event], Awaitable[None] | None]):
        onchain_hooks.add_thread(
            func,
            event,
            network,
        )
        return func

    return wrapper
