from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Space(Base):
    """
    A Space is the top-level organizational container.
    Each user can create multiple spaces (e.g., "Linear Algebra", "Calculus").
    All content (files, chats, quizzes, flashcards, videos) belongs to a space.
    """

    __tablename__ = "spaces"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), default="layout-grid")
    color = Column(String(7), default="#00c875")
    content_count = Column(Integer, default=0)
    is_public = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_accessed_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User")
    files = relationship(
        "UploadedFile", back_populates="space", cascade="all, delete-orphan"
    )
    chat_sessions = relationship(
        "ChatSession", back_populates="space", cascade="all, delete-orphan"
    )
    flashcard_decks = relationship(
        "FlashcardDeck", back_populates="space", cascade="all, delete-orphan"
    )
    quizzes = relationship("Quiz", back_populates="space", cascade="all, delete-orphan")
    videos = relationship(
        "GeneratedVideo", back_populates="space", cascade="all, delete-orphan"
    )
