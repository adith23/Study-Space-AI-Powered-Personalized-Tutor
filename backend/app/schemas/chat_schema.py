from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# Chat message response schema
class ChatMessageResponse(BaseModel):
    role: str
    content: str

    model_config = ConfigDict(from_attributes=True)

# Chat session response schema
class ChatSessionResponse(BaseModel):
    id: UUID
    name: str

    model_config = ConfigDict(from_attributes=True)

# Conversational chat request schema
class ConversationalChatRequest(BaseModel):
    query: str
    session_id: UUID
    file_ids: List[int]

# Chat response schema
class ChatResponse(BaseModel):
    answer: str
