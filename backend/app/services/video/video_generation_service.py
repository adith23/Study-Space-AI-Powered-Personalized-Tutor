"""
Video Generation Orchestrator

Coordinates the full 4-stage pipeline:
  1. Script generation (Gemini LLM)
  2. Image generation (Gemini 2.5 Flash Image)
  3. Audio narration (Gemini TTS)
  4. Video assembly (FFmpeg)

Updates the GeneratedVideo database record at each stage so the
frontend can poll progress.
"""

import logging
import os
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.material_model import UploadedFile
from app.models.video_model import GeneratedVideo, VideoStatus
from app.services.content_generation_context_service import (
    build_content_generation_context,
    get_valid_selected_files,
)
from app.services.video.image_generator import generate_all_scene_images
from app.services.video.script_generator import generate_video_script
from app.services.video.tts_generator import generate_all_scene_audio
from app.services.video.video_assembler import assemble_video

logger = logging.getLogger(__name__)


def _update_status(
    db: Session,
    video: GeneratedVideo,
    status: VideoStatus,
    progress: int,
    **kwargs,
) -> None:
    """Update video record status and commit."""
    video.status = status.value
    video.progress_pct = progress
    for key, value in kwargs.items():
        setattr(video, key, value)
    db.commit()


def run_video_pipeline(db: Session, video_id: int) -> None:
    """
    Execute the full video generation pipeline for a given video record.

    This function is designed to be called from a Celery background task.
    It manages its own error handling and status updates.
    """
    video = db.query(GeneratedVideo).filter(GeneratedVideo.id == video_id).first()
    if not video:
        logger.error("Video record %d not found.", video_id)
        return

    # Prevent re-processing completed videos
    if video.status == VideoStatus.COMPLETED.value:
        logger.warning("Video %d already completed. Skipping.", video_id)
        return

    try:
        # ── Resolve source files ─────────────────────────────────────────
        user = video.user
        file_ids = video.source_file_ids or []
        files = get_valid_selected_files(
            db=db, current_user=user, file_ids=file_ids
        )

        # Create output directory for this video
        video_dir = os.path.join(settings.VIDEO_STORAGE_PATH, str(video_id))
        os.makedirs(video_dir, exist_ok=True)

        # ── Stage 1: Script Generation (0% → 20%) ───────────────────────
        _update_status(db, video, VideoStatus.SCRIPTING, 5)

        context = build_content_generation_context(
            db=db,
            current_user=user,
            files=files,
            focus_prompt=video.focus_prompt,
            item_count=10,
        )

        script = generate_video_script(
            context=context,
            style=video.style or "explainer",
            focus_prompt=video.focus_prompt,
        )

        _update_status(
            db,
            video,
            VideoStatus.SCRIPTING,
            20,
            title=script.title,
            script_json={
                "title": script.title,
                "scenes": [s.model_dump() for s in script.scenes],
                "total_duration_seconds": script.total_duration_seconds,
            },
        )
        logger.info(
            "Stage 1 complete: %d scenes, %.0fs",
            len(script.scenes),
            script.total_duration_seconds,
        )

        # ── Stage 2: Image Generation (20% → 60%) ───────────────────────
        _update_status(db, video, VideoStatus.GENERATING_IMAGES, 25)

        image_paths = generate_all_scene_images(
            scenes=script.scenes,
            video_dir=video_dir,
        )

        _update_status(db, video, VideoStatus.GENERATING_IMAGES, 60)
        logger.info("Stage 2 complete: %d images generated", len(image_paths))

        # ── Stage 3: Audio Generation (60% → 80%) ───────────────────────
        _update_status(db, video, VideoStatus.GENERATING_AUDIO, 65)

        audio_results = generate_all_scene_audio(
            scenes=script.scenes,
            video_dir=video_dir,
        )

        _update_status(db, video, VideoStatus.GENERATING_AUDIO, 80)
        logger.info("Stage 3 complete: %d audio clips generated", len(audio_results))

        # ── Stage 4: Video Assembly (80% → 100%) ────────────────────────
        _update_status(db, video, VideoStatus.ASSEMBLING, 85)

        video_path, thumbnail_path, total_duration = assemble_video(
            image_paths=image_paths,
            audio_results=audio_results,
            video_dir=video_dir,
        )

        _update_status(
            db,
            video,
            VideoStatus.COMPLETED,
            100,
            video_path=video_path,
            thumbnail_path=thumbnail_path,
            duration_seconds=total_duration,
            completed_at=datetime.now(timezone.utc),
        )
        logger.info(
            "Video %d completed: %.0fs, %s",
            video_id,
            total_duration,
            video_path,
        )

    except Exception as exc:
        logger.error("Video pipeline failed for %d: %s", video_id, exc, exc_info=True)
        _update_status(
            db,
            video,
            VideoStatus.FAILED,
            video.progress_pct or 0,
            error_message=str(exc)[:500],
        )
