from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user_model import User
from app.schemas.quiz_schema import (
    CreateQuizRequest,
    QuizAttemptResultResponse,
    QuizDetailResponse,
    QuizResponse,
    SubmitQuizAttemptRequest,
)
from app.services.quiz_attempt_service import (
    get_quiz_attempt_result,
    submit_quiz_attempt,
)
from app.services.quiz_service import (
    create_quiz,
    get_quiz_detail,
    get_quiz_or_404,
    list_quizzes,
)
from app.tasks.quiz_tasks import generate_quiz_task

router = APIRouter()


@router.post("/quizzes", response_model=QuizResponse)
def create_quiz_route(
    request: CreateQuizRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    quiz = create_quiz(db=db, current_user=current_user, request=request)
    generate_quiz_task.delay(quiz.id)
    return quiz


@router.get("/quizzes", response_model=list[QuizResponse])
def list_quizzes_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return list_quizzes(db=db, current_user=current_user)


@router.get("/quizzes/{quiz_id}", response_model=QuizDetailResponse)
def get_quiz_route(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return get_quiz_detail(db=db, current_user=current_user, quiz_id=quiz_id)


@router.post(
    "/quizzes/{quiz_id}/attempts",
    response_model=QuizAttemptResultResponse,
)
def submit_quiz_attempt_route(
    quiz_id: int,
    request: SubmitQuizAttemptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    quiz = get_quiz_or_404(db=db, current_user=current_user, quiz_id=quiz_id)
    return submit_quiz_attempt(
        db=db,
        current_user=current_user,
        quiz=quiz,
        request=request,
    )


@router.get(
    "/quizzes/{quiz_id}/attempts/{attempt_id}",
    response_model=QuizAttemptResultResponse,
)
def get_quiz_attempt_route(
    quiz_id: int,
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    quiz = get_quiz_or_404(db=db, current_user=current_user, quiz_id=quiz_id)
    return get_quiz_attempt_result(
        db=db,
        current_user=current_user,
        quiz=quiz,
        attempt_id=attempt_id,
    )
