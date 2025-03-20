import json
import os
import threading
import time
from typing import Any, Callable

import boto3
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr


class Queue(BaseModel):
    name: str
    sqs: Any = Field(default_factory=lambda: boto3.resource("sqs"))
    _queue: boto3.resources.base.ServiceResource = PrivateAttr()

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def model_post_init(self, __context: Any) -> None:
        self._queue = self.sqs.get_queue_by_name(QueueName=self.name)
        return super().model_post_init(__context)

    def pending_count(self) -> int:
        self._queue.reload()
        return int(self._queue.attributes["ApproximateNumberOfMessages"])

    @property
    def url(self) -> str:
        return self._queue.url

    def get(self, max_messages: int = 5, visibility_timeout: int = 8) -> list:
        response = self._queue.receive_messages(
            QueueUrl=self.url,
            MaxNumberOfMessages=max_messages,
            VisibilityTimeout=visibility_timeout,
        )

        return response


class SQSHooksManager:
    queue: Queue | None = Field(default=None)
    hooks: dict[str, Callable] = Field(default_factory=dict)
    running: bool = Field(default=False)
    _thread: threading.Thread | None = Field(default=None)

    stop_event: threading.Event = Field(default_factory=threading.Event)

    def __init__(self):
        self.queue = None
        self.hooks = {}
        self.running = False
        self._thread = None
        self.stop_event = threading.Event()

    def add_hook(self, hook_name: str, hook: Callable):
        self.hooks[hook_name] = hook

    def run(
        self,
        visibility_timeout: int = 30,
        loop_interval: int = 5,
        keep_alive: bool = False,
    ):
        if not os.environ.get("ENVIRONMENT") == "production":
            return
        if self.running and not keep_alive:
            return

        self.running = True
        self._thread = threading.Thread(
            target=self._run,
            args=(visibility_timeout, loop_interval),
            daemon=True,
        )
        self._thread.start()

        if keep_alive:
            while True:
                time.sleep(3)

    def stop(self, loop_interval: int = 5):
        self.running = False
        self.stop_event.set()
        if self._thread:
            self._thread.join(loop_interval)

    def _run(self, visibility_timeout: int = 30, loop_interval: int = 5):
        if not self.queue:
            self.queue = Queue(name=os.environ["AWS_SQS_QUEUE_NAME"])

        while not self.stop_event.is_set():
            messages = self.queue.get(visibility_timeout=visibility_timeout)
            for message in messages:
                body = json.loads(message.body)
                query = body["query"]
                if query in self.hooks:
                    self.hooks[query](body)
                    message.delete()
            time.sleep(loop_interval)


hooks: SQSHooksManager = SQSHooksManager()
