from typing import List
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.chat_model import ChatMessage, ChatSession
from app.models.user_model import User


# Get an owned chat session
def _get_owned_chat_session(
    *, session_id: UUID, db: Session, current_user: User
) -> ChatSession:
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
        .first()
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session

# Create a chat session 
def create_chat_session(*, db: Session, current_user: User) -> ChatSession:
    new_session = ChatSession(user_id=current_user.id)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

# List all chat sessions for a user
def list_user_chat_sessions(*, db: Session, current_user: User) -> List[ChatSession]:
    return (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.created_at.desc())
        .all()
    )

# Get a chat session
def get_chat_session(*, session_id: UUID, db: Session, current_user: User) -> ChatSession:
    return _get_owned_chat_session(
        session_id=session_id,
        db=db,
        current_user=current_user,
    )

# List all messages for a chat session
def list_chat_session_messages(
    *, session_id: UUID, db: Session, current_user: User
) -> List[ChatMessage]:
    session = _get_owned_chat_session(
        session_id=session_id,
        db=db,
        current_user=current_user,
    )
    return list(session.messages)
