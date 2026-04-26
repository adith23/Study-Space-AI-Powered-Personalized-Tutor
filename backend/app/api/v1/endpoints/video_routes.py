import os
import shutil

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user_model import User
from app.models.video_model import GeneratedVideo, VideoRenderer, VideoStatus, VideoStyle
from app.schemas.video_schema import (
    VideoGenerateRequest,
    VideoGenerateResponse,
    VideoListItem,
    VideoStatusResponse,
)
from app.services.content_generation_context_service import get_valid_selected_files
from app.tasks.video_tasks import generate_video_task

router = APIRouter()


def _enum_value(value):
    return value.value if hasattr(value, "value") else value


@router.post("/generate", response_model=VideoGenerateResponse)
async def create_video(
    request: VideoGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_valid_selected_files(db=db, current_user=current_user, file_ids=request.file_ids)

    try:
        style = VideoStyle(request.style)
    except ValueError:
        style = VideoStyle.EXPLAINER

    try:
        renderer = VideoRenderer(request.renderer)
    except ValueError:
        renderer = VideoRenderer.IMAGE

    video = GeneratedVideo(
        user_id=current_user.id,
        status=VideoStatus.PENDING.value,
        progress_pct=0,
        style=style.value,
        renderer=renderer.value,
        source_file_ids=request.file_ids,
        focus_prompt=request.focus_prompt,
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    generate_video_task.delay(video.id)

    return VideoGenerateResponse(
        id=video.id,
        status=_enum_value(video.status),
        renderer=_enum_value(video.renderer),
    )


@router.get("", response_model=list[VideoListItem])
async def list_videos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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
            status=_enum_value(v.status),
            duration_seconds=v.duration_seconds,
            style=_enum_value(v.style),
            created_at=v.created_at.isoformat() if v.created_at else None,
            renderer=_enum_value(v.renderer),
        )
        for v in videos
    ]


@router.get("/{video_id}", response_model=VideoStatusResponse)
async def get_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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
    thumbnail_url = f"/api/v1/videos/{video.id}/thumbnail" if video.thumbnail_path else None

    return VideoStatusResponse(
        id=video.id,
        status=_enum_value(video.status),
        progress_pct=video.progress_pct,
        title=video.title,
        duration_seconds=video.duration_seconds,
        video_url=video_url,
        thumbnail_url=thumbnail_url,
        created_at=video.created_at.isoformat() if video.created_at else None,
        error_message=video.error_message,
        style=_enum_value(video.style),
        renderer=_enum_value(video.renderer),
    )


@router.get("/{video_id}/stream")
async def stream_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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


@router.get("/{video_id}/thumbnail")
async def get_thumbnail(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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
        raise HTTPException(status_code=404, detail="Thumbnail file missing from storage.")

    return FileResponse(video.thumbnail_path, media_type="image/jpeg")


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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

    from app.core.config import settings

    video_dir = os.path.join(settings.VIDEO_STORAGE_PATH, str(video_id))
    if os.path.isdir(video_dir):
        shutil.rmtree(video_dir, ignore_errors=True)

    db.delete(video)
    db.commit()
