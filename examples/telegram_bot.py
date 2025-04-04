import logging

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes

from emp_hooks import log, manager
from emp_hooks.handlers.telegram import on_message

load_dotenv()

log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(formatter)
log.addHandler(stream_handler)


@on_message()
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("UPDATE?", update, context)
    if update.message:
        await update.message.reply_text("ok")


@on_message(command="test")
async def handle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("UPDATE?", update, context)
    if update.message:
        await update.message.reply_text("test command ran")


if __name__ == "__main__":
    manager.hooks.run_forever()
