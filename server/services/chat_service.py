from pathlib import Path
import shutil
from collections import defaultdict
from threading import Lock
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from server.database import session_scope
from server.config import PRIVATE_STORAGE_DIR
from server.models import Chat, GenerationHistory, Participant
from server.repositories.chat_repository import (
    create_chat,
    get_chat,
    update_chat,
)
from server.repositories.message_repository import (
    add_message,
    delete_message as remove_message,
    get_messages,
    update_message,
)
from server.repositories.participant_repository import (
    add_participant,
    delete_participant,
    get_participant,
    get_participants,
    update_participant_name,
)
from server.renderers.chatgpt import render_chatgpt
from server.renderers.instagram import render_instagram
from server.renderers.whatsapp import render_whatsapp
from server.security import utc_now


PRIVATE_GENERATED_DIR = PRIVATE_STORAGE_DIR / "generated"
_render_locks = defaultdict(Lock)


def create_chat_workflow(
    user_id,
    platform,
    title,
    subtitle,
    theme,
    my_name="You",
    other_name=None,
):
    platform = (platform or "whatsapp").strip().lower()
    if platform not in {"whatsapp", "instagram", "chatgpt"}:
        raise ValueError(f"Unsupported platform: {platform}")

    my_name = (my_name or "You").strip() or "You"
    other_name = (other_name or title or "Friend").strip() or "Friend"
    chat_id = create_chat(user_id, platform, title, subtitle, theme)

    me_id = add_participant(chat_id, user_id, my_name, "me")
    other_id = add_participant(chat_id, user_id, other_name, "other")
    if me_id is None or other_id is None:
        raise RuntimeError("Could not create participants for the new chat")

    preview_path = generate_preview(chat_id, user_id)
    if preview_path is None:
        raise RuntimeError("Could not render the new chat")
    return {
        "chat_id": chat_id,
        "preview": preview_path,
        "me_id": me_id,
        "other_id": other_id,
    }


def add_message_workflow(
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
    if get_chat(chat_id, user_id) is None:
        return None
    message_id = add_message(
        chat_id,
        user_id,
        sender_role,
        msg_type,
        content,
        timestamp,
        direction,
        reply_to,
        meta,
    )
    if message_id is None:
        return None
    return {"status": "message added", "message_id": message_id}


def get_chat_state(chat_id, user_id):
    chat = get_chat(chat_id, user_id)
    if chat is None:
        return None
    return {
        "chat": chat,
        "participants": get_participants(chat_id, user_id),
        "messages": get_messages(chat_id, user_id),
    }


def update_chat_workflow(
    chat_id,
    user_id,
    platform,
    title,
    subtitle,
    theme,
    my_name=None,
    other_name=None,
):
    platform = (platform or "whatsapp").strip().lower()
    if platform not in {"whatsapp", "instagram", "chatgpt"}:
        raise ValueError(f"Unsupported platform: {platform}")
    if not update_chat(chat_id, user_id, platform, title, subtitle, theme):
        return False

    for participant in get_participants(chat_id, user_id):
        if participant[3] == "me" and my_name is not None:
            update_participant_name(participant[0], user_id, my_name.strip() or "You")
        elif participant[3] == "other" and other_name is not None:
            update_participant_name(
                participant[0], user_id, other_name.strip() or title or "Friend"
            )
    return {"status": "chat updated"}


def generate_preview(chat_id, user_id):
    with _render_locks[chat_id]:
        renderer_output = _render_chat_for_user(chat_id, user_id)
        if renderer_output is None:
            return None
        owner_dir = PRIVATE_GENERATED_DIR / str(user_id)
        owner_dir.mkdir(parents=True, exist_ok=True)
        private_output = owner_dir / f"chat_{chat_id}.png"
        shutil.move(str(renderer_output), str(private_output))
        return str(private_output)


def generate_chat_image(chat_id, user_id):
    with _render_locks[chat_id]:
        renderer_output = _render_chat_for_user(chat_id, user_id)
        if renderer_output is None:
            return None
        owner_dir = PRIVATE_GENERATED_DIR / str(user_id)
        owner_dir.mkdir(parents=True, exist_ok=True)
        private_output = owner_dir / f"generation_{uuid4().hex}.png"
        shutil.move(str(renderer_output), str(private_output))
        try:
            with session_scope() as session:
                session.add(
                    GenerationHistory(
                        user_id=user_id,
                        chat_id=chat_id,
                        output_path=str(private_output),
                        created_at=utc_now(),
                    )
                )
        except SQLAlchemyError:
            private_output.unlink(missing_ok=True)
            raise
        return str(private_output)


def _render_chat_for_user(chat_id, user_id):
    chat = get_chat(chat_id, user_id)
    if chat is None:
        return None
    participants = get_participants(chat_id, user_id)
    messages = get_messages(chat_id, user_id)
    return Path(_render_chat(chat, participants, messages))


def get_history_image(history_id, user_id):
    with session_scope() as session:
        history = session.scalar(
            select(GenerationHistory).where(
                GenerationHistory.id == history_id,
                GenerationHistory.user_id == user_id,
            )
        )
        if history is None:
            return None
        path = Path(history.output_path).resolve()
        owner_dir = (PRIVATE_GENERATED_DIR / str(user_id)).resolve()
        if path.parent != owner_dir or not path.is_file():
            return None
        return path


def edit_message_workflow(chat_id, message_id, user_id, content, timestamp):
    return update_message(chat_id, message_id, user_id, content, timestamp)


def delete_message_workflow(chat_id, message_id, user_id):
    return remove_message(chat_id, message_id, user_id)


def delete_chat_workflow(chat_id, user_id):
    with session_scope() as session:
        chat = session.scalar(
            select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
        )
        if chat is None:
            return False
        output_paths = session.scalars(
            select(GenerationHistory.output_path).where(
                GenerationHistory.chat_id == chat_id,
                GenerationHistory.user_id == user_id,
            )
        ).all()
        avatar_paths = session.scalars(
            select(Participant.avatar_path)
            .join(Chat, Chat.id == Participant.chat_id)
            .where(Chat.id == chat_id, Chat.user_id == user_id)
        ).all()
        session.delete(chat)
    generated_dir = (PRIVATE_GENERATED_DIR / str(user_id)).resolve()
    for output_path in output_paths:
        _unlink_owned_file(output_path, generated_dir)
    avatar_dir = (PRIVATE_STORAGE_DIR / "avatars" / str(user_id)).resolve()
    for avatar_path in avatar_paths:
        _unlink_owned_file(avatar_path, avatar_dir)
    return True


def delete_participant_workflow(participant_id, user_id):
    participant = get_participant(participant_id, user_id)
    if participant is None or not delete_participant(participant_id, user_id):
        return False
    _unlink_owned_file(
        participant[4],
        (PRIVATE_STORAGE_DIR / "avatars" / str(user_id)).resolve(),
    )
    return True


def _unlink_owned_file(path, owner_dir):
    if path:
        candidate = Path(path).resolve()
        if candidate.parent == owner_dir:
            candidate.unlink(missing_ok=True)


def _render_chat(chat, participants, messages):
    platform = (chat[1] or "whatsapp").strip().lower()
    if platform in {"whatsapp", "wa"}:
        return render_whatsapp(chat, participants, messages)
    if platform == "instagram":
        return render_instagram(chat, participants, messages)
    if platform == "chatgpt":
        return render_chatgpt(chat, participants, messages)
    raise ValueError(f"Unsupported platform: {platform}")
