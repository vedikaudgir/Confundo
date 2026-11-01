from typing import Annotated, Any

from pydantic import BaseModel, Field, StringConstraints


MessageContent = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)
]
MessageTimestamp = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)
]


class AddMessageRequest(BaseModel):
    sender_role: str = Field(pattern="^(me|other)$")
    type: str = Field(default="text", min_length=1, max_length=32)
    content: MessageContent
    timestamp: MessageTimestamp
    direction: str = Field(pattern="^(inbound|outbound)$")
    reply_to: int | None = Field(default=None, gt=0)
    meta: dict[str, Any] | None = None


class UpdateMessageRequest(BaseModel):
    content: MessageContent
    timestamp: MessageTimestamp


class MessageResponse(BaseModel):
    id: int
    sender_id: int
    sender_role: str
    type: str
    content: str
    timestamp: str
    direction: str
    position: int
    reply_to: int | None = None
    meta: dict[str, Any] | None = None


class MessageCreatedResponse(BaseModel):
    status: str
    message_id: int


class OperationStatusResponse(BaseModel):
    status: str
