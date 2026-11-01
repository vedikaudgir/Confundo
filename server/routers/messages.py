from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from server.auth_dependencies import get_current_user
from server.database import session_scope
from server.models import Chat, Message, Participant, User
from server.schemas.message_schema import (
    AddMessageRequest,
    MessageCreatedResponse,
    MessageResponse,
    OperationStatusResponse,
    UpdateMessageRequest,
)
from server.services.chat_service import (
    add_message_workflow,
    delete_message_workflow,
    edit_message_workflow,
)


router = APIRouter(tags=["messages"])


@router.get("/chats/{chat_id}/messages", response_model=list[MessageResponse])
def list_messages(chat_id: int, user: User = Depends(get_current_user)):
    with session_scope() as session:
        chat = session.scalar(select(Chat.id).where(Chat.id == chat_id, Chat.user_id == user.id))
        if chat is None:
            raise HTTPException(status_code=404, detail="Chat not found")
        messages = session.execute(
            select(Message, Participant.role)
            .outerjoin(Participant, Participant.id == Message.sender_id)
            .where(Message.chat_id == chat_id)
            .order_by(Message.position, Message.id)
        ).all()
        return [
            {
                "id": message.id,
                "sender_id": message.sender_id,
                "sender_role": role or "other",
                "type": message.message_type,
                "content": message.content,
                "timestamp": message.timestamp,
                "direction": message.direction,
                "position": message.position,
                "reply_to": message.reply_to,
                "meta": message.meta,
            }
            for message, role in messages
        ]


@router.post("/chats/{chat_id}/messages", response_model=MessageCreatedResponse)
def add_message(
    chat_id: int,
    data: AddMessageRequest,
    user: User = Depends(get_current_user),
):
    if not data.content.strip():
        raise HTTPException(status_code=422, detail="Message content cannot be empty")
    if data.reply_to is not None:
        with session_scope() as session:
            reply = session.scalar(
                select(Message.id)
                .join(Chat, Chat.id == Message.chat_id)
                .where(
                    Message.id == data.reply_to,
                    Message.chat_id == chat_id,
                    Chat.user_id == user.id,
                )
            )
        if reply is None:
            raise HTTPException(status_code=422, detail="Reply target is not in this chat")
    result = add_message_workflow(
        chat_id,
        user.id,
        data.sender_role,
        data.type,
        data.content.strip(),
        data.timestamp.strip(),
        data.direction,
        data.reply_to,
        data.meta,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Chat or participant not found")
    return result


@router.patch(
    "/chats/{chat_id}/messages/{message_id}",
    response_model=OperationStatusResponse,
)
def update_message(
    chat_id: int,
    message_id: int,
    data: UpdateMessageRequest,
    user: User = Depends(get_current_user),
):
    if not edit_message_workflow(
        chat_id, message_id, user.id, data.content.strip(), data.timestamp.strip()
    ):
        raise HTTPException(status_code=404, detail="Message not found")
    return {"status": "message updated"}


@router.delete(
    "/chats/{chat_id}/messages/{message_id}",
    response_model=OperationStatusResponse,
)
def delete_message(chat_id: int, message_id: int, user: User = Depends(get_current_user)):
    if not delete_message_workflow(chat_id, message_id, user.id):
        raise HTTPException(status_code=404, detail="Message not found")
    return {"status": "message deleted"}
