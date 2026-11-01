from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy import select

from server.auth_dependencies import get_current_user
from server.config import PRIVATE_STORAGE_DIR
from server.database import session_scope
from server.models import Chat, User
from server.repositories.chat_repository import get_chat, get_chat_record
from server.schemas.chat_schema import (
    ChatDetailResponse,
    ChatResponse,
    CreateChatRequest,
    CreateChatResponse,
    OperationStatusResponse,
    UpdateChatRequest,
)
from server.services.chat_service import (
    create_chat_workflow,
    delete_chat_workflow,
    generate_chat_image,
    generate_preview,
    get_chat_state,
    update_chat_workflow,
)


router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("", response_model=list[ChatResponse])
def list_chats(
    user: User = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    with session_scope() as session:
        return session.scalars(
            select(Chat)
            .where(Chat.user_id == user.id)
            .order_by(Chat.updated_at.desc(), Chat.id.desc())
            .offset(offset)
            .limit(limit)
        ).all()


@router.post("", response_model=CreateChatResponse)
def create_chat(data: CreateChatRequest, user: User = Depends(get_current_user)):
    try:
        result = create_chat_workflow(
            user.id,
            data.platform,
            data.title,
            data.subtitle,
            data.theme,
            data.my_name,
            data.other_name,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {
        "chat_id": result["chat_id"],
        "preview_url": f"/chats/{result['chat_id']}/preview",
        "me_id": result["me_id"],
        "other_id": result["other_id"],
    }


@router.get("/{chat_id}/data", response_model=ChatDetailResponse)
def get_chat_data(chat_id: int, user: User = Depends(get_current_user)):
    state = get_chat_state(chat_id, user.id)
    if state is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    chat_record = get_chat_record(chat_id, user.id)
    if chat_record is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    chat_id_value, platform, title, subtitle, theme = state["chat"]
    participant_rows = state["participants"]
    roles = {row[0]: row[3] for row in participant_rows}
    message_rows = state["messages"]
    return {
        "id": chat_id_value,
        "platform": platform,
        "title": title,
        "subtitle": subtitle,
        "theme": theme,
        "created_at": chat_record.created_at,
        "updated_at": chat_record.updated_at,
        "participants": [
            {"id": row[0], "name": row[2], "role": row[3]} for row in participant_rows
        ],
        "messages": [
            {
                "id": row[0],
                "sender_id": row[2],
                "sender_role": roles.get(row[2], "other"),
                "message_type": row[3],
                "content": row[4],
                "timestamp": row[5],
                "position": index,
                "direction": row[6],
            }
            for index, row in enumerate(message_rows, start=1)
        ],
    }


@router.patch("/{chat_id}", response_model=OperationStatusResponse)
def update_chat(
    chat_id: int,
    data: UpdateChatRequest,
    user: User = Depends(get_current_user),
):
    current = get_chat(chat_id, user.id)
    if current is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    values = data.model_dump(exclude_unset=True, exclude_none=True)
    try:
        result = update_chat_workflow(
            chat_id,
            user.id,
            values.get("platform", current[1]),
            values.get("title", current[2]),
            values.get("subtitle", current[3]),
            values.get("theme", current[4]),
            values.get("my_name"),
            values.get("other_name"),
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if not result:
        raise HTTPException(status_code=404, detail="Chat not found")
    return result


@router.delete("/{chat_id}", status_code=204)
def delete_chat(chat_id: int, user: User = Depends(get_current_user)):
    output_path = PRIVATE_STORAGE_DIR / "generated" / str(user.id) / f"chat_{chat_id}.png"
    if not delete_chat_workflow(chat_id, user.id):
        raise HTTPException(status_code=404, detail="Chat not found")
    output_path.unlink(missing_ok=True)
    return Response(status_code=204)


@router.get("/{chat_id}")
@router.get("/{chat_id}/preview")
def preview(chat_id: int, user: User = Depends(get_current_user)):
    path = generate_preview(chat_id, user.id)
    if not path:
        raise HTTPException(status_code=404, detail="Chat not found")
    return FileResponse(
        Path(path),
        media_type="image/png",
        headers={"Cache-Control": "private, no-store"},
    )


@router.post("/{chat_id}/generate")
def generate(chat_id: int, user: User = Depends(get_current_user)):
    path = generate_chat_image(chat_id, user.id)
    if not path:
        raise HTTPException(status_code=404, detail="Chat not found")
    return FileResponse(
        Path(path),
        media_type="image/png",
        headers={"Cache-Control": "private, no-store"},
    )
