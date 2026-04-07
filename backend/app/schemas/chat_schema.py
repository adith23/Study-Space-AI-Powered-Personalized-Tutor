from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ChatMessageResponse(BaseModel):
    role: str
    content: str

    model_config = ConfigDict(from_attributes=True)


class ChatSessionResponse(BaseModel):
    id: UUID
    name: str

    model_config = ConfigDict(from_attributes=True)


class ConversationalChatRequest(BaseModel):
    query: str
    session_id: UUID
    file_ids: List[int]


class ChatResponse(BaseModel):
    answer: str
