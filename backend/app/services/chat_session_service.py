from typing import List
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.chat_model import ChatSession
from app.models.user_model import User


def create_chat_session(*, db: Session, current_user: User) -> ChatSession:
    new_session = ChatSession(user_id=current_user.id)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


def get_user_chat_sessions(*, db: Session, current_user: User) -> List[ChatSession]:
    return db.query(ChatSession).filter(ChatSession.user_id == current_user.id).all()


def get_chat_session_messages(
    *, session_id: UUID, db: Session, current_user: User
) -> list:
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session.messages
