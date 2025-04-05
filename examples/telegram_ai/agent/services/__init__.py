from emp_hooks.orm import load_session

from ..models import Chat, Message, User
from .conversation import ChatService, MessageService, UserService

session = load_session()

chat_service = ChatService(session, Chat)
user_service = UserService(session, User)
message_service = MessageService(session, Message)

__all__ = ["chat_service", "user_service", "message_service"]
