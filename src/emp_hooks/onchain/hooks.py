import asyncio
import threading
import time
from collections.abc import Callable
from concurrent.futures import Future

from eth_rpc import Event
from eth_rpc.types import Network
from pydantic import ConfigDict, Field, PrivateAttr

from ..aws import DynamoKeyValueStore
from ..types import Hook


def event_generator(
    func: Callable[[Event], None],
    event: Event,
    network: type[Network],
    stop_event: threading.Event,
    sleep_time: int = 8,
):
    while True:
        _event_generator(func, event, network, stop_event)
        if stop_event.is_set():
            break
        time.sleep(sleep_time)


def _event_generator(
    func: Callable[[Event], None],
    event: Event,
    network: type[Network],
    stop_event: threading.Event,
):
    kv_store = DynamoKeyValueStore()
    _offset_value = kv_store.get(f"{event.name}-{network}-offset")
    offset_value = int(_offset_value or "0")

    for event_data in event[network].sync.backfill(
        start_block=offset_value, step_size=2_000
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
    stop_event: threading.Event = Field(default_factory=threading.Event)
    futures: list[Future] = Field(default_factory=list)
    loop: asyncio.AbstractEventLoop | None = Field(default=None)
    _threads: list[threading.Thread] = PrivateAttr(default_factory=list)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def add_thread(
        self,
        func,
        event: Event,
        network: type[Network],
    ):
        thread = threading.Thread(
            target=event_generator,
            args=(func, event, network, self.stop_event),
            daemon=False,
        )
        thread.start()
        self._threads.append(thread)

    def set_stop_event(self):
        self.stop_event.set()

    def stop(self, timeout: int = 5):
        self.set_stop_event()
        for thread in self._threads:
            thread.join(timeout)


onchain_hooks = OnchainHooks()
