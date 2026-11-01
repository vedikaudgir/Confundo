from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy import select

from server.auth_dependencies import get_current_user
from server.config import PRIVATE_STORAGE_DIR
from server.database import session_scope
from server.models import Chat, GenerationHistory, User
from server.schemas.history_schema import HistoryResponse
from server.services.chat_service import get_history_image


router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=list[HistoryResponse])
def list_history(user: User = Depends(get_current_user)):
    with session_scope() as session:
        rows = session.execute(
            select(GenerationHistory, Chat)
            .join(Chat, Chat.id == GenerationHistory.chat_id)
            .where(GenerationHistory.user_id == user.id)
            .order_by(GenerationHistory.created_at.desc(), GenerationHistory.id.desc())
        ).all()
        return [
            {
                "id": history.id,
                "chat_id": chat.id,
                "title": chat.title,
                "platform": chat.platform,
                "created_at": history.created_at,
                "image_url": f"/history/{history.id}/image",
            }
            for history, chat in rows
        ]


@router.get("/{history_id}/image")
def get_history_output(history_id: int, user: User = Depends(get_current_user)):
    path = get_history_image(history_id, user.id)
    if path is None:
        raise HTTPException(status_code=404, detail="Generation not found")
    return FileResponse(path, media_type="image/png", headers={"Cache-Control": "private, no-store"})


@router.delete("/{history_id}", status_code=204)
def delete_history(history_id: int, user: User = Depends(get_current_user)):
    with session_scope() as session:
        history = session.scalar(
            select(GenerationHistory).where(
                GenerationHistory.id == history_id,
                GenerationHistory.user_id == user.id,
            )
        )
        if history is None:
            raise HTTPException(status_code=404, detail="Generation not found")
        path = Path(history.output_path).resolve()
        session.delete(history)
    owner_dir = (PRIVATE_STORAGE_DIR / "generated" / str(user.id)).resolve()
    if path.parent == owner_dir:
        path.unlink(missing_ok=True)
    return Response(status_code=204)
