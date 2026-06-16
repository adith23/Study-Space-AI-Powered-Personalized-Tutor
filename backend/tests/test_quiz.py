"""
Quiz service unit tests and Quiz API integration tests.

Covers: QUIZ-UNIT-001 through QUIZ-UNIT-007
        QUIZ-INT-001 through QUIZ-INT-005

See qa_testing_plan.md Sections 6.4 and 7.5.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from app.models.material_model import UploadedFile, FileType, ProcessingStatus
from app.models.quiz_model import (
    Quiz,
    QuizQuestion,
    QuizSource,
    QuizStatus,
    QuizDifficulty,
    QuizGenerationMode,
)
from app.models.user_model import User
from app.schemas.quiz_schema import (
    CreateQuizRequest,
    SubmitQuizAttemptRequest,
    SubmitQuizAnswerRequest,
)
from app.services.quiz_service import create_quiz, list_quizzes, get_quiz_or_404
from app.services.quiz_attempt_service import submit_quiz_attempt

# ==========================================================================
# Helper to create test materials (shared across quiz/flashcard tests)
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


def _create_quiz_with_questions(db_session, user, file_record, num_questions=3):
    """Helper: create a READY quiz with questions for a user."""
    quiz = Quiz(
        user_id=user.id,
        title="Test Quiz",
        difficulty_level=QuizDifficulty.MEDIUM,
        number_of_questions=num_questions,
        generation_mode=QuizGenerationMode.BROAD_FULL_SOURCE,
        status=QuizStatus.READY,
    )
    db_session.add(quiz)
    db_session.flush()

    db_session.add(QuizSource(quiz_id=quiz.id, uploaded_file_id=file_record.id))

    for i in range(1, num_questions + 1):
        db_session.add(
            QuizQuestion(
                quiz_id=quiz.id,
                question_text=f"Question {i}?",
                option_a=f"Option A{i}",
                option_b=f"Option B{i}",
                option_c=f"Option C{i}",
                option_d=f"Option D{i}",
                correct_option="A",
                question_order=i,
            )
        )

    db_session.commit()
    db_session.refresh(quiz)
    return quiz


# ==========================================================================
# QUIZ-UNIT-001 through 007: Quiz service unit tests
# ==========================================================================


class TestCreateQuiz:
    """QUIZ-UNIT-001: create_quiz creates a quiz with PENDING status."""

    @patch("app.services.quiz_service.get_valid_selected_files")
    def test_creates_quiz_with_pending_status(
        self, mock_validate, db_session, test_user
    ):
        """QUIZ-UNIT-001: create_quiz creates a quiz record with PENDING status."""
        file_record = _create_processed_file(db_session, test_user)
        mock_validate.return_value = [file_record]

        request = CreateQuizRequest(
            file_ids=[file_record.id],
            number_of_questions=5,
            difficulty_level=QuizDifficulty.EASY,
        )
        result = create_quiz(db=db_session, current_user=test_user, request=request)
        assert result.status == QuizStatus.PENDING
        assert result.number_of_questions == 5


class TestListQuizzes:
    """QUIZ-UNIT-002: list_quizzes returns only current user's quizzes."""

    def test_returns_only_current_user_quizzes(
        self, db_session, test_user, second_user
    ):
        """QUIZ-UNIT-002: Only current user's quizzes are returned."""
        file_a = _create_processed_file(db_session, test_user, "a.pdf")
        file_b = _create_processed_file(db_session, second_user, "b.pdf")

        _create_quiz_with_questions(db_session, test_user, file_a)
        _create_quiz_with_questions(db_session, second_user, file_b)

        results = list_quizzes(db=db_session, current_user=test_user)
        assert len(results) == 1
        assert all(r.id for r in results)


class TestGetQuizOr404:
    """QUIZ-UNIT-003, 004: get_quiz_or_404 error handling."""

    def test_raises_404_for_nonexistent_quiz(self, db_session, test_user):
        """QUIZ-UNIT-003: Raises 404 for a quiz that doesn't exist."""
        with pytest.raises(HTTPException) as exc_info:
            get_quiz_or_404(db=db_session, current_user=test_user, quiz_id=99999)
        assert exc_info.value.status_code == 404

    def test_raises_404_for_other_users_quiz(self, db_session, test_user, second_user):
        """QUIZ-UNIT-004: Raises 404 for another user's quiz."""
        file_record = _create_processed_file(db_session, second_user)
        quiz = _create_quiz_with_questions(db_session, second_user, file_record)

        with pytest.raises(HTTPException) as exc_info:
            get_quiz_or_404(db=db_session, current_user=test_user, quiz_id=quiz.id)
        assert exc_info.value.status_code == 404


class TestSubmitQuizAttempt:
    """QUIZ-UNIT-005, 006: Quiz attempt scoring."""

    def test_calculates_score_correctly(self, db_session, test_user):
        """QUIZ-UNIT-005: Score is calculated correctly for known answers."""
        file_record = _create_processed_file(db_session, test_user)
        quiz = _create_quiz_with_questions(
            db_session, test_user, file_record, num_questions=3
        )

        questions = sorted(quiz.questions, key=lambda q: q.question_order)

        # Answer: 2 correct (A), 1 wrong (B)
        request = SubmitQuizAttemptRequest(
            answers=[
                SubmitQuizAnswerRequest(
                    question_id=questions[0].id, selected_option="A"
                ),
                SubmitQuizAnswerRequest(
                    question_id=questions[1].id, selected_option="A"
                ),
                SubmitQuizAnswerRequest(
                    question_id=questions[2].id, selected_option="B"
                ),
            ]
        )

        result = submit_quiz_attempt(
            db=db_session, current_user=test_user, quiz=quiz, request=request
        )
        assert result.score == 2
        assert result.total_questions == 3
        assert result.percentage == pytest.approx(66.67, abs=0.1)

    def test_rejects_incomplete_answers(self, db_session, test_user):
        """QUIZ-UNIT-006: submit_quiz_attempt rejects partial answers."""
        file_record = _create_processed_file(db_session, test_user)
        quiz = _create_quiz_with_questions(
            db_session, test_user, file_record, num_questions=3
        )

        questions = sorted(quiz.questions, key=lambda q: q.question_order)

        # Only answer 2 of 3 questions
        request = SubmitQuizAttemptRequest(
            answers=[
                SubmitQuizAnswerRequest(
                    question_id=questions[0].id, selected_option="A"
                ),
                SubmitQuizAnswerRequest(
                    question_id=questions[1].id, selected_option="A"
                ),
            ]
        )

        with pytest.raises(HTTPException) as exc_info:
            submit_quiz_attempt(
                db=db_session, current_user=test_user, quiz=quiz, request=request
            )
        assert exc_info.value.status_code == 422


# ==========================================================================
# QUIZ-INT-001 through 005: Quiz API integration tests
# ==========================================================================


class TestQuizAPICreate:
    """QUIZ-INT-001: POST /api/v1/materials/quizzes."""

    @patch("app.tasks.quiz_tasks.generate_quiz_task")
    @patch("app.services.quiz_service.get_valid_selected_files")
    def test_create_quiz_dispatches_celery(
        self, mock_validate, mock_task, client, db_session, test_user, auth_headers
    ):
        """QUIZ-INT-001: POST /quizzes creates quiz and dispatches Celery task."""
        file_record = _create_processed_file(db_session, test_user)
        mock_validate.return_value = [file_record]

        response = client.post(
            "/api/v1/materials/quizzes",
            headers=auth_headers,
            json={
                "file_ids": [file_record.id],
                "number_of_questions": 5,
                "difficulty_level": "easy",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        mock_task.delay.assert_called_once_with(data["id"])


class TestQuizAPIList:
    """QUIZ-INT-002, 003: GET /api/v1/materials/quizzes."""

    def test_list_quizzes_returns_only_current_user(
        self,
        client,
        db_session,
        test_user,
        second_user,
        auth_headers,
        second_user_headers,
    ):
        """QUIZ-INT-002: GET /quizzes returns only current user's quizzes."""
        file_a = _create_processed_file(db_session, test_user, "a.pdf")
        file_b = _create_processed_file(db_session, second_user, "b.pdf")
        _create_quiz_with_questions(db_session, test_user, file_a)
        _create_quiz_with_questions(db_session, second_user, file_b)

        response = client.get("/api/v1/materials/quizzes", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_get_quiz_returns_404_for_other_user(
        self, client, db_session, test_user, second_user, second_user_headers
    ):
        """QUIZ-INT-003: GET /quizzes/{id} returns 404 for other user's quiz."""
        file_record = _create_processed_file(db_session, test_user)
        quiz = _create_quiz_with_questions(db_session, test_user, file_record)

        response = client.get(
            f"/api/v1/materials/quizzes/{quiz.id}",
            headers=second_user_headers,
        )
        assert response.status_code == 404


class TestQuizAPIAttempts:
    """QUIZ-INT-004, 005: Quiz attempt submission and retrieval."""

    def test_submit_attempt_persists_score(
        self, client, db_session, test_user, auth_headers
    ):
        """QUIZ-INT-004: POST /quizzes/{id}/attempts calculates and persists score."""
        file_record = _create_processed_file(db_session, test_user)
        quiz = _create_quiz_with_questions(
            db_session, test_user, file_record, num_questions=2
        )
        questions = sorted(quiz.questions, key=lambda q: q.question_order)

        response = client.post(
            f"/api/v1/materials/quizzes/{quiz.id}/attempts",
            headers=auth_headers,
            json={
                "answers": [
                    {"question_id": questions[0].id, "selected_option": "A"},
                    {"question_id": questions[1].id, "selected_option": "B"},
                ]
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 1  # First correct (A), second wrong (B)
        assert data["total_questions"] == 2
        assert "attempt_id" in data

    def test_get_attempt_result(self, client, db_session, test_user, auth_headers):
        """QUIZ-INT-005: GET /quizzes/{id}/attempts/{aid} returns correct result."""
        file_record = _create_processed_file(db_session, test_user)
        quiz = _create_quiz_with_questions(
            db_session, test_user, file_record, num_questions=2
        )
        questions = sorted(quiz.questions, key=lambda q: q.question_order)

        # First submit
        submit_resp = client.post(
            f"/api/v1/materials/quizzes/{quiz.id}/attempts",
            headers=auth_headers,
            json={
                "answers": [
                    {"question_id": questions[0].id, "selected_option": "A"},
                    {"question_id": questions[1].id, "selected_option": "A"},
                ]
            },
        )
        attempt_id = submit_resp.json()["attempt_id"]

        # Then retrieve
        response = client.get(
            f"/api/v1/materials/quizzes/{quiz.id}/attempts/{attempt_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 2
        assert data["attempt_id"] == attempt_id
