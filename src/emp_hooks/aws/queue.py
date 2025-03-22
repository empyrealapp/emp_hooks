from typing import Any

import boto3
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr


class SQSQueue(BaseModel):
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
