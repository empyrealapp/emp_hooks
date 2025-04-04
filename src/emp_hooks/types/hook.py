import threading
from abc import ABC, abstractmethod

from pydantic import BaseModel, PrivateAttr


class Hook(BaseModel, ABC):
    name: str
    _stop_event: threading.Event = PrivateAttr(default_factory=threading.Event)

    @abstractmethod
    def stop(self, timeout: int = 5): ...

    def start(self):
        pass

    def update_stop_event(self, stop_event: threading.Event):
        self._stop_event = stop_event
