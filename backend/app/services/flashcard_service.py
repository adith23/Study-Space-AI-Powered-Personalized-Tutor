from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.flashcard_model import Flashcard, FlashcardDeck, FlashcardDeckSource
from app.models.quiz_model import QuizGenerationMode, QuizStatus
from app.models.user_model import User
from app.schemas.flashcard_schema import (
    CreateFlashcardDeckRequest,
    FlashcardDeckDetailResponse,
    FlashcardDeckResponse,
    FlashcardDeckSourceResponse,
    FlashcardResponse,
    GeneratedFlashcardPayload,
)
from app.services.content_generation_context_service import (
    build_content_generation_context,
    get_valid_selected_files,
)
from app.services.flashcard_generation_service import generate_flashcard_payload


def create_flashcard_deck(
    *, db: Session, current_user: User, request: CreateFlashcardDeckRequest
) -> FlashcardDeckResponse:
    try:
        files = get_valid_selected_files(
            db=db,
            current_user=current_user,
            file_ids=request.file_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    generation_mode = (
        QuizGenerationMode.FOCUSED_RAG
        if request.focus_prompt
        else QuizGenerationMode.BROAD_FULL_SOURCE
    )
    title = request.title or _default_deck_title(files)
    deck = FlashcardDeck(
        user_id=current_user.id,
        title=title,
        difficulty_level=request.difficulty_level,
        number_of_cards=request.number_of_cards,
        focus_prompt=request.focus_prompt,
        generation_mode=generation_mode,
        status=QuizStatus.PENDING,
    )
    db.add(deck)
    db.flush()

    for file in files:
        db.add(FlashcardDeckSource(deck_id=deck.id, uploaded_file_id=file.id))

    db.commit()
    db.refresh(deck)
    return FlashcardDeckResponse.model_validate(deck)


def list_flashcard_decks(
    *, db: Session, current_user: User
) -> list[FlashcardDeckResponse]:
    decks = (
        db.query(FlashcardDeck)
        .filter(FlashcardDeck.user_id == current_user.id)
        .order_by(FlashcardDeck.created_at.desc(), FlashcardDeck.id.desc())
        .all()
    )
    return [FlashcardDeckResponse.model_validate(deck) for deck in decks]


def get_flashcard_deck_or_404(
    *, db: Session, current_user: User, deck_id: int
) -> FlashcardDeck:
    deck = (
        db.query(FlashcardDeck)
        .options(
            joinedload(FlashcardDeck.sources).joinedload(
                FlashcardDeckSource.uploaded_file
            ),
            joinedload(FlashcardDeck.cards),
        )
        .filter(FlashcardDeck.id == deck_id, FlashcardDeck.user_id == current_user.id)
        .first()
    )
    if deck is None:
        raise HTTPException(status_code=404, detail="Flashcard deck not found.")
    return deck


def get_flashcard_deck_detail(
    *, db: Session, current_user: User, deck_id: int
) -> FlashcardDeckDetailResponse:
    deck = get_flashcard_deck_or_404(db=db, current_user=current_user, deck_id=deck_id)
    return _serialize_flashcard_deck_detail(deck)


def generate_flashcard_deck_for_id(*, db: Session, deck_id: int) -> None:
    deck = (
        db.query(FlashcardDeck)
        .options(
            joinedload(FlashcardDeck.sources).joinedload(
                FlashcardDeckSource.uploaded_file
            )
        )
        .filter(FlashcardDeck.id == deck_id)
        .first()
    )
    if deck is None:
        raise ValueError(f"Flashcard deck {deck_id} not found.")
    if deck.status == QuizStatus.READY and deck.cards:
        return

    deck.status = QuizStatus.GENERATING
    deck.error_message = None
    db.commit()
    db.refresh(deck)

    files = [source.uploaded_file for source in deck.sources]
    if not files:
        _mark_deck_failed(
            db=db, deck=deck, error_message="Flashcard deck has no selected sources."
        )
        return

    current_user = deck.user
    try:
        context = build_content_generation_context(
            db=db,
            current_user=current_user,
            files=files,
            focus_prompt=deck.focus_prompt,
            item_count=deck.number_of_cards,
        )
        payload = generate_flashcard_payload(
            context=context,
            difficulty_level=deck.difficulty_level,
            number_of_cards=deck.number_of_cards,
            focus_prompt=deck.focus_prompt,
        )
        _persist_generated_cards(db=db, deck=deck, payload=payload)
        deck.status = QuizStatus.READY
        deck.error_message = None
        db.commit()
    except Exception as exc:
        db.rollback()
        deck = db.query(FlashcardDeck).filter(FlashcardDeck.id == deck_id).first()
        if deck is not None:
            _mark_deck_failed(db=db, deck=deck, error_message=str(exc))
        raise


def _persist_generated_cards(
    *, db: Session, deck: FlashcardDeck, payload: GeneratedFlashcardPayload
) -> None:
    db.query(Flashcard).filter(Flashcard.deck_id == deck.id).delete()
    for index, card in enumerate(payload.cards, start=1):
        db.add(
            Flashcard(
                deck_id=deck.id,
                front_text=card.front_text,
                back_text=card.back_text,
                card_order=index,
                source_snippet=card.source_snippet,
                source_metadata=card.source_metadata,
            )
        )


def _mark_deck_failed(*, db: Session, deck: FlashcardDeck, error_message: str) -> None:
    deck.status = QuizStatus.FAILED
    deck.error_message = error_message[:500]
    db.commit()


def _default_deck_title(files: list) -> str:
    if len(files) == 1:
        return f"Flashcards: {files[0].name or f'Source {files[0].id}'}"
    first_name = files[0].name or f"Source {files[0].id}"
    return f"Flashcards: {first_name} + {len(files) - 1} more"


def _serialize_flashcard_deck_detail(
    deck: FlashcardDeck,
) -> FlashcardDeckDetailResponse:
    return FlashcardDeckDetailResponse(
        id=deck.id,
        title=deck.title,
        difficulty_level=deck.difficulty_level,
        number_of_cards=deck.number_of_cards,
        focus_prompt=deck.focus_prompt,
        generation_mode=deck.generation_mode,
        status=deck.status,
        error_message=deck.error_message,
        sources=[
            FlashcardDeckSourceResponse(
                uploaded_file_id=source.uploaded_file_id,
                name=source.uploaded_file.name if source.uploaded_file else None,
            )
            for source in deck.sources
        ],
        cards=[
            FlashcardResponse(
                id=card.id,
                front_text=card.front_text,
                back_text=card.back_text,
                card_order=card.card_order,
            )
            for card in sorted(deck.cards, key=lambda item: item.card_order)
        ],
    )
