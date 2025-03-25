import json
import os
import threading
import time
from typing import Callable

from pydantic import ConfigDict, Field, PrivateAttr

from emp_hooks.types import Hook
from emp_hooks.utils import SQSQueue


class SQSHooks(Hook):
    name: str = Field(default="SQS Hooks")

    queue: SQSQueue | None = Field(default=None)
    hooks: dict[str, Callable] = Field(default_factory=dict)
    running: bool = Field(default=False)

    _thread: threading.Thread | None = PrivateAttr(default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def add_hook(self, hook_name: str, hook: Callable):
        self.hooks[hook_name] = hook

    def run(
        self,
        visibility_timeout: int = 30,
        loop_interval: int = 5,
        daemon: bool = False,
    ):
        if not os.environ.get("ENVIRONMENT", "").lower() == "production":
            return
        if self.running:
            return

        self.running = True
        self._thread = threading.Thread(
            target=self._run,
            args=(visibility_timeout, loop_interval),
            daemon=daemon,  # keep the program running until the hook is stopped
        )
        self._thread.start()

    def stop(self, timeout: int = 5):
        self.running = False
        if self._thread:
            self._thread.join(timeout)

    def _run(self, visibility_timeout: int = 30, loop_interval: int = 5):
        if not self.queue:
            self.queue = SQSQueue(name=os.environ["AWS_SQS_QUEUE_NAME"])

        while not self._stop_event.is_set():
            messages = self.queue.get(visibility_timeout=visibility_timeout)
            for message in messages:
                if self._stop_event.is_set():
                    break

                body = json.loads(message.body)
                query = body["query"]
                if query in self.hooks:
                    do_delete: bool = self.hooks[query](body)
                    if do_delete:
                        message.delete()
            time.sleep(loop_interval)


sqs_hooks: SQSHooks = SQSHooks()
