from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user_model import User
from app.schemas.flashcard_schema import (
    CreateFlashcardDeckRequest,
    FlashcardDeckDetailResponse,
    FlashcardDeckResponse,
)
from app.services.flashcard_service import (
    create_flashcard_deck,
    get_flashcard_deck_detail,
    list_flashcard_decks,
)
from app.tasks.flashcard_tasks import generate_flashcard_deck_task

router = APIRouter()


@router.post("/flashcards", response_model=FlashcardDeckResponse)
def create_flashcard_deck_route(
    request: CreateFlashcardDeckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    deck = create_flashcard_deck(db=db, current_user=current_user, request=request)
    generate_flashcard_deck_task.delay(deck.id)
    return deck


@router.get("/flashcards", response_model=list[FlashcardDeckResponse])
def list_flashcard_decks_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return list_flashcard_decks(db=db, current_user=current_user)


@router.get("/flashcards/{deck_id}", response_model=FlashcardDeckDetailResponse)
def get_flashcard_deck_route(
    deck_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return get_flashcard_deck_detail(
        db=db,
        current_user=current_user,
        deck_id=deck_id,
    )
