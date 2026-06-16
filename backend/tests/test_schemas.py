"""
Schema validation (Pydantic) unit tests.

Covers: SCHEMA-UNIT-001 through SCHEMA-UNIT-008

See qa_testing_plan.md Section 6.7.
"""

import uuid

import pytest
from pydantic import ValidationError

from app.models.quiz_model import QuizDifficulty
from app.schemas.chat_schema import ConversationalChatRequest
from app.schemas.flashcard_schema import CreateFlashcardDeckRequest
from app.schemas.quiz_schema import (CreateQuizRequest,
                                     SubmitQuizAnswerRequest,
                                     SubmitQuizAttemptRequest)
from app.schemas.user_schema import UserCreate
from app.schemas.video_schema import VideoGenerateRequest

# ==========================================================================
# SCHEMA-UNIT-001 through 008
# ==========================================================================


class TestUserCreateSchema:
    """SCHEMA-UNIT-001, 002: UserCreate validation."""

    def test_rejects_invalid_email(self):
        """SCHEMA-UNIT-001: UserCreate rejects invalid email format."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(username="user", email="not-an-email", password="Password123!")
        errors = exc_info.value.errors()
        assert any("email" in str(e["loc"]) for e in errors)

    def test_rejects_empty_password(self):
        """SCHEMA-UNIT-002: UserCreate rejects empty password (PRODBUG-2 fix applied).

        After the min_length=8 fix, empty and short passwords should be rejected.
        """
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(username="user", email="user@test.com", password="")
        errors = exc_info.value.errors()
        assert any("password" in str(e["loc"]) for e in errors)

    def test_rejects_short_password(self):
        """Supplementary: UserCreate rejects passwords shorter than 8 characters."""
        with pytest.raises(ValidationError):
            UserCreate(username="user", email="user@test.com", password="Short1!")

    def test_accepts_valid_user(self):
        """Supplementary: UserCreate accepts valid data."""
        user = UserCreate(
            username="validuser",
            email="valid@test.com",
            password="ValidPass123!",
        )
        assert user.username == "validuser"
        assert user.email == "valid@test.com"


class TestVideoGenerateRequestSchema:
    """SCHEMA-UNIT-003: VideoGenerateRequest validation."""

    def test_rejects_missing_file_ids(self):
        """SCHEMA-UNIT-003: VideoGenerateRequest raises ValidationError when file_ids is missing."""
        with pytest.raises(ValidationError) as exc_info:
            VideoGenerateRequest()
        errors = exc_info.value.errors()
        assert any("file_ids" in str(e["loc"]) for e in errors)

    def test_default_values(self):
        """Supplementary: VideoGenerateRequest has correct defaults."""
        req = VideoGenerateRequest(file_ids=[1, 2])
        assert req.renderer == "image"
        assert req.style == "explainer"
        assert req.focus_prompt is None


class TestCreateQuizRequestSchema:
    """SCHEMA-UNIT-004: CreateQuizRequest validation with boundary values."""

    def test_rejects_empty_file_ids(self):
        """SCHEMA-UNIT-004a: CreateQuizRequest rejects empty file_ids (min_length=1)."""
        with pytest.raises(ValidationError):
            CreateQuizRequest(
                file_ids=[],
                number_of_questions=5,
                difficulty_level=QuizDifficulty.MEDIUM,
            )

    def test_rejects_zero_questions(self):
        """SCHEMA-UNIT-004b: CreateQuizRequest rejects number_of_questions=0 (ge=1)."""
        with pytest.raises(ValidationError):
            CreateQuizRequest(
                file_ids=[1],
                number_of_questions=0,
                difficulty_level=QuizDifficulty.EASY,
            )

    def test_rejects_21_questions(self):
        """SCHEMA-UNIT-004c: CreateQuizRequest rejects number_of_questions=21 (le=20)."""
        with pytest.raises(ValidationError):
            CreateQuizRequest(
                file_ids=[1],
                number_of_questions=21,
                difficulty_level=QuizDifficulty.HARD,
            )

    def test_rejects_missing_difficulty(self):
        """SCHEMA-UNIT-004d: CreateQuizRequest rejects missing difficulty_level."""
        with pytest.raises(ValidationError):
            CreateQuizRequest(
                file_ids=[1],
                number_of_questions=5,
                # difficulty_level is missing
            )

    def test_accepts_valid_quiz_request(self):
        """Supplementary: CreateQuizRequest accepts valid data with boundary values."""
        # Minimum values
        req_min = CreateQuizRequest(
            file_ids=[1],
            number_of_questions=1,
            difficulty_level=QuizDifficulty.EASY,
        )
        assert req_min.number_of_questions == 1

        # Maximum values
        req_max = CreateQuizRequest(
            file_ids=[1, 2, 3],
            number_of_questions=20,
            difficulty_level=QuizDifficulty.HARD,
        )
        assert req_max.number_of_questions == 20

    def test_optional_fields_default_to_none(self):
        """Supplementary: focus_prompt and title default to None."""
        req = CreateQuizRequest(
            file_ids=[1],
            number_of_questions=5,
            difficulty_level=QuizDifficulty.MEDIUM,
        )
        assert req.focus_prompt is None
        assert req.title is None

    def test_whitespace_only_title_becomes_none(self):
        """Supplementary: Whitespace-only title is normalized to None by field_validator."""
        req = CreateQuizRequest(
            file_ids=[1],
            number_of_questions=5,
            difficulty_level=QuizDifficulty.MEDIUM,
            title="   ",
        )
        assert req.title is None


class TestSubmitQuizAnswerSchema:
    """SCHEMA-UNIT-005, 006: Quiz answer validation."""

    def test_accepts_valid_attempt(self):
        """SCHEMA-UNIT-005: SubmitQuizAttemptRequest accepts valid answers."""
        attempt = SubmitQuizAttemptRequest(
            answers=[
                SubmitQuizAnswerRequest(question_id=1, selected_option="A"),
                SubmitQuizAnswerRequest(question_id=2, selected_option="B"),
                SubmitQuizAnswerRequest(question_id=3, selected_option="C"),
                SubmitQuizAnswerRequest(question_id=4, selected_option="D"),
            ]
        )
        assert len(attempt.answers) == 4

    def test_rejects_invalid_option_e(self):
        """SCHEMA-UNIT-006a: SubmitQuizAnswerRequest rejects option 'E'."""
        with pytest.raises(ValidationError):
            SubmitQuizAnswerRequest(question_id=1, selected_option="E")

    def test_rejects_empty_option(self):
        """SCHEMA-UNIT-006b: SubmitQuizAnswerRequest rejects empty selected_option."""
        with pytest.raises(ValidationError):
            SubmitQuizAnswerRequest(question_id=1, selected_option="")

    def test_normalizes_lowercase_to_uppercase(self):
        """Supplementary: lowercase options are normalized to uppercase."""
        answer = SubmitQuizAnswerRequest(question_id=1, selected_option="a")
        assert answer.selected_option == "A"

    def test_rejects_empty_answers_list(self):
        """Supplementary: SubmitQuizAttemptRequest rejects an empty answers list."""
        with pytest.raises(ValidationError):
            SubmitQuizAttemptRequest(answers=[])


class TestFlashcardDeckRequestSchema:
    """SCHEMA-UNIT-007: CreateFlashcardDeckRequest boundary validation."""

    def test_rejects_zero_cards(self):
        """SCHEMA-UNIT-007a: Rejects number_of_cards=0 (ge=1)."""
        with pytest.raises(ValidationError):
            CreateFlashcardDeckRequest(
                file_ids=[1],
                number_of_cards=0,
                difficulty_level=QuizDifficulty.EASY,
            )

    def test_rejects_31_cards(self):
        """SCHEMA-UNIT-007b: Rejects number_of_cards=31 (le=30)."""
        with pytest.raises(ValidationError):
            CreateFlashcardDeckRequest(
                file_ids=[1],
                number_of_cards=31,
                difficulty_level=QuizDifficulty.EASY,
            )

    def test_accepts_boundary_values(self):
        """Supplementary: Accepts 1 and 30 cards (inclusive boundaries)."""
        deck_min = CreateFlashcardDeckRequest(
            file_ids=[1],
            number_of_cards=1,
            difficulty_level=QuizDifficulty.EASY,
        )
        assert deck_min.number_of_cards == 1

        deck_max = CreateFlashcardDeckRequest(
            file_ids=[1],
            number_of_cards=30,
            difficulty_level=QuizDifficulty.HARD,
        )
        assert deck_max.number_of_cards == 30


class TestChatRequestSchema:
    """SCHEMA-UNIT-008: ConversationalChatRequest validation."""

    def test_rejects_missing_query(self):
        """SCHEMA-UNIT-008a: ConversationalChatRequest rejects missing query."""
        with pytest.raises(ValidationError):
            ConversationalChatRequest(
                session_id=uuid.uuid4(),
                file_ids=[1],
            )

    def test_rejects_missing_session_id(self):
        """SCHEMA-UNIT-008b: ConversationalChatRequest rejects missing session_id."""
        with pytest.raises(ValidationError):
            ConversationalChatRequest(
                query="What is photosynthesis?",
                file_ids=[1],
            )

    def test_rejects_invalid_uuid_session_id(self):
        """SCHEMA-UNIT-008c: ConversationalChatRequest rejects invalid UUID."""
        with pytest.raises(ValidationError):
            ConversationalChatRequest(
                query="What is photosynthesis?",
                session_id="not-a-uuid",
                file_ids=[1],
            )

    def test_accepts_valid_chat_request(self):
        """Supplementary: ConversationalChatRequest accepts valid data."""
        req = ConversationalChatRequest(
            query="What is photosynthesis?",
            session_id=uuid.uuid4(),
            file_ids=[1, 2, 3],
        )
        assert req.query == "What is photosynthesis?"
        assert len(req.file_ids) == 3
