from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints


ParticipantName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)
]


class AddParticipantRequest(BaseModel):
    name: ParticipantName
    role: str = Field(pattern="^(me|other)$")


class UpdateParticipantRequest(BaseModel):
    name: ParticipantName


class ParticipantResponse(BaseModel):
    id: int
    name: str
    role: str


class AvatarResponse(BaseModel):
    status: str
    avatar_url: str


class OperationStatusResponse(BaseModel):
    status: str
