import signal
import threading
from types import FrameType

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from emp_hooks.logger import log

from .handlers import onchain_hooks, scheduled_hooks, sqs_hooks, telegram_hooks
from .types import Hook


class HooksManager(BaseModel):
    hook_managers: list[Hook] = Field(default_factory=list)
    running: bool = Field(default=False)
    _stopped: threading.Event = PrivateAttr(default_factory=threading.Event)
    _main_thread: threading.Thread = PrivateAttr()

    def model_post_init(self, __context):
        # call "stop" when a SIGINT or SIGTERM is sent
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

        return super().model_post_init(__context)

    def add_hook_manager(self, hook: Hook):
        hook.update_stop_event(self._stopped)
        self.hook_managers.append(hook)

    def stop(self, signum: int, frame: FrameType):
        log.info("Stopping hook managers")
        self._stopped.set()

        log.info("Stopping hook managers")
        for hook in self.hook_managers:
            hook.stop()
            log.info("Stopped hook manager: %s", hook.name)

    def run_forever(self, timeout: int = 3):
        """Runs all hook managers indefinitely"""
        import time

        for hook in self.hook_managers:
            hook.start()

        while not self._stopped.is_set():
            time.sleep(timeout)

    model_config = ConfigDict(arbitrary_types_allowed=True)


hooks: HooksManager = HooksManager()
hooks.add_hook_manager(sqs_hooks)
hooks.add_hook_manager(onchain_hooks)
hooks.add_hook_manager(scheduled_hooks)
hooks.add_hook_manager(telegram_hooks)
