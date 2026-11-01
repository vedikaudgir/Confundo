from sqlalchemy import func, or_, select

from server.database import session_scope
from server.models import User


def create_user(username: str, email: str, password_hash: str) -> int:
    with session_scope() as session:
        user = User(username=username, email=email.lower(), password_hash=password_hash)
        session.add(user)
        session.flush()
        return user.id


def get_user_by_identifier(identifier: str):
    normalized = identifier.strip().lower()
    with session_scope() as session:
        user = session.scalar(
            select(User).where(
                or_(User.email == normalized, func.lower(User.username) == normalized)
            )
        )
        if user is None:
            return None
        session.expunge(user)
        return user


def get_user(user_id: int):
    with session_scope() as session:
        user = session.get(User, user_id)
        if user is None:
            return None
        session.expunge(user)
        return user
