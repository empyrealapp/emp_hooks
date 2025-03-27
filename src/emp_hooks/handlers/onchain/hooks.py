import asyncio
import threading
import time
from collections.abc import Callable
from concurrent.futures import Future

from eth_rpc import Event
from eth_rpc.types import Network
from pydantic import ConfigDict, Field, PrivateAttr

from emp_hooks.logger import log
from emp_hooks.types import Hook
from emp_hooks.utils import DynamoKeyValueStore


def event_generator(
    func: Callable[[Event], None],
    event: Event,
    network: type[Network],
    stop_event: threading.Event,
    subscribe: bool = False,
    sleep_time: int = 8,
):
    while True:
        if subscribe:
            _event_subscriber(func, event, network, stop_event)
        else:
            _event_generator(
                func,
                event,
                network,
                stop_event,
            )
        if stop_event.is_set():
            break
        time.sleep(sleep_time)


def _event_subscriber(
    func: Callable[[Event], None],
    event: Event,
    network: type[Network],
    stop_event: threading.Event,
):
    """
    Subscribes to the event and calls the function for each event.
    """
    for event_data in event[network].sync.subscribe():
        if stop_event.is_set():
            break

        func(event_data)


def _event_generator(
    func: Callable[[Event], None],
    event: Event,
    network: type[Network],
    stop_event: threading.Event,
):
    """
    Backfills from the last block and calls the function for each event.
    """
    kv_store = DynamoKeyValueStore()
    _offset_value = kv_store.get(f"{event.name}-{network}-offset")
    offset_value = int(_offset_value or "0")

    log.info("Backfilling from block: %s", offset_value)

    for event_data in event[network].sync.backfill(
        start_block=offset_value,
    ):
        if stop_event.is_set():
            break

        func(event_data)

        if event_data.log.block_number != offset_value:
            _offset_value = str(event_data.log.block_number)
            kv_store.set(f"{event.name}-{network}-offset", _offset_value)
            offset_value = int(_offset_value)

    _offset_value = str(event_data.log.block_number)
    kv_store.set(f"{event.name}-{network}-offset", _offset_value)


class OnchainHooks(Hook):
    name: str = Field(default="Onchain Hooks")

    futures: list[Future] = Field(default_factory=list)
    loop: asyncio.AbstractEventLoop | None = Field(default=None)
    _threads: list[threading.Thread] = PrivateAttr(default_factory=list)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def add_thread(
        self,
        func,
        event: Event,
        network: type[Network],
        subscribe: bool = False,
    ):
        thread = threading.Thread(
            target=event_generator,
            args=(func, event, network, self._stop_event, subscribe),
            daemon=True,
        )
        thread.start()
        self._threads.append(thread)

    def stop(self, timeout: int = 5):
        for thread in self._threads:
            thread.join(timeout)


onchain_hooks = OnchainHooks()
