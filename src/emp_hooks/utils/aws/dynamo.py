import os
from typing import Any

import boto3
from pydantic import BaseModel, Field, PrivateAttr


class DynamoKeyValueStore(BaseModel):
    region_name: str | None = Field(
        default_factory=lambda: os.environ.get("AWS_REGION")
    )
    table_name: str | None = Field(
        default_factory=lambda: os.environ.get("AWS_DYNAMODB_TABLE_NAME")
    )

    # Create the DynamoDB resource
    _dynamodb: Any = PrivateAttr()
    _table: Any = PrivateAttr()

    def model_post_init(self, __context: Any) -> None:
        self._dynamodb = boto3.resource("dynamodb", region_name=self.region_name)
        self._table = self._dynamodb.Table(self.table_name)

        return super().model_post_init(__context)

    def get(self, key: str) -> str | None:
        response = self._table.get_item(Key={"id": key}) or {}
        return (response or {}).get("Item", {}).get("Data")

    def set(self, key: str, value: str) -> None:
        self._table.put_item(Item={"id": key, "Data": value})


class MockDynamoKeyValueStore(BaseModel):
    _store: dict[str, str] = PrivateAttr(default_factory=dict)

    def get(self, key: str) -> str | None:
        return self._store.get(key)

    def set(self, key: str, value: str) -> None:
        self._store[key] = value
