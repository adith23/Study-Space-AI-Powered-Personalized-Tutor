from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.quiz_model import (
    Quiz,
    QuizGenerationMode,
    QuizAttempt,
    QuizQuestion,
    QuizSource,
    QuizStatus,
)
from app.models.user_model import User
from app.schemas.quiz_schema import (
    CreateQuizRequest,
    GeneratedQuizPayload,
    QuizDetailResponse,
    QuizQuestionResponse,
    QuizResponse,
    QuizSourceResponse,
)
from app.services.quiz_context_service import (
    build_quiz_generation_context,
    get_valid_selected_files,
)
from app.services.quiz_generation_service import generate_quiz_payload


def create_quiz(
    *, db: Session, current_user: User, request: CreateQuizRequest
) -> QuizResponse:
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
    title = request.title or _default_quiz_title(files)
    quiz = Quiz(
        user_id=current_user.id,
        title=title,
        difficulty_level=request.difficulty_level,
        number_of_questions=request.number_of_questions,
        focus_prompt=request.focus_prompt,
        generation_mode=generation_mode,
        status=QuizStatus.PENDING,
    )
    db.add(quiz)
    db.flush()

    for file in files:
        db.add(QuizSource(quiz_id=quiz.id, uploaded_file_id=file.id))

    db.commit()
    db.refresh(quiz)
    return QuizResponse.model_validate(quiz)


def list_quizzes(*, db: Session, current_user: User) -> list[QuizResponse]:
    quizzes = (
        db.query(Quiz)
        .filter(Quiz.user_id == current_user.id)
        .order_by(Quiz.created_at.desc(), Quiz.id.desc())
        .all()
    )
    return [QuizResponse.model_validate(quiz) for quiz in quizzes]


def get_quiz_or_404(*, db: Session, current_user: User, quiz_id: int) -> Quiz:
    quiz = (
        db.query(Quiz)
        .options(
            joinedload(Quiz.sources).joinedload(QuizSource.uploaded_file),
            joinedload(Quiz.questions),
            joinedload(Quiz.attempts).joinedload(QuizAttempt.answers),
        )
        .filter(Quiz.id == quiz_id, Quiz.user_id == current_user.id)
        .first()
    )
    if quiz is None:
        raise HTTPException(status_code=404, detail="Quiz not found.")
    return quiz


def get_quiz_detail(
    *, db: Session, current_user: User, quiz_id: int
) -> QuizDetailResponse:
    quiz = get_quiz_or_404(db=db, current_user=current_user, quiz_id=quiz_id)
    return _serialize_quiz_detail(quiz)


def generate_quiz_for_id(*, db: Session, quiz_id: int) -> None:
    quiz = (
        db.query(Quiz)
        .options(joinedload(Quiz.sources).joinedload(QuizSource.uploaded_file))
        .filter(Quiz.id == quiz_id)
        .first()
    )
    if quiz is None:
        raise ValueError(f"Quiz {quiz_id} not found.")
    if quiz.status == QuizStatus.READY and quiz.questions:
        return

    quiz.status = QuizStatus.GENERATING
    quiz.error_message = None
    db.commit()
    db.refresh(quiz)

    files = [source.uploaded_file for source in quiz.sources]
    if not files:
        _mark_quiz_failed(db=db, quiz=quiz, error_message="Quiz has no selected sources.")
        return

    current_user = quiz.user
    try:
        context = build_quiz_generation_context(
            db=db,
            current_user=current_user,
            files=files,
            focus_prompt=quiz.focus_prompt,
            number_of_questions=quiz.number_of_questions,
        )
        payload = generate_quiz_payload(
            context=context,
            difficulty_level=quiz.difficulty_level,
            number_of_questions=quiz.number_of_questions,
            focus_prompt=quiz.focus_prompt,
        )
        _persist_generated_questions(db=db, quiz=quiz, payload=payload)
        quiz.status = QuizStatus.READY
        quiz.error_message = None
        db.commit()
    except Exception as exc:
        db.rollback()
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if quiz is not None:
            _mark_quiz_failed(db=db, quiz=quiz, error_message=str(exc))
        raise


def _persist_generated_questions(
    *, db: Session, quiz: Quiz, payload: GeneratedQuizPayload
) -> None:
    db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz.id).delete()
    for index, question in enumerate(payload.questions, start=1):
        db.add(
            QuizQuestion(
                quiz_id=quiz.id,
                question_text=question.question_text,
                option_a=question.options[0],
                option_b=question.options[1],
                option_c=question.options[2],
                option_d=question.options[3],
                correct_option=question.correct_option,
                question_order=index,
                source_snippet=question.source_snippet,
                source_metadata=question.source_metadata,
            )
        )


def _mark_quiz_failed(*, db: Session, quiz: Quiz, error_message: str) -> None:
    quiz.status = QuizStatus.FAILED
    quiz.error_message = error_message[:500]
    db.commit()


def _default_quiz_title(files: list) -> str:
    if len(files) == 1:
        return f"Quiz: {files[0].name or f'Source {files[0].id}'}"
    first_name = files[0].name or f"Source {files[0].id}"
    return f"Quiz: {first_name} + {len(files) - 1} more"


def _serialize_quiz_detail(quiz: Quiz) -> QuizDetailResponse:
    return QuizDetailResponse(
        id=quiz.id,
        title=quiz.title,
        difficulty_level=quiz.difficulty_level,
        number_of_questions=quiz.number_of_questions,
        focus_prompt=quiz.focus_prompt,
        generation_mode=quiz.generation_mode,
        status=quiz.status,
        error_message=quiz.error_message,
        sources=[
            QuizSourceResponse(
                uploaded_file_id=source.uploaded_file_id,
                name=source.uploaded_file.name if source.uploaded_file else None,
            )
            for source in quiz.sources
        ],
        questions=[
            QuizQuestionResponse(
                id=question.id,
                question_text=question.question_text,
                options=[
                    question.option_a,
                    question.option_b,
                    question.option_c,
                    question.option_d,
                ],
                question_order=question.question_order,
            )
            for question in sorted(quiz.questions, key=lambda item: item.question_order)
        ],
    )
