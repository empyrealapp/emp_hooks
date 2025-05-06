import asyncio
import json
import os
import threading
from typing import Callable

from pydantic import ConfigDict, Field, PrivateAttr

import botocore.exceptions
from emp_hooks.types import Hook
from emp_hooks.utils import SQSQueue

from emp_hooks.logger import log


class SQSHooks(Hook):
    name: str = Field(default="SQS Hooks")

    queue: SQSQueue | None = Field(default=None)
    hooks: dict[str, Callable] = Field(default_factory=dict)
    running: bool = Field(default=False)

    _thread: threading.Thread | None = PrivateAttr(default=None)
    _loop: asyncio.AbstractEventLoop | None = PrivateAttr(default=None)

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
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._run_loop,
            args=(visibility_timeout, loop_interval),
            daemon=daemon,
        )
        self._thread.start()

    def stop(self, timeout: int = 5):
        self.running = False
        if self._thread:
            self._thread.join(timeout)

    def _run_loop(self, visibility_timeout: int = 30, loop_interval: int = 5):
        asyncio.set_event_loop(self._loop)
        assert self._loop is not None
        self._loop.run_until_complete(self._run(visibility_timeout, loop_interval))

    async def _run(self, visibility_timeout: int = 30, loop_interval: int = 5):
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
                    func = self.hooks[query]

                    do_delete: bool
                    if asyncio.iscoroutinefunction(func):
                        do_delete = await func(body)
                    else:
                        do_delete = func(body)

                    if do_delete:
                        try:
                            message.delete()
                        except botocore.exceptions.ClientError as e:
                            log.error("Error deleting message: %s", e)
            await asyncio.sleep(loop_interval)


sqs_hooks: SQSHooks = SQSHooks()
