from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from emp_hooks.orm import DBModel, Mapped, mapped_column


class Message(DBModel):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id"), nullable=False)
    message_id: Mapped[int] = mapped_column(nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(nullable=False)
    text: Mapped[str] = mapped_column(nullable=False)

    chat: Mapped["Chat"] = relationship("Chat", back_populates="messages")
    user: Mapped["User"] = relationship("User", back_populates="messages")


class Chat(DBModel):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(nullable=False)

    messages: Mapped[list["Message"]] = relationship("Message", back_populates="chat")


class User(DBModel):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(nullable=True)
    first_name: Mapped[str] = mapped_column(nullable=True)
    last_name: Mapped[str] = mapped_column(nullable=True)

    messages: Mapped[list["Message"]] = relationship("Message", back_populates="user")
