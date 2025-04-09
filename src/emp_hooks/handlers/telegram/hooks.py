import asyncio
import os
import threading

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr
from telegram import Update
from telegram.ext import Application, ApplicationBuilder

from emp_hooks.logger import log
from emp_hooks.types import Hook


class TelegramApp(BaseModel):
    loop: asyncio.AbstractEventLoop
    app: Application

    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def run(self):
        await self.app.initialize()
        await self.app.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
        )
        await self.app.start()
        log.info("Telegram app running")


class TelegramHooks(Hook):
    name: str = Field(default="Telegram Hooks")

    _app: Application | None = PrivateAttr(default=None)
    _thread: threading.Thread = PrivateAttr()
    _loop: asyncio.AbstractEventLoop | None = PrivateAttr(default=None)
    _is_running: bool = PrivateAttr(default=False)
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def register_app(self, app: Application):
        self._app = app

    def get_app(self):
        if self._app is None:
            self._app = (
                ApplicationBuilder().token(os.environ["TELEGRAM_BOT_TOKEN"]).build()
            )
        return self._app

    def start(self):
        if self._is_running:
            return

        if not self._app:
            return

        def run_app():
            loop = asyncio.new_event_loop()
            self._loop = loop
            asyncio.set_event_loop(loop)
            loop.run_until_complete(TelegramApp(loop=loop, app=self._app).run())
            loop.run_forever()

        self._thread = threading.Thread(target=run_app)
        self._thread.start()
        self._is_running = True

    def stop(self, timeout: int = 1):
        log.info("Stopping telegram app")
        if self._loop:
            # Wait for thread to finish
            self._thread.join(timeout)

            # Stop the loop
            self._loop.stop()


telegram_hooks = TelegramHooks()
