import os
from collections.abc import Callable

from eth_rpc import Event, set_alchemy_key
from eth_rpc.event import IGNORE, IGNORE_VAL
from eth_rpc.types import BLOCK_STRINGS, HexAddress, Network
from eth_typing import HexStr

from emp_hooks.utils import DynamoKeyValueStore, MockDynamoKeyValueStore

from .hooks import onchain_hooks


def on_event(
    event: Event,
    network: type[Network],
    start_block: int | BLOCK_STRINGS | None = None,
    address: list[HexAddress] | HexAddress | None = None,
    addresses: list[HexAddress] = [],
    topic1: list[HexStr] | HexStr | IGNORE = IGNORE_VAL,
    topic2: list[HexStr] | HexStr | IGNORE = IGNORE_VAL,
    topic3: list[HexStr] | HexStr | IGNORE = IGNORE_VAL,
    subscribe: bool = False,
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
        topic1 (list[HexStr] | HexStr | IGNORE, optional): A single topic or a list of topics to filter for topic1 on the event. Defaults to IGNORE.
        topic2 (list[HexStr] | HexStr | IGNORE, optional): A single topic or a list of topics to filter for topic2 on the event. Defaults to IGNORE.
        topic3 (list[HexStr] | HexStr | IGNORE, optional): A single topic or a list of topics to filter for topic3 on the event. Defaults to IGNORE.
        force_set_block (bool, optional): If True, forces the start block to be set even if an offset exists. Defaults to False.

    Returns:
        Callable: A decorator that registers the function to be called when the event occurs.
    """

    set_alchemy_key(os.environ["ALCHEMY_KEY"])
    if os.environ.get("ENVIRONMENT") == "testing":
        kv_store = MockDynamoKeyValueStore()
    else:
        kv_store = DynamoKeyValueStore()
    item = kv_store.get(f"{event.name}-{network}-offset")

    if address:
        if isinstance(address, str):
            addresses.append(address)
        else:
            addresses.extend(address)

    if addresses:
        event = event.set_filter(
            addresses=addresses,
            topic1=topic1,
            topic2=topic2,
            topic3=topic3,
        )

    if (item is None and start_block is not None) or force_set_block:
        kv_store.set(f"{event.name}-{network}-offset", str(start_block))

    def wrapper(func: Callable[[Event], None]):
        onchain_hooks.add_thread(
            func,
            event,
            network,
            subscribe=subscribe,
        )
        return func

    return wrapper
