from telegram import Update
from telegram.constants import ChatType


def is_group_chat(update: Update) -> bool:
    return bool(
        update.message
        and update.message.chat.type
        in [
            ChatType.GROUP,
            ChatType.SUPERGROUP,
        ]
    )
