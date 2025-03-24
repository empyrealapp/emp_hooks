from abc import ABC, abstractmethod

from pydantic import BaseModel


class Hook(BaseModel, ABC):
    @abstractmethod
    def stop(self, timeout: int = 5): ...

    @abstractmethod
    def set_stop_event(self): ...
