import threading
import time
from collections.abc import Callable
from datetime import datetime, timezone

from pydantic import ConfigDict, Field, PrivateAttr

from ..aws import DynamoKeyValueStore
from ..types import Hook


def _cron_function(
    func,
    cron_string: str,
    identifier: str,
    stop_event: threading.Event,
    sleep_time: int = 3,
):
    from croniter import croniter

    kv_store = DynamoKeyValueStore()
    last_run = kv_store.get(f"scheduled-{identifier}")
    if not last_run:
        raise ValueError(f"No last run value found for {identifier}")
    last_run_value = float(last_run)

    while not stop_event.is_set():
        now = datetime.now(timezone.utc)
        cron = croniter(cron_string, last_run_value)
        next_run = cron.get_next(datetime)

        if next_run <= now:
            func()
            last_run = str(now.timestamp())
            kv_store.set(f"scheduled-{identifier}", last_run)

        time.sleep(sleep_time)


def _interval_function(
    func: Callable[[], None],
    execution_frequency: int,
    identifier: str,
    stop_event: threading.Event,
    sleep_time: int = 3,
):
    kv_store = DynamoKeyValueStore()
    last_run = kv_store.get(f"scheduled-{identifier}")
    last_run_value = float(last_run or "0")

    while not stop_event.is_set():
        now = datetime.now(timezone.utc).timestamp()
        if last_run_value + execution_frequency < now:
            func()
            last_run_value = now
            kv_store.set(f"scheduled-{identifier}", str(last_run_value))
        time.sleep(sleep_time)


class ScheduledHooks(Hook):
    stop_event: threading.Event = Field(default_factory=threading.Event)
    _threads: list[threading.Thread] = PrivateAttr(default_factory=list)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def add_scheduled_function(
        self,
        func,
        identifier: str,
        execution_frequency: int | str,
        execute_on_start: bool = False,
    ):
        kv_store = DynamoKeyValueStore()
        if not kv_store.get(f"scheduled-{identifier}"):
            if execute_on_start:
                kv_store.set(f"scheduled-{identifier}", str(0))
            else:
                now = datetime.now(timezone.utc).timestamp()
                kv_store.set(f"scheduled-{identifier}", str(now))

        thread_target: Callable
        if isinstance(execution_frequency, str):
            thread_target = _cron_function
        else:
            thread_target = _interval_function

        thread = threading.Thread(
            target=thread_target,
            args=(func, execution_frequency, identifier, self.stop_event),
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


scheduled_hooks = ScheduledHooks()
