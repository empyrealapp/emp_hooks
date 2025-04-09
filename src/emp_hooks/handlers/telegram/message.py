from collections.abc import Callable
from typing import Any, Coroutine

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from ...logger import log
from .hooks import telegram_hooks

BASIC_TEXT_FILTER = filters.TEXT & ~filters.COMMAND


def on_message(
    app: Application | None = None,
    command: str | None = None,
    filter: filters.BaseFilter | None = None,
):
    """
    Decorator to register a function to be called when a message is received.

    Args:
        app (Application | None, optional): The application to use. If not provided, the function will be registered to the default application.

    Returns:
        Callable: A decorator that registers the function to be called at the specified interval or cron schedule.
    """

    def wrapper(
        func: Callable[[Update, ContextTypes.DEFAULT_TYPE], Coroutine[Any, Any, None]],
    ):
        nonlocal app
        if app is None:
            app = telegram_hooks.get_app()
        else:
            telegram_hooks.register_app(app)

        if command is not None:
            log.info("Adding command handler for %s", command)
            app.add_handler(CommandHandler(command, func))
        else:
            log.info("Adding message handler for %s", filter or BASIC_TEXT_FILTER)
            app.add_handler(MessageHandler(filter or BASIC_TEXT_FILTER, func))
        return func

    return wrapper
