from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user_model import User
from app.schemas.chat_schema import (
    ChatMessageResponse,
    ChatResponse,
    ChatSessionResponse,
    ConversationalChatRequest,
)
from app.services.chat_service import run_conversational_chat
from app.services.chat_session_service import (
    create_chat_session,
    list_chat_session_messages,
    list_user_chat_sessions,
)

router = APIRouter()

# Create a chat session
@router.post("/chat/sessions", response_model=ChatSessionResponse, status_code=201)
def create_session(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return create_chat_session(db=db, current_user=current_user)

# List all chat sessions for a user
@router.get("/chat/sessions", response_model=List[ChatSessionResponse])
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return list_user_chat_sessions(db=db, current_user=current_user)

# List all messages for a chat session
@router.get("/chat/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
def list_session_messages(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return list_chat_session_messages(
        session_id=session_id,
        db=db,
        current_user=current_user,
    )

# Run a conversational chat
@router.post("/chat", response_model=ChatResponse)
async def conversational_chat(
    request: ConversationalChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return await run_conversational_chat(
        request=request,
        db=db,
        current_user=current_user,
    )
