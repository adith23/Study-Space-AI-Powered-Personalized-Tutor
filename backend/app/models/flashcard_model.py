from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.quiz_model import QuizDifficulty, QuizGenerationMode, QuizStatus


class FlashcardDeck(Base):
    __tablename__ = "flashcard_decks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    difficulty_level = Column(Enum(QuizDifficulty), nullable=False)
    number_of_cards = Column(Integer, nullable=False)
    focus_prompt = Column(Text, nullable=True)
    generation_mode = Column(Enum(QuizGenerationMode), nullable=False)
    status = Column(Enum(QuizStatus), nullable=False, default=QuizStatus.PENDING)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User")
    sources = relationship(
        "FlashcardDeckSource",
        back_populates="deck",
        cascade="all, delete-orphan",
    )
    cards = relationship(
        "Flashcard",
        back_populates="deck",
        cascade="all, delete-orphan",
        order_by="Flashcard.card_order",
    )


class FlashcardDeckSource(Base):
    __tablename__ = "flashcard_deck_sources"

    id = Column(Integer, primary_key=True, index=True)
    deck_id = Column(
        Integer, ForeignKey("flashcard_decks.id"), nullable=False, index=True
    )
    uploaded_file_id = Column(
        Integer, ForeignKey("uploaded_files.id"), nullable=False, index=True
    )

    deck = relationship("FlashcardDeck", back_populates="sources")
    uploaded_file = relationship("UploadedFile")


class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(Integer, primary_key=True, index=True)
    deck_id = Column(
        Integer, ForeignKey("flashcard_decks.id"), nullable=False, index=True
    )
    front_text = Column(Text, nullable=False)
    back_text = Column(Text, nullable=False)
    card_order = Column(Integer, nullable=False)
    source_snippet = Column(Text, nullable=True)
    source_metadata = Column(JSON, nullable=True)

    deck = relationship("FlashcardDeck", back_populates="cards")
