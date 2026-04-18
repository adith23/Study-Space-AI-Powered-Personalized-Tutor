import os
import shutil

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user_model import User
from app.models.video_model import GeneratedVideo, VideoStatus, VideoStyle
from app.schemas.video_schema import (
    VideoGenerateRequest,
    VideoGenerateResponse,
    VideoListItem,
    VideoStatusResponse,
)
from app.services.content_generation_context_service import get_valid_selected_files
from app.tasks.video_tasks import generate_video_task

router = APIRouter()


# ── POST /generate — Start video generation ──────────────────────────────────


@router.post("/generate", response_model=VideoGenerateResponse)
async def create_video(
    request: VideoGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Validate sources, create a video record, and dispatch the Celery task."""

    # Validate that all selected files exist and are processed
    get_valid_selected_files(
        db=db, current_user=current_user, file_ids=request.file_ids
    )

    # Map style string to enum
    try:
        style = VideoStyle(request.style)
    except ValueError:
        style = VideoStyle.EXPLAINER

    # Create the video record
    video = GeneratedVideo(
        user_id=current_user.id,
        status=VideoStatus.PENDING.value,
        progress_pct=0,
        style=style.value,
        source_file_ids=request.file_ids,
        focus_prompt=request.focus_prompt,
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    # Dispatch the background task
    generate_video_task.delay(video.id)

    return VideoGenerateResponse(id=video.id, status=video.status)


# ── GET / — List user's videos ───────────────────────────────────────────────


@router.get("", response_model=list[VideoListItem])
async def list_videos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all generated videos for the current user, newest first."""
    videos = (
        db.query(GeneratedVideo)
        .filter(GeneratedVideo.user_id == current_user.id)
        .order_by(GeneratedVideo.created_at.desc())
        .all()
    )
    return [
        VideoListItem(
            id=v.id,
            title=v.title,
            status=v.status,
            duration_seconds=v.duration_seconds,
            style=v.style,
            created_at=v.created_at.isoformat() if v.created_at else None,
        )
        for v in videos
    ]


# ── GET /{id} — Get video status / metadata ──────────────────────────────────


@router.get("/{video_id}", response_model=VideoStatusResponse)
async def get_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the current status and metadata of a generated video."""
    video = (
        db.query(GeneratedVideo)
        .filter(
            GeneratedVideo.id == video_id,
            GeneratedVideo.user_id == current_user.id,
        )
        .first()
    )
    if not video:
        raise HTTPException(status_code=404, detail="Video not found.")

    video_url = f"/api/v1/videos/{video.id}/stream" if video.video_path else None
    thumbnail_url = (
        f"/api/v1/videos/{video.id}/thumbnail" if video.thumbnail_path else None
    )

    return VideoStatusResponse(
        id=video.id,
        status=video.status,
        progress_pct=video.progress_pct,
        title=video.title,
        duration_seconds=video.duration_seconds,
        video_url=video_url,
        thumbnail_url=thumbnail_url,
        created_at=video.created_at.isoformat() if video.created_at else None,
        error_message=video.error_message,
        style=video.style,
    )


# ── GET /{id}/stream — Stream the video file ─────────────────────────────────


@router.get("/{video_id}/stream")
async def stream_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stream the generated video file."""
    video = (
        db.query(GeneratedVideo)
        .filter(
            GeneratedVideo.id == video_id,
            GeneratedVideo.user_id == current_user.id,
        )
        .first()
    )
    if not video or not video.video_path:
        raise HTTPException(status_code=404, detail="Video not found or not ready.")

    if not os.path.isfile(video.video_path):
        raise HTTPException(status_code=404, detail="Video file missing from storage.")

    return FileResponse(
        video.video_path,
        media_type="video/mp4",
        filename=f"{video.title or 'video'}.mp4",
    )


# ── GET /{id}/thumbnail — Serve the thumbnail image ─────────────────────────


@router.get("/{video_id}/thumbnail")
async def get_thumbnail(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Serve the video thumbnail image."""
    video = (
        db.query(GeneratedVideo)
        .filter(
            GeneratedVideo.id == video_id,
            GeneratedVideo.user_id == current_user.id,
        )
        .first()
    )
    if not video or not video.thumbnail_path:
        raise HTTPException(status_code=404, detail="Thumbnail not found.")

    if not os.path.isfile(video.thumbnail_path):
        raise HTTPException(
            status_code=404, detail="Thumbnail file missing from storage."
        )

    return FileResponse(video.thumbnail_path, media_type="image/jpeg")


# ── DELETE /{id} — Delete video and cleanup files ────────────────────────────


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a generated video and remove all associated files."""
    video = (
        db.query(GeneratedVideo)
        .filter(
            GeneratedVideo.id == video_id,
            GeneratedVideo.user_id == current_user.id,
        )
        .first()
    )
    if not video:
        raise HTTPException(status_code=404, detail="Video not found.")

    # Remove files from disk
    from app.core.config import settings

    video_dir = os.path.join(settings.VIDEO_STORAGE_PATH, str(video_id))
    if os.path.isdir(video_dir):
        shutil.rmtree(video_dir, ignore_errors=True)

    # Remove DB record
    db.delete(video)
    db.commit()
