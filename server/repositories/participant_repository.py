from sqlalchemy import select

from server.database import session_scope
from server.models import Chat, Participant


def add_participant(chat_id, user_id, name, role):
    with session_scope() as session:
        owns_chat = session.scalar(
            select(Chat.id).where(Chat.id == chat_id, Chat.user_id == user_id)
        )
        if owns_chat is None:
            return None
        participant = Participant(chat_id=chat_id, name=name, role=role)
        session.add(participant)
        session.flush()
        return participant.id


def get_participants(chat_id, user_id):
    with session_scope() as session:
        participants = session.scalars(
            select(Participant)
            .join(Chat, Chat.id == Participant.chat_id)
            .where(Chat.id == chat_id, Chat.user_id == user_id)
            .order_by(Participant.id)
        ).all()
        return [
            (item.id, item.chat_id, item.name, item.role, item.avatar_path)
            for item in participants
        ]


def get_participant(participant_id, user_id):
    with session_scope() as session:
        participant = session.scalar(
            select(Participant)
            .join(Chat, Chat.id == Participant.chat_id)
            .where(Participant.id == participant_id, Chat.user_id == user_id)
        )
        if participant is None:
            return None
        return (
            participant.id,
            participant.chat_id,
            participant.name,
            participant.role,
            participant.avatar_path,
        )


def update_avatar(participant_id, user_id, path):
    with session_scope() as session:
        participant = session.scalar(
            select(Participant)
            .join(Chat, Chat.id == Participant.chat_id)
            .where(Participant.id == participant_id, Chat.user_id == user_id)
        )
        if participant is None:
            return False
        participant.avatar_path = path
        return True


def update_participant_name(participant_id, user_id, name):
    with session_scope() as session:
        participant = session.scalar(
            select(Participant)
            .join(Chat, Chat.id == Participant.chat_id)
            .where(Participant.id == participant_id, Chat.user_id == user_id)
        )
        if participant is None:
            return False
        participant.name = name
        return True


def delete_participant(participant_id, user_id):
    with session_scope() as session:
        participant = session.scalar(
            select(Participant)
            .join(Chat, Chat.id == Participant.chat_id)
            .where(Participant.id == participant_id, Chat.user_id == user_id)
        )
        if participant is None:
            return False
        session.delete(participant)
        return True
