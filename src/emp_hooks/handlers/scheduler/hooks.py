import threading
import time
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from croniter import croniter
from pydantic import ConfigDict, Field, PrivateAttr

from emp_hooks.logger import log
from emp_hooks.types import Hook
from emp_hooks.utils import DynamoKeyValueStore


def _cron_function(
    func: Callable[[], Any],
    cron_string: str,
    identifier: str,
    stop_event: threading.Event,
    sleep_time: int = 3,
):
    kv_store = DynamoKeyValueStore()
    last_run = kv_store.get(f"scheduled-{identifier}")
    if not last_run:
        raise ValueError(f"No last run value found for {identifier}")
    last_run_value: float = float(last_run)

    while not stop_event.is_set():
        now: datetime = datetime.now(timezone.utc)
        cron = croniter(cron_string, last_run_value)
        next_run: datetime = cron.get_next(datetime).replace(tzinfo=timezone.utc)

        if next_run <= now:
            log.info("Running scheduled function: %s", identifier)
            func()
            last_run_value = next_run.timestamp()
            last_run = str(last_run_value)
            kv_store.set(f"scheduled-{identifier}", last_run)

        time.sleep(sleep_time)


def _interval_function(
    func: Callable[[], Any],
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
            log.info("Running scheduled function: %s", identifier)
            func()
            last_run_value = now
            kv_store.set(f"scheduled-{identifier}", str(last_run_value))
        time.sleep(sleep_time)


class ScheduledHooks(Hook):
    name: str = Field(default="Scheduled Hooks")

    _threads: dict[str, threading.Thread] = PrivateAttr(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def add_scheduled_function(
        self,
        func: Callable[[], Any],
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
        if isinstance(execution_frequency, str) and croniter.is_valid(
            execution_frequency
        ):
            thread_target = _cron_function
        elif (
            isinstance(execution_frequency, int)
            or execution_frequency.replace(".", "", 1).isdigit()
        ):
            thread_target = _interval_function
        else:
            raise ValueError(f"Invalid execution frequency: {execution_frequency}")

        thread = threading.Thread(
            target=thread_target,
            args=(func, execution_frequency, identifier, self._stop_event),
            daemon=False,
        )
        thread.start()
        self._threads[identifier] = thread

    def stop(self, timeout: int = 5):
        for identifier, thread in self._threads.items():
            log.info("Stopping scheduled function: %s", identifier)
            thread.join(timeout)


scheduled_hooks = ScheduledHooks()
