import asyncio
import threading
from collections.abc import Awaitable, Callable
from concurrent.futures import Future

from eth_rpc import Event
from eth_rpc.types import Network
from pydantic import ConfigDict, Field, PrivateAttr

from ..aws import DynamoKeyValueStore
from ..types import Hook


async def event_generator(
    func: Callable[[Event], None | Awaitable[None]],
    event: Event,
    network: type[Network],
    stop_event: threading.Event,
    sleep_time: int = 8,
):
    while True:
        await _event_generator(func, event, network, stop_event)
        if stop_event.is_set():
            break
        print("SLEEPING")
        await asyncio.sleep(sleep_time)


async def _event_generator(
    func: Callable[[Event], None | Awaitable[None]],
    event: Event,
    network: type[Network],
    stop_event: threading.Event,
):
    print("LOAD KV STORE")
    kv_store = DynamoKeyValueStore()
    _offset_value = kv_store.get(f"{event.name}-{network}-offset")
    offset_value = int(_offset_value or "0")

    async for event_data in event[network].backfill(
        start_block=offset_value, step_size=2_000
    ):
        if stop_event.is_set():
            break

        print("RUN FUNC")
        if asyncio.iscoroutinefunction(func):
            await func(event_data)
        else:
            func(event_data)

        print("STORE CHECKPOINT")
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
    _thread: threading.Thread | None = PrivateAttr(default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def add_thread(
        self,
        func,
        event: Event,
        network: type[Network],
    ):
        if self.loop is None:
            self.loop = asyncio.new_event_loop()
            # Start the loop in a separate thread
            self._thread = threading.Thread(target=self._run_event_loop, daemon=False)
            self._thread.start()

        # Create task in the loop
        future = asyncio.run_coroutine_threadsafe(
            event_generator(func, event, network, self.stop_event), self.loop
        )
        self.futures.append(future)

    def _run_event_loop(self):
        # asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_forever()
        finally:
            # Close the event loop when run_forever() exits
            self.loop.close()

    def set_stop_event(self):
        self.stop_event.set()

    def stop(self, timeout: int = 5):
        self.set_stop_event()  # Set stop event first
        for task in self.futures:
            task.cancel()
        if self.loop is not None:
            # Schedule loop.stop() from within the loop
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self._thread:
            self._thread.join(timeout)
        self.loop = None


onchain_hooks = OnchainHooks()
