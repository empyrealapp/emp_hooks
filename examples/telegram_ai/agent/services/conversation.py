from sqlalchemy import select
from telegram import Message as TelegramMessage
from telegram import User as TelegramUser
from telegram.ext import ContextTypes

from emp_hooks.orm import DBService

from ..models import Chat, Message, User


class MessageService(DBService[Message]):
    def get_latest_message(
        self, chat_id: int, user_id: int | None = None, limit: int = 10
    ) -> list[Message]:
        stmt = select(Message).where(Message.chat_id == chat_id)
        if user_id:
            stmt = stmt.where(Message.user_id == user_id)

        stmt = stmt.order_by(Message.timestamp.desc()).limit(limit)
        return list(self.session.scalars(stmt))[::-1]


class ChatService(DBService[Chat]):
    def store_chat(self, message: TelegramMessage) -> Chat:
        return self.get_or_create(
            id=message.chat.id,
            type=message.chat.type,
        )


class UserService(DBService[User]):
    def load_bot(self, context: ContextTypes.DEFAULT_TYPE) -> User:
        return self.get_or_create(
            id=context.bot.id,
            username=context.bot.username,
            first_name=context.bot.first_name,
            last_name=context.bot.last_name,
        )

    def store_user(self, user: TelegramUser):
        return self.get_or_create(
            id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )
