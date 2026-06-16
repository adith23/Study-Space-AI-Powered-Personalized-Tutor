"""
Space-scoped resource routes.

These routes nest all content-related endpoints under /spaces/{space_id}/...
so that files, chats, quizzes, flashcards, and videos are scoped to a specific space.

The original non-scoped routes remain functional for backward compatibility.
"""

from typing import List, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.task_dispatcher import dispatch_task
from app.models.user_model import User
from app.models.video_model import (
    GeneratedVideo,
    VideoRenderer,
    VideoStatus,
    VideoStyle,
)
from app.schemas.chat_schema import ChatSessionResponse
from app.schemas.flashcard_schema import (
    CreateFlashcardDeckRequest,
    FlashcardDeckResponse,
)
from app.schemas.material_schema import FileType as SchemaFileType
from app.schemas.material_schema import UploadedFileResponse
from app.schemas.quiz_schema import CreateQuizRequest, QuizResponse
from app.schemas.video_schema import (
    VideoGenerateRequest,
    VideoGenerateResponse,
    VideoListItem,
)
from app.services.chat_session_service import (
    create_chat_session,
    list_user_chat_sessions,
)
from app.services.content_generation_context_service import get_valid_selected_files
from app.services.flashcard_service import create_flashcard_deck, list_flashcard_decks
from app.services.material_service import create_uploaded_file, list_user_files
from app.services.quiz_service import create_quiz, list_quizzes
from app.services.space_service import get_space, touch_space_access

router = APIRouter()


def _enum_value(value):
    return value.value if hasattr(value, "value") else value


# ──────────────────────────────────────────
# Materials (Files) — scoped to a space
# ──────────────────────────────────────────


@router.post("/{space_id}/materials/file", response_model=UploadedFileResponse)
async def upload_file_to_space(
    space_id: int,
    background_tasks: BackgroundTasks,
    file_type: SchemaFileType = Form(...),
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Upload a file scoped to a specific space."""
    # Verify space ownership
    get_space(space_id=space_id, db=db, current_user=current_user)
    return await create_uploaded_file(
        file_type=file_type,
        file=file,
        url=url,
        db=db,
        current_user=current_user,
        space_id=space_id,
    )


@router.get("/{space_id}/materials/files", response_model=List[UploadedFileResponse])
def list_space_files(
    space_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all files in a specific space."""
    get_space(space_id=space_id, db=db, current_user=current_user)
    return list_user_files(db=db, current_user=current_user, space_id=space_id)


# ──────────────────────────────────────────
# Chat Sessions — scoped to a space
# ──────────────────────────────────────────


@router.post(
    "/{space_id}/materials/chat/sessions",
    response_model=ChatSessionResponse,
    status_code=201,
)
def create_space_chat_session(
    space_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new chat session scoped to a specific space."""
    get_space(space_id=space_id, db=db, current_user=current_user)
    return create_chat_session(db=db, current_user=current_user, space_id=space_id)


@router.get(
    "/{space_id}/materials/chat/sessions", response_model=List[ChatSessionResponse]
)
def list_space_chat_sessions(
    space_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all chat sessions in a specific space."""
    get_space(space_id=space_id, db=db, current_user=current_user)
    return list_user_chat_sessions(db=db, current_user=current_user, space_id=space_id)


# ──────────────────────────────────────────
# Quizzes — scoped to a space
# ──────────────────────────────────────────


@router.post("/{space_id}/materials/quizzes", response_model=QuizResponse)
def create_space_quiz(
    space_id: int,
    request: CreateQuizRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a quiz scoped to a specific space."""
    get_space(space_id=space_id, db=db, current_user=current_user)
    quiz = create_quiz(
        db=db, current_user=current_user, request=request, space_id=space_id
    )
    dispatch_task("generate_quiz", {"quiz_id": quiz.id})
    return quiz


@router.get("/{space_id}/materials/quizzes", response_model=list[QuizResponse])
def list_space_quizzes(
    space_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all quizzes in a specific space."""
    get_space(space_id=space_id, db=db, current_user=current_user)
    return list_quizzes(db=db, current_user=current_user, space_id=space_id)


# ──────────────────────────────────────────
# Flashcards — scoped to a space
# ──────────────────────────────────────────


@router.post("/{space_id}/materials/flashcards", response_model=FlashcardDeckResponse)
def create_space_flashcard_deck(
    space_id: int,
    request: CreateFlashcardDeckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a flashcard deck scoped to a specific space."""
    get_space(space_id=space_id, db=db, current_user=current_user)
    deck = create_flashcard_deck(
        db=db, current_user=current_user, request=request, space_id=space_id
    )
    dispatch_task("generate_flashcard", {"deck_id": deck.id})
    return deck


@router.get(
    "/{space_id}/materials/flashcards", response_model=list[FlashcardDeckResponse]
)
def list_space_flashcard_decks(
    space_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all flashcard decks in a specific space."""
    get_space(space_id=space_id, db=db, current_user=current_user)
    return list_flashcard_decks(db=db, current_user=current_user, space_id=space_id)


# ──────────────────────────────────────────
# Videos — scoped to a space
# ──────────────────────────────────────────


@router.post("/{space_id}/videos/generate", response_model=VideoGenerateResponse)
async def create_space_video(
    space_id: int,
    request: VideoGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Generate a video scoped to a specific space."""
    get_space(space_id=space_id, db=db, current_user=current_user)
    get_valid_selected_files(
        db=db, current_user=current_user, file_ids=request.file_ids
    )

    try:
        style = VideoStyle(request.style)
    except ValueError:
        style = VideoStyle.EXPLAINER

    try:
        renderer_val = VideoRenderer(request.renderer)
    except ValueError:
        renderer_val = VideoRenderer.IMAGE

    video = GeneratedVideo(
        user_id=current_user.id,
        space_id=space_id,
        status=VideoStatus.PENDING.value,
        progress_pct=0,
        style=style.value,
        renderer=renderer_val.value,
        source_file_ids=request.file_ids,
        focus_prompt=request.focus_prompt,
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    dispatch_task("generate_video", {"video_id": video.id})

    return VideoGenerateResponse(
        id=video.id,
        status=_enum_value(video.status),
        renderer=_enum_value(video.renderer),
    )


@router.get("/{space_id}/videos", response_model=list[VideoListItem])
async def list_space_videos(
    space_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all videos in a specific space."""
    get_space(space_id=space_id, db=db, current_user=current_user)
    videos = (
        db.query(GeneratedVideo)
        .filter(
            GeneratedVideo.user_id == current_user.id,
            GeneratedVideo.space_id == space_id,
        )
        .order_by(GeneratedVideo.created_at.desc())
        .all()
    )
    return [
        VideoListItem(
            id=v.id,
            title=v.title,
            status=_enum_value(v.status),
            duration_seconds=v.duration_seconds,
            style=_enum_value(v.style),
            created_at=v.created_at.isoformat() if v.created_at else None,
            renderer=_enum_value(v.renderer),
        )
        for v in videos
    ]
