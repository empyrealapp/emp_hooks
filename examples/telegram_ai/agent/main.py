import os

from dotenv import load_dotenv
from emp_agents import AgentBase
from emp_agents.providers import OpenAIProvider
from telegram import Update
from telegram.ext import ContextTypes

from emp_hooks import manager
from emp_hooks.handlers.telegram import on_message
from emp_hooks.orm import load_session

from .models import Chat, Message, User
from .prompt import PROMPT
from .services import ChatService, MessageService, UserService

load_dotenv()

agent = AgentBase(
    prompt=PROMPT,
    sync_tools=True,
    provider=OpenAIProvider(
        api_key=os.environ["OPENAI_API_KEY"],
    ),
)

session = load_session()

chat_service = ChatService(session, Chat)
user_service = UserService(session, User)
message_service = MessageService(session, Message)


@on_message()
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_user = user_service.load_bot(context)

    if not (update.message and update.message.from_user):
        return

    # add user and message to database
    chat = chat_service.store_chat(update.message)
    db_user = user_service.store_user(update.message.from_user)
    message_service.get_or_create(
        chat_id=chat.id,
        message_id=update.message.message_id,
        text=update.message.text,
        user_id=db_user.id,
        timestamp=update.message.date,
    )

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

        # add agent message to database
        message_service.get_or_create(
            chat_id=chat.id,
            message_id=response_msg.message_id,
            text=response,
            user_id=bot_user.id,
            timestamp=response_msg.date,
        )


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
