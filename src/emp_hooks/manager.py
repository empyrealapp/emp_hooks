import signal
import threading
from types import FrameType

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from .onchain import onchain_hooks
from .sqs_hooks import sqs_hooks
from .types import Hook


class HooksManager(BaseModel):
    hook_managers: list[Hook] = Field(default_factory=list)
    running: bool = Field(default=False)
    _stopped: threading.Event = PrivateAttr(default_factory=threading.Event)

    def model_post_init(self, __context):
        # call "stop" when a SIGINT or SIGTERM is sent
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

        return super().model_post_init(__context)

    def add_hook_manager(self, hook: Hook):
        self.hook_managers.append(hook)

    def stop(self, signum: int, frame: FrameType):
        self._stopped.set()
        for hook in self.hook_managers:
            hook.set_stop_event()

        for hook in self.hook_managers:
            hook.stop()

    def run_forever(self, timeout: int = 3):
        import time

        while not self._stopped.is_set():
            time.sleep(timeout)

    model_config = ConfigDict(arbitrary_types_allowed=True)


hooks: HooksManager = HooksManager()
hooks.add_hook_manager(sqs_hooks)
hooks.add_hook_manager(onchain_hooks)
