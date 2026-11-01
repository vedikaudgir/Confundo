from sqlalchemy import func, select

from server.database import session_scope
from server.models import Chat, Message, Participant


def add_message(
    chat_id,
    user_id,
    sender_role,
    msg_type,
    content,
    timestamp,
    direction,
    reply_to=None,
    meta=None,
):
    with session_scope() as session:
        participant = session.scalar(
            select(Participant)
            .join(Chat, Chat.id == Participant.chat_id)
            .where(
                Chat.id == chat_id,
                Chat.user_id == user_id,
                Participant.role == sender_role,
            )
            .order_by(Participant.id)
        )
        if participant is None:
            return None
        position = session.scalar(
            select(func.coalesce(func.max(Message.position), 0)).where(Message.chat_id == chat_id)
        ) + 1
        message = Message(
            chat_id=chat_id,
            sender_id=participant.id,
            content=content,
            message_type=msg_type,
            timestamp=timestamp,
            position=position,
            direction=direction,
            reply_to=reply_to,
            meta=meta,
        )
        session.add(message)
        session.flush()
        return message.id


def get_messages(chat_id, user_id):
    with session_scope() as session:
        messages = session.scalars(
            select(Message)
            .join(Chat, Chat.id == Message.chat_id)
            .where(Chat.id == chat_id, Chat.user_id == user_id)
            .order_by(Message.position, Message.id)
        ).all()
        return [
            (
                item.id,
                item.chat_id,
                item.sender_id,
                item.message_type,
                item.content,
                item.timestamp,
                item.direction,
                item.reply_to,
                item.meta,
            )
            for item in messages
        ]


def update_message(chat_id, message_id, user_id, content, timestamp):
    with session_scope() as session:
        message = session.scalar(
            select(Message)
            .join(Chat, Chat.id == Message.chat_id)
            .where(
                Message.id == message_id,
                Message.chat_id == chat_id,
                Chat.user_id == user_id,
            )
        )
        if message is None:
            return False
        message.content = content
        message.timestamp = timestamp
        return True


def delete_message(chat_id, message_id, user_id):
    with session_scope() as session:
        message = session.scalar(
            select(Message)
            .join(Chat, Chat.id == Message.chat_id)
            .where(
                Message.id == message_id,
                Message.chat_id == chat_id,
                Chat.user_id == user_id,
            )
        )
        if message is None:
            return False
        session.delete(message)
        return True
