"""
Flashcard service unit tests and Flashcard API integration tests.

Covers: FLASH-UNIT-001 through FLASH-UNIT-005
        FLASH-INT-001 through FLASH-INT-003

See qa_testing_plan.md Sections 6.5 and 7.6.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from app.models.material_model import UploadedFile, FileType, ProcessingStatus
from app.models.flashcard_model import FlashcardDeck, FlashcardDeckSource, Flashcard
from app.models.quiz_model import QuizDifficulty, QuizGenerationMode, QuizStatus
from app.schemas.flashcard_schema import CreateFlashcardDeckRequest
from app.services.flashcard_service import (
    create_flashcard_deck,
    list_flashcard_decks,
    get_flashcard_deck_or_404,
)


# ==========================================================================
# Helpers
# ==========================================================================

def _create_processed_file(db_session, user, name="test.pdf"):
    """Helper: create a fully processed UploadedFile for a user."""
    f = UploadedFile(
        name=name,
        file_type=FileType.pdf,
        status=ProcessingStatus.SUCCESS,
        user_id=user.id,
    )
    db_session.add(f)
    db_session.commit()
    db_session.refresh(f)
    return f


def _create_flashcard_deck_with_cards(db_session, user, file_record, num_cards=5):
    """Helper: create a READY flashcard deck with cards."""
    deck = FlashcardDeck(
        user_id=user.id,
        title="Test Deck",
        difficulty_level=QuizDifficulty.EASY,
        number_of_cards=num_cards,
        generation_mode=QuizGenerationMode.BROAD_FULL_SOURCE,
        status=QuizStatus.READY,
    )
    db_session.add(deck)
    db_session.flush()

    db_session.add(FlashcardDeckSource(deck_id=deck.id, uploaded_file_id=file_record.id))

    for i in range(1, num_cards + 1):
        db_session.add(Flashcard(
            deck_id=deck.id,
            front_text=f"Term {i}",
            back_text=f"Definition {i}",
            card_order=i,
        ))

    db_session.commit()
    db_session.refresh(deck)
    return deck


# ==========================================================================
# FLASH-UNIT-001 through 005
# ==========================================================================


class TestCreateFlashcardDeck:
    """FLASH-UNIT-001: Flashcard deck is created with correct metadata."""

    @patch("app.services.flashcard_service.get_valid_selected_files")
    def test_creates_deck_with_correct_metadata(self, mock_validate, db_session, test_user):
        """FLASH-UNIT-001: Deck has correct title, difficulty, and PENDING status."""
        file_record = _create_processed_file(db_session, test_user)
        mock_validate.return_value = [file_record]

        request = CreateFlashcardDeckRequest(
            file_ids=[file_record.id],
            number_of_cards=10,
            difficulty_level=QuizDifficulty.MEDIUM,
            title="Biology Flashcards",
        )
        result = create_flashcard_deck(
            db=db_session, current_user=test_user, request=request
        )
        assert result.status == QuizStatus.PENDING
        assert result.number_of_cards == 10
        assert result.title == "Biology Flashcards"
        assert result.difficulty_level == QuizDifficulty.MEDIUM


class TestListFlashcardDecks:
    """FLASH-UNIT-002: Only current user's flashcard decks are returned."""

    def test_returns_only_current_user_decks(self, db_session, test_user, second_user):
        """FLASH-UNIT-002: list_flashcard_decks filters by user."""
        file_a = _create_processed_file(db_session, test_user, "a.pdf")
        file_b = _create_processed_file(db_session, second_user, "b.pdf")

        _create_flashcard_deck_with_cards(db_session, test_user, file_a)
        _create_flashcard_deck_with_cards(db_session, test_user, file_a)
        _create_flashcard_deck_with_cards(db_session, second_user, file_b)

        results = list_flashcard_decks(db=db_session, current_user=test_user)
        assert len(results) == 2


class TestGetFlashcardDeckOr404:
    """FLASH-UNIT-003, 004: get_flashcard_deck_or_404."""

    def test_raises_404_for_other_users_deck(self, db_session, test_user, second_user):
        """FLASH-UNIT-003: Raises 404 when deck belongs to a different user."""
        file_record = _create_processed_file(db_session, second_user)
        deck = _create_flashcard_deck_with_cards(db_session, second_user, file_record)

        with pytest.raises(HTTPException) as exc_info:
            get_flashcard_deck_or_404(
                db=db_session, current_user=test_user, deck_id=deck.id
            )
        assert exc_info.value.status_code == 404

    def test_raises_404_for_nonexistent_deck(self, db_session, test_user):
        """FLASH-UNIT-004: Raises 404 for a deck that doesn't exist."""
        with pytest.raises(HTTPException) as exc_info:
            get_flashcard_deck_or_404(
                db=db_session, current_user=test_user, deck_id=99999
            )
        assert exc_info.value.status_code == 404


class TestSharedEnumRegression:
    """FLASH-UNIT-005: Shared quiz enums are valid for flashcard context."""

    def test_shared_enums_valid_for_flashcards(self):
        """FLASH-UNIT-005: QuizDifficulty and QuizStatus values make sense for flashcards."""
        # All difficulty levels should be valid for flashcards
        valid_difficulties = {d.value for d in QuizDifficulty}
        assert valid_difficulties == {"easy", "medium", "hard"}

        # All status values should apply to flashcard decks too
        valid_statuses = {s.value for s in QuizStatus}
        assert "pending" in valid_statuses
        assert "ready" in valid_statuses
        assert "failed" in valid_statuses


# ==========================================================================
# FLASH-INT-001 through 003: Flashcard API integration tests
# ==========================================================================


class TestFlashcardAPICreate:
    """FLASH-INT-001: POST /api/v1/materials/flashcards."""

    @patch("app.tasks.flashcard_tasks.generate_flashcard_deck_task")
    @patch("app.services.flashcard_service.get_valid_selected_files")
    def test_create_deck_dispatches_celery(
        self, mock_validate, mock_task, client, db_session, test_user, auth_headers
    ):
        """FLASH-INT-001: POST /flashcards creates deck and dispatches Celery task."""
        file_record = _create_processed_file(db_session, test_user)
        mock_validate.return_value = [file_record]

        response = client.post(
            "/api/v1/materials/flashcards",
            headers=auth_headers,
            json={
                "file_ids": [file_record.id],
                "number_of_cards": 10,
                "difficulty_level": "easy",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        mock_task.delay.assert_called_once_with(data["id"])


class TestFlashcardAPIList:
    """FLASH-INT-002, 003: GET /api/v1/materials/flashcards."""

    def test_list_returns_only_current_user_decks(
        self, client, db_session, test_user, second_user,
        auth_headers, second_user_headers
    ):
        """FLASH-INT-002: GET /flashcards returns only current user's decks."""
        file_a = _create_processed_file(db_session, test_user, "a.pdf")
        file_b = _create_processed_file(db_session, second_user, "b.pdf")

        _create_flashcard_deck_with_cards(db_session, test_user, file_a)
        _create_flashcard_deck_with_cards(db_session, second_user, file_b)

        response = client.get("/api/v1/materials/flashcards", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_get_deck_returns_404_for_other_user(
        self, client, db_session, test_user, second_user, second_user_headers
    ):
        """FLASH-INT-003: GET /flashcards/{id} returns 404 for other user's deck."""
        file_record = _create_processed_file(db_session, test_user)
        deck = _create_flashcard_deck_with_cards(db_session, test_user, file_record)

        response = client.get(
            f"/api/v1/materials/flashcards/{deck.id}",
            headers=second_user_headers,
        )
        assert response.status_code == 404
