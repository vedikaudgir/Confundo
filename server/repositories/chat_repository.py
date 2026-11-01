from sqlalchemy import select

from server.database import session_scope
from server.models import Chat


def create_chat(user_id, platform, title, subtitle, theme):
    with session_scope() as session:
        chat = Chat(
            user_id=user_id,
            platform=platform,
            title=title,
            subtitle=subtitle,
            theme=theme or "light",
        )
        session.add(chat)
        session.flush()
        return chat.id


def get_chat(chat_id, user_id):
    with session_scope() as session:
        chat = session.scalar(
            select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
        )
        if chat is None:
            return None
        return chat.id, chat.platform, chat.title, chat.subtitle, chat.theme


def get_chat_record(chat_id, user_id):
    with session_scope() as session:
        chat = session.scalar(
            select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
        )
        if chat is None:
            return None
        session.expunge(chat)
        return chat


def update_chat(chat_id, user_id, platform, title, subtitle, theme):
    with session_scope() as session:
        chat = session.scalar(
            select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
        )
        if chat is None:
            return False
        chat.platform = platform
        chat.title = title
        chat.subtitle = subtitle
        chat.theme = theme or "light"
        return True


def delete_chat(chat_id, user_id):
    with session_scope() as session:
        chat = session.scalar(
            select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
        )
        if chat is None:
            return False
        session.delete(chat)
        return True
