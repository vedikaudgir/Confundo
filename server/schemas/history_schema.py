from datetime import datetime

from pydantic import BaseModel


class HistoryResponse(BaseModel):
    id: int
    chat_id: int
    title: str
    platform: str
    created_at: datetime
    image_url: str
