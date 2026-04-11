from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.quiz_model import Quiz, QuizAnswer, QuizAttempt, QuizQuestion, QuizStatus
from app.models.user_model import User
from app.schemas.quiz_schema import (
    QuizAttemptAnswerResultResponse,
    QuizAttemptResultResponse,
    SubmitQuizAttemptRequest,
)


def submit_quiz_attempt(
    *,
    db: Session,
    current_user: User,
    quiz: Quiz,
    request: SubmitQuizAttemptRequest,
) -> QuizAttemptResultResponse:
    if quiz.status != QuizStatus.READY:
        raise HTTPException(status_code=409, detail="Quiz is not ready for attempts.")

    questions = sorted(quiz.questions, key=lambda question: question.question_order)
    question_map = {question.id: question for question in questions}
    if not questions:
        raise HTTPException(status_code=409, detail="Quiz has no questions.")

    submitted_ids = [answer.question_id for answer in request.answers]
    expected_ids = [question.id for question in questions]
    if set(submitted_ids) != set(expected_ids) or len(submitted_ids) != len(expected_ids):
        raise HTTPException(
            status_code=422,
            detail="Answers must be provided for every quiz question exactly once.",
        )

    attempt = QuizAttempt(
        quiz_id=quiz.id,
        user_id=current_user.id,
        score=0,
        percentage=0.0,
    )
    db.add(attempt)
    db.flush()

    score = 0
    answer_results: list[QuizAttemptAnswerResultResponse] = []
    for submitted_answer in request.answers:
        question = question_map.get(submitted_answer.question_id)
        if question is None:
            raise HTTPException(status_code=422, detail="Answer contains an unknown question_id.")

        is_correct = submitted_answer.selected_option == question.correct_option
        if is_correct:
            score += 1

        db.add(
            QuizAnswer(
                attempt_id=attempt.id,
                question_id=question.id,
                selected_option=submitted_answer.selected_option,
                is_correct=is_correct,
            )
        )
        answer_results.append(_serialize_attempt_answer(question, submitted_answer.selected_option, is_correct))

    attempt.score = score
    attempt.percentage = round((score / len(questions)) * 100, 2)

    db.commit()
    db.refresh(attempt)

    ordered_results = sorted(
        answer_results,
        key=lambda answer: question_map[answer.question_id].question_order,
    )
    return QuizAttemptResultResponse(
        attempt_id=attempt.id,
        quiz_id=quiz.id,
        score=attempt.score,
        percentage=attempt.percentage,
        total_questions=len(questions),
        answers=ordered_results,
    )


def get_quiz_attempt_result(
    *, db: Session, current_user: User, quiz: Quiz, attempt_id: int
) -> QuizAttemptResultResponse:
    attempt = (
        db.query(QuizAttempt)
        .filter(
            QuizAttempt.id == attempt_id,
            QuizAttempt.quiz_id == quiz.id,
            QuizAttempt.user_id == current_user.id,
        )
        .first()
    )
    if attempt is None:
        raise HTTPException(status_code=404, detail="Quiz attempt not found.")

    questions = {question.id: question for question in quiz.questions}
    answers = sorted(
        attempt.answers,
        key=lambda answer: questions[answer.question_id].question_order,
    )
    return QuizAttemptResultResponse(
        attempt_id=attempt.id,
        quiz_id=quiz.id,
        score=attempt.score,
        percentage=attempt.percentage,
        total_questions=len(quiz.questions),
        answers=[
            _serialize_attempt_answer(
                questions[answer.question_id],
                answer.selected_option,
                answer.is_correct,
            )
            for answer in answers
        ],
    )


def _serialize_attempt_answer(
    question: QuizQuestion, selected_option: str, is_correct: bool
) -> QuizAttemptAnswerResultResponse:
    return QuizAttemptAnswerResultResponse(
        question_id=question.id,
        question_text=question.question_text,
        options=[
            question.option_a,
            question.option_b,
            question.option_c,
            question.option_d,
        ],
        selected_option=selected_option,
        correct_option=question.correct_option,
        is_correct=is_correct,
    )
