from datetime import datetime

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


ChatTitle = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
ParticipantName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]


class CreateChatRequest(BaseModel):
    platform: str = Field(default="whatsapp", min_length=2, max_length=32)
    title: ChatTitle = "My Chat"
    subtitle: str = Field(default="", max_length=120)
    theme: str = Field(default="light", pattern="^(light|dark)$")
    my_name: ParticipantName = "You"
    other_name: Annotated[str, StringConstraints(strip_whitespace=True, max_length=60)] | None = None


class UpdateChatRequest(BaseModel):
    platform: str | None = Field(default=None, min_length=2, max_length=32)
    title: ChatTitle | None = None
    subtitle: str | None = Field(default=None, max_length=120)
    theme: str | None = Field(default=None, pattern="^(light|dark)$")
    my_name: Annotated[str, StringConstraints(strip_whitespace=True, max_length=60)] | None = None
    other_name: Annotated[str, StringConstraints(strip_whitespace=True, max_length=60)] | None = None


class ChatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    platform: str
    title: str
    subtitle: str
    theme: str
    created_at: datetime
    updated_at: datetime


class ParticipantResponse(BaseModel):
    id: int
    name: str
    role: str


class MessageResponse(BaseModel):
    id: int
    sender_id: int
    sender_role: str
    message_type: str
    content: str
    timestamp: str
    position: int
    direction: str


class ChatDetailResponse(ChatResponse):
    participants: list[ParticipantResponse]
    messages: list[MessageResponse]


class CreateChatResponse(BaseModel):
    chat_id: int
    preview_url: str
    me_id: int
    other_id: int


class OperationStatusResponse(BaseModel):
    status: str
