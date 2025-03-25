import os
from collections.abc import Callable

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
    """
    Decorator to register a function to be called when a specific on-chain event occurs.

    Args:
        event (Event): The event to listen for.
        network (type[Network]): The network on which the event is expected.
        start_block (int | BLOCK_STRINGS | None, optional): The block number to start listening from. Defaults to None.
        address (list[HexAddress] | HexAddress | None, optional): A single address or a list of addresses to filter the event. Defaults to None.
        addresses (list[HexAddress], optional): A list of addresses to filter the event. Defaults to an empty list.
        force_set_block (bool, optional): If True, forces the start block to be set even if an offset exists. Defaults to False.

    Returns:
        Callable: A decorator that registers the function to be called when the event occurs.
    """

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

    if (item is None and start_block is not None) or force_set_block:
        kv_store.set(f"{event.name}-{network}-offset", str(start_block))

    def wrapper(func: Callable[[Event], None]):
        onchain_hooks.add_thread(
            func,
            event,
            network,
        )
        return func

    return wrapper
