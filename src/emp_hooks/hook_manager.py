import os
import threading
import time
from typing import Any, Callable

import boto3
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr


class Queue(BaseModel):
    name: str
    sqs: Any = Field(default_factory=lambda: boto3.client("sqs"))
    _queue: boto3.resources.base.ServiceResource = PrivateAttr()

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def model_post_init(self, __context: Any) -> None:
        self._queue = self.sqs.get_queue_by_name(QueueName=self.name)
        return super().model_post_init(__context)

    async def pending_count(self) -> int:
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

    def add_hook(self, hook_name: str, hook: Callable):
        self.hooks[hook_name] = hook

    def run(self, visibility_timeout: int = 30, loop_interval: int = 5):
        if not os.environ.get("ENVIRONMENT") == "production":
            return

        if self.running:
            return

        self.running = True

        self._thread = threading.Thread(
            target=self._run,
            args=(visibility_timeout, loop_interval),
            daemon=True,
        )
        self._thread.setDaemon(True)
        self._thread.start()

    def stop(self):
        self.running = False
        self._thread.join(5)

    def _run(self, visibility_timeout: int = 30, loop_interval: int = 5):
        if not self.queue:
            self.queue = Queue(name=os.environ["SQS_QUEUE_NAME"])

        while True:
            messages = self.queue.get(visibility_timeout=visibility_timeout)
            for message in messages:
                if message["type"] in self.hooks:
                    self.hooks[message["type"]](message)
                    message.delete()
            time.sleep(loop_interval)


hooks: SQSHooksManager = SQSHooksManager()
