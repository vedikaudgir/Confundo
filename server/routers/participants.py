from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import select

from server.auth_dependencies import get_current_user
from server.config import MAX_AVATAR_BYTES, MAX_AVATAR_PIXELS, PRIVATE_STORAGE_DIR
from server.database import session_scope
from server.models import Chat, Participant, User
from server.repositories.participant_repository import (
    add_participant,
    get_participant,
    get_participants,
    update_avatar,
    update_participant_name,
)
from server.schemas.participant_schema import (
    AddParticipantRequest,
    AvatarResponse,
    OperationStatusResponse,
    ParticipantResponse,
    UpdateParticipantRequest,
)
from server.services.chat_service import delete_participant_workflow


router = APIRouter(prefix="/participants", tags=["participants"])
PRIVATE_AVATAR_DIR = PRIVATE_STORAGE_DIR / "avatars"
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


@router.get("/chats/{chat_id}", response_model=list[ParticipantResponse])
def list_participants(chat_id: int, user: User = Depends(get_current_user)):
    rows = get_participants(chat_id, user.id)
    if not rows:
        with session_scope() as session:
            owns_chat = session.scalar(
                select(Chat.id).where(Chat.id == chat_id, Chat.user_id == user.id)
            )
        if owns_chat is None:
            raise HTTPException(status_code=404, detail="Chat not found")
    return [{"id": row[0], "name": row[2], "role": row[3]} for row in rows]


@router.post("/chats/{chat_id}", status_code=201, response_model=ParticipantResponse)
def create_participant(
    chat_id: int,
    data: AddParticipantRequest,
    user: User = Depends(get_current_user),
):
    participant_id = add_participant(chat_id, user.id, data.name.strip(), data.role)
    if participant_id is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"id": participant_id, "name": data.name.strip(), "role": data.role}


@router.patch("/{participant_id}", response_model=OperationStatusResponse)
def update_participant(
    participant_id: int,
    data: UpdateParticipantRequest,
    user: User = Depends(get_current_user),
):
    participant = get_participant(participant_id, user.id)
    if participant is None:
        raise HTTPException(status_code=404, detail="Participant not found")
    update_participant_name(participant_id, user.id, data.name.strip())
    return {"status": "participant updated"}


@router.delete("/{participant_id}", status_code=204)
def delete_participant(participant_id: int, user: User = Depends(get_current_user)):
    participant = get_participant(participant_id, user.id)
    if participant is None:
        raise HTTPException(status_code=404, detail="Participant not found")
    if not delete_participant_workflow(participant_id, user.id):
        raise HTTPException(status_code=404, detail="Participant not found")
    return None


@router.post("/{participant_id}/avatar", response_model=AvatarResponse)
def upload_avatar(
    participant_id: int,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    participant = get_participant(participant_id, user.id)
    if participant is None:
        raise HTTPException(status_code=404, detail="Participant not found")
    image_data = file.file.read(MAX_AVATAR_BYTES + 1)
    if len(image_data) > MAX_AVATAR_BYTES:
        raise HTTPException(status_code=413, detail="Avatar must be 5 MB or smaller")
    try:
        with Image.open(BytesIO(image_data)) as image:
            if image.format not in ALLOWED_IMAGE_FORMATS:
                raise HTTPException(status_code=415, detail="Avatar must be JPEG, PNG, or WebP")
            if image.width * image.height > MAX_AVATAR_PIXELS:
                raise HTTPException(status_code=413, detail="Avatar image dimensions are too large")
            image.verify()
        with Image.open(BytesIO(image_data)) as image:
            normalized = ImageOps.exif_transpose(image).convert("RGBA")
            normalized.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            output = BytesIO()
            normalized.save(output, format="PNG", optimize=True)
    except HTTPException:
        raise
    except (
        OSError,
        SyntaxError,
        ValueError,
        UnidentifiedImageError,
        Image.DecompressionBombError,
    ) as error:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image") from error

    owner_dir = PRIVATE_AVATAR_DIR / str(user.id)
    owner_dir.mkdir(parents=True, exist_ok=True)
    path = owner_dir / f"{uuid4().hex}.png"
    path.write_bytes(output.getvalue())
    previous_path = participant[4]
    if not update_avatar(participant_id, user.id, str(path.resolve())):
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=404, detail="Participant not found")
    if previous_path:
        old_path = Path(previous_path).resolve()
        if old_path.parent == owner_dir.resolve():
            old_path.unlink(missing_ok=True)
    return {"status": "avatar updated", "avatar_url": f"/participants/{participant_id}/avatar"}


@router.get("/{participant_id}/avatar")
def get_avatar(participant_id: int, user: User = Depends(get_current_user)):
    participant = get_participant(participant_id, user.id)
    if participant is None or not participant[4]:
        raise HTTPException(status_code=404, detail="Avatar not found")
    path = Path(participant[4]).resolve()
    owner_dir = (PRIVATE_AVATAR_DIR / str(user.id)).resolve()
    if path.parent != owner_dir or not path.is_file():
        raise HTTPException(status_code=404, detail="Avatar not found")
    return FileResponse(path, media_type="image/png", headers={"Cache-Control": "private, no-store"})
