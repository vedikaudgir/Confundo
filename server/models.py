from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("length(username) BETWEEN 3 AND 32", name="ck_users_username_length"),
        CheckConstraint("length(email) BETWEEN 3 AND 254", name="ck_users_email_length"),
        CheckConstraint("length(password_hash) > 0", name="ck_users_password_hash"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )

    settings: Mapped["UserSettings"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    chats: Mapped[list["Chat"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    generation_history: Mapped[list["GenerationHistory"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        overlaps="chat",
    )
    refresh_sessions: Mapped[list["RefreshSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )


class UserSettings(Base):
    __tablename__ = "user_settings"
    __table_args__ = (
        CheckConstraint("theme IN ('light', 'dark')", name="ck_user_settings_theme"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    theme: Mapped[str] = mapped_column(String(16), nullable=False, default="light")
    preferences: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    user: Mapped[User] = relationship(back_populates="settings")


class Chat(Base):
    __tablename__ = "chats"
    __table_args__ = (
        CheckConstraint(
            "platform IN ('whatsapp', 'instagram', 'chatgpt')",
            name="ck_chats_platform",
        ),
        CheckConstraint("theme IN ('light', 'dark')", name="ck_chats_theme"),
        UniqueConstraint("id", "user_id", name="uq_chats_id_user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform: Mapped[str] = mapped_column(String(32), nullable=False, default="whatsapp")
    title: Mapped[str] = mapped_column(String(120), nullable=False, default="My Chat")
    subtitle: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    theme: Mapped[str] = mapped_column(String(16), nullable=False, default="light")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=utc_now,
    )

    user: Mapped[User] = relationship(back_populates="chats")
    participants: Mapped[list["Participant"]] = relationship(
        back_populates="chat", cascade="all, delete-orphan", passive_deletes=True
    )
    messages: Mapped[list["Message"]] = relationship(
        back_populates="chat", cascade="all, delete-orphan", passive_deletes=True
    )
    generation_history: Mapped[list["GenerationHistory"]] = relationship(
        back_populates="chat",
        cascade="all, delete-orphan",
        passive_deletes=True,
        overlaps="user,generation_history",
    )


class Participant(Base):
    __tablename__ = "participants"
    __table_args__ = (
        CheckConstraint("role IN ('me', 'other')", name="ck_participants_role"),
        CheckConstraint("length(trim(name)) > 0", name="ck_participants_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    avatar_path: Mapped[str | None] = mapped_column(String(1024))

    chat: Mapped[Chat] = relationship(back_populates="participants")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="sender", passive_deletes=True
    )


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        UniqueConstraint("chat_id", "position", name="uq_message_chat_position"),
        CheckConstraint("position >= 1", name="ck_messages_position"),
        CheckConstraint(
            "direction IN ('inbound', 'outbound')",
            name="ck_messages_direction",
        ),
        CheckConstraint("length(trim(content)) > 0", name="ck_messages_content"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sender_id: Mapped[int] = mapped_column(
        ForeignKey("participants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column("type", String(32), nullable=False, default="text")
    timestamp: Mapped[str] = mapped_column(String(80), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    direction: Mapped[str] = mapped_column(String(16), nullable=False, default="outbound")
    reply_to: Mapped[int | None] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL")
    )
    meta: Mapped[dict | None] = mapped_column(JSON)

    chat: Mapped[Chat] = relationship(back_populates="messages")
    sender: Mapped[Participant | None] = relationship(back_populates="messages")


class GenerationHistory(Base):
    __tablename__ = "generation_history"
    __table_args__ = (
        ForeignKeyConstraint(
            ["chat_id", "user_id"],
            ["chats.id", "chats.user_id"],
            ondelete="CASCADE",
            name="fk_generation_history_chat_owner",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chat_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    output_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )

    user: Mapped[User] = relationship(
        back_populates="generation_history",
        overlaps="chat,generation_history",
    )
    chat: Mapped[Chat] = relationship(
        back_populates="generation_history",
        overlaps="user,generation_history",
    )


class RefreshSession(Base):
    __tablename__ = "refresh_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )

    user: Mapped[User] = relationship(back_populates="refresh_sessions")
