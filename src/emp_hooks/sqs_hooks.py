import json
import os
import signal
import threading
import time
from types import FrameType
from typing import Callable

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from .queue import SQSQueue


class SQSHooksManager(BaseModel):
    queue: SQSQueue | None = Field(default=None)
    hooks: dict[str, Callable] = Field(default_factory=dict)
    running: bool = Field(default=False)
    stop_event: threading.Event = Field(default_factory=threading.Event)

    _thread: threading.Thread | None = PrivateAttr(default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def model_post_init(self, __context):
        # call stop when a SIGINT or SIGTERM is sent
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

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

    def stop(self, signum: int, frame: FrameType, timeout: int = 5):
        self.running = False
        self.stop_event.set()
        if self._thread:
            self._thread.join(timeout)

    def _run(self, visibility_timeout: int = 30, loop_interval: int = 5):
        if not self.queue:
            self.queue = SQSQueue(name=os.environ["AWS_SQS_QUEUE_NAME"])

        while not self.stop_event.is_set():
            messages = self.queue.get(visibility_timeout=visibility_timeout)
            for message in messages:
                body = json.loads(message.body)
                query = body["query"]
                if query in self.hooks:
                    do_delete: bool = self.hooks[query](body)
                    if do_delete:
                        message.delete()
            time.sleep(loop_interval)


hooks: SQSHooksManager = SQSHooksManager()
