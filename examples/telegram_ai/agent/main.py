from dotenv import load_dotenv
from emp_agents import AgentBase
from emp_agents.providers import OpenAIModelType, OpenAIProvider
from telegram import Update
from telegram.ext import ContextTypes, filters

from emp_hooks import manager
from emp_hooks.handlers.telegram import on_message
from emp_hooks.utils.telegram import is_group_chat

from .prompts import GROUP_CHAT_PROMPT, PRIVATE_CHAT_PROMPT
from .services import chat_service, message_service, user_service

load_dotenv()


@on_message(filter=filters.TEXT & ~filters.COMMAND)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_user = user_service.load_bot(context)

    if not (update.message and update.message.from_user):
        return

    prompt = GROUP_CHAT_PROMPT if is_group_chat(update) else PRIVATE_CHAT_PROMPT
    agent = AgentBase(
        prompt=prompt,
        provider=OpenAIProvider(
            default_model=OpenAIModelType.gpt4o,
        ),
    )

    # add user and message to database
    chat = chat_service.store_chat(update.message)
    db_user = user_service.store_user(update.message.from_user)
    message_service.add_message(chat, db_user, update.message)

    # create response using conversation history
    response = await agent.answer(
        "\n".join(
            f"{message.user.username}: {message.text}"
            for message in message_service.get_latest_message(chat.id)
        )
    )

    # if agent has something to say, send it
    if response != "NO RESPONSE":
        response_msg = await update.message.reply_text(response)
        message_service.add_message(chat, bot_user, response_msg)


@on_message(command="test")
async def handle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    An example of a command that the bot will execute.
    To run, just send "/test" to the bot.
    """
    if update.message:
        await update.message.reply_text("test command ran")


if __name__ == "__main__":
    manager.hooks.run_forever()
