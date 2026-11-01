"""Create the initial ChattieBaby account and chat schema."""

from alembic import op
import sqlalchemy as sa


revision = "20261101_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(32), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(username) BETWEEN 3 AND 32",
            name="ck_users_username_length",
        ),
        sa.CheckConstraint(
            "length(email) BETWEEN 3 AND 254",
            name="ck_users_email_length",
        ),
        sa.CheckConstraint(
            "length(password_hash) > 0",
            name="ck_users_password_hash",
        ),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "user_settings",
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("theme", sa.String(16), server_default="light", nullable=False),
        sa.Column(
            "preferences",
            sa.JSON(),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "theme IN ('light', 'dark')",
            name="ck_user_settings_theme",
        ),
    )

    op.create_table(
        "chats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("platform", sa.String(32), server_default="whatsapp", nullable=False),
        sa.Column("title", sa.String(120), server_default="My Chat", nullable=False),
        sa.Column("subtitle", sa.String(120), server_default="", nullable=False),
        sa.Column("theme", sa.String(16), server_default="light", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "platform IN ('whatsapp', 'instagram', 'chatgpt')",
            name="ck_chats_platform",
        ),
        sa.CheckConstraint("theme IN ('light', 'dark')", name="ck_chats_theme"),
        sa.UniqueConstraint("id", "user_id", name="uq_chats_id_user_id"),
    )
    op.create_index("ix_chats_user_id", "chats", ["user_id"], unique=False)

    op.create_table(
        "participants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "chat_id",
            sa.Integer(),
            sa.ForeignKey("chats.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(60), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("avatar_path", sa.String(1024)),
        sa.CheckConstraint(
            "role IN ('me', 'other')",
            name="ck_participants_role",
        ),
        sa.CheckConstraint(
            "length(trim(name)) > 0",
            name="ck_participants_name",
        ),
    )
    op.create_index("ix_participants_chat_id", "participants", ["chat_id"], unique=False)

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "chat_id",
            sa.Integer(),
            sa.ForeignKey("chats.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "sender_id",
            sa.Integer(),
            sa.ForeignKey("participants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(32), server_default="text", nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("timestamp", sa.String(80), nullable=False),
        sa.Column("position", sa.Integer(), server_default="1", nullable=False),
        sa.Column("direction", sa.String(16), server_default="outbound", nullable=False),
        sa.Column(
            "reply_to",
            sa.Integer(),
            sa.ForeignKey("messages.id", ondelete="SET NULL"),
        ),
        sa.Column("meta", sa.JSON()),
        sa.CheckConstraint(
            "position >= 1",
            name="ck_messages_position",
        ),
        sa.CheckConstraint(
            "direction IN ('inbound', 'outbound')",
            name="ck_messages_direction",
        ),
        sa.CheckConstraint(
            "length(trim(content)) > 0",
            name="ck_messages_content",
        ),
        sa.UniqueConstraint("chat_id", "position", name="uq_message_chat_position"),
    )
    op.create_index("ix_messages_chat_id", "messages", ["chat_id"], unique=False)
    op.create_index("ix_messages_sender_id", "messages", ["sender_id"], unique=False)

    op.create_table(
        "generation_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chat_id", sa.Integer(), nullable=False),
        sa.Column("output_path", sa.String(1024), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["chat_id", "user_id"],
            ["chats.id", "chats.user_id"],
            ondelete="CASCADE",
            name="fk_generation_history_chat_owner",
        ),
    )
    op.create_index(
        "ix_generation_history_user_id",
        "generation_history",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_generation_history_chat_id",
        "generation_history",
        ["chat_id"],
        unique=False,
    )

    op.create_table(
        "refresh_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_refresh_sessions_user_id",
        "refresh_sessions",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_refresh_sessions_token_hash",
        "refresh_sessions",
        ["token_hash"],
        unique=True,
    )


def downgrade():
    op.drop_table("refresh_sessions")
    op.drop_index("ix_generation_history_chat_id", table_name="generation_history")
    op.drop_index("ix_generation_history_user_id", table_name="generation_history")
    op.drop_table("generation_history")
    op.drop_index("ix_messages_sender_id", table_name="messages")
    op.drop_index("ix_messages_chat_id", table_name="messages")
    op.drop_table("messages")
    op.drop_index("ix_participants_chat_id", table_name="participants")
    op.drop_table("participants")
    op.drop_index("ix_chats_user_id", table_name="chats")
    op.drop_table("chats")
    op.drop_table("user_settings")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
