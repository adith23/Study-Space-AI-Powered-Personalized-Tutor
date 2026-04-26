"""
Renderer-aware video generation orchestration.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.video_model import GeneratedVideo, VideoRenderer, VideoStatus
from app.schemas.video_schema import RenderedVisualResult
from app.services.content_generation_context_service import (
    build_content_generation_context,
    get_valid_selected_files,
)
from app.services.video.artifacts import VideoArtifactRegistry, build_artifacts_snapshot
from app.services.video.renderers.image_renderer import ImageRenderer
from app.services.video.renderers.manim_renderer import ManimRenderer
from app.services.video.script_generator import generate_video_script
from app.services.video.tts_generator import generate_all_scene_audio
from app.services.video.video_assembler import (
    VisualAssemblyService,
    create_scene_clips_from_images,
)
from app.services.video.workspace import build_video_workspace, write_json_artifact

logger = logging.getLogger(__name__)


def _update_status(
    db: Session,
    video: GeneratedVideo,
    status: VideoStatus,
    progress: int,
    **kwargs,
) -> None:
    video.status = status.value
    video.progress_pct = progress
    for key, value in kwargs.items():
        setattr(video, key, value)
    db.commit()


class VideoPipelineOrchestrator:
    def __init__(self, db: Session) -> None:
        self.db = db
        self._registry = {
            VideoRenderer.IMAGE: ImageRenderer(),
            VideoRenderer.MANIM: ManimRenderer(),
        }
        self._assembler = VisualAssemblyService()

    def run(self, video_id: int) -> None:
        video = self._load_video(video_id)
        if not video:
            logger.error("Video record %d not found.", video_id)
            return
        if video.status == VideoStatus.COMPLETED.value:
            logger.warning("Video %d already completed. Skipping.", video_id)
            return

        workspace = build_video_workspace(video_id)
        artifacts = VideoArtifactRegistry()
        stage_timings: dict[str, float] = {}

        try:
            user = video.user
            files = get_valid_selected_files(
                db=self.db,
                current_user=user,
                file_ids=video.source_file_ids or [],
            )

            script_start = time.perf_counter()
            _update_status(self.db, video, VideoStatus.SCRIPTING, 5)
            context = build_content_generation_context(
                db=self.db,
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
            stage_timings["scripting_seconds"] = time.perf_counter() - script_start
            video.title = script.title
            video.script_json = script.model_dump(mode="json")
            write_json_artifact(workspace.script_path(), video.script_json)
            artifacts.record(
                "script_json",
                str(workspace.script_path()),
                "json",
                {"scene_count": len(script.scenes)},
            )
            self._persist_artifacts(video, artifacts, stage_timings, workspace)
            self.db.commit()

            renderer = self._resolve_renderer(video)
            visual_start = time.perf_counter()
            visual_result = self._generate_visuals(
                renderer=renderer,
                video=video,
                context=context,
                script=script,
                workspace=workspace,
            )
            stage_timings["visuals_seconds"] = time.perf_counter() - visual_start
            renderer_value = self._renderer_value(video)
            if renderer_value == VideoRenderer.MANIM.value:
                video.render_spec_json = self._read_json_file_if_exists(str(workspace.spec_path()))
            for name, meta in visual_result.artifacts.items():
                artifacts.record(name, meta.path, meta.kind, meta.metadata)
            self._persist_artifacts(video, artifacts, stage_timings, workspace)
            self.db.commit()

            audio_start = time.perf_counter()
            _update_status(self.db, video, VideoStatus.GENERATING_AUDIO, 75)
            audio_results = generate_all_scene_audio(
                scenes=script.scenes,
                workspace=workspace,
            )
            stage_timings["audio_seconds"] = time.perf_counter() - audio_start
            for item in audio_results:
                artifacts.record(
                    f"audio_{item.scene_number:03d}",
                    item.audio_path,
                    "audio",
                    {"duration_seconds": item.duration_seconds},
                )

            if not visual_result.scene_clips:
                visual_result.scene_clips = create_scene_clips_from_images(
                    image_paths=visual_result.image_paths,
                    audio_results=audio_results,
                    workspace=workspace,
                )

            assembly_start = time.perf_counter()
            _update_status(self.db, video, VideoStatus.ASSEMBLING, 90)
            assembly = self._assembler.assemble_scene_clips(
                scene_clips=visual_result.scene_clips,
                audio_results=audio_results,
                workspace=workspace,
            )
            stage_timings["assembly_seconds"] = time.perf_counter() - assembly_start
            artifacts.record("output_video", assembly.video_path, "video", {})
            artifacts.record("thumbnail", assembly.thumbnail_path, "image", {})

            _update_status(
                self.db,
                video,
                VideoStatus.COMPLETED,
                100,
                video_path=assembly.video_path,
                thumbnail_path=assembly.thumbnail_path,
                duration_seconds=assembly.duration_seconds,
                completed_at=datetime.now(timezone.utc),
                artifacts_json=build_artifacts_snapshot(artifacts),
            )
            self._persist_artifacts(video, artifacts, stage_timings, workspace)
            self.db.commit()
        except Exception as exc:
            logger.error("Video pipeline failed for %d: %s", video_id, exc, exc_info=True)
            self._fail(video, str(exc), artifacts, stage_timings, workspace)

    def _load_video(self, video_id: int) -> GeneratedVideo | None:
        return self.db.query(GeneratedVideo).filter(GeneratedVideo.id == video_id).first()

    def _resolve_renderer(self, video: GeneratedVideo):
        renderer_value = self._renderer_value(video)
        renderer_enum = VideoRenderer(renderer_value)
        return self._registry[renderer_enum]

    def _generate_visuals(
        self,
        *,
        renderer,
        video: GeneratedVideo,
        context,
        script,
        workspace,
    ) -> RenderedVisualResult:
        if self._renderer_value(video) == VideoRenderer.MANIM.value:
            _update_status(self.db, video, VideoStatus.PLANNING_VISUALS, 30)
            _update_status(self.db, video, VideoStatus.COMPILING_MANIM, 45)
            _update_status(self.db, video, VideoStatus.RENDERING_MANIM, 60)
            return renderer.render(
                script=script,
                context=context,
                workspace=workspace,
                style=video.style or "explainer",
                focus_prompt=video.focus_prompt,
            )

        _update_status(self.db, video, VideoStatus.GENERATING_IMAGES, 25)
        result = renderer.render(script=script, workspace=workspace)
        _update_status(self.db, video, VideoStatus.GENERATING_IMAGES, 60)
        return result

    def _renderer_value(self, video: GeneratedVideo) -> str:
        renderer = getattr(video, "renderer", VideoRenderer.IMAGE)
        if isinstance(renderer, VideoRenderer):
            return renderer.value
        return str(renderer)

    def _persist_artifacts(
        self,
        video: GeneratedVideo,
        artifacts: VideoArtifactRegistry,
        stage_timings: dict[str, float],
        workspace,
    ) -> None:
        snapshot = build_artifacts_snapshot(artifacts)
        snapshot["stage_timings"] = {
            "path": "",
            "kind": "metadata",
            "metadata": stage_timings,
        }
        video.artifacts_json = snapshot
        write_json_artifact(workspace.artifacts_manifest_path(), snapshot)

    def _read_json_file_if_exists(self, path: str):
        try:
            import json

            with open(path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except OSError:
            return None

    def _fail(
        self,
        video: GeneratedVideo,
        message: str,
        artifacts: VideoArtifactRegistry,
        stage_timings: dict[str, float],
        workspace,
    ) -> None:
        self._persist_artifacts(video, artifacts, stage_timings, workspace)
        _update_status(
            self.db,
            video,
            VideoStatus.FAILED,
            video.progress_pct or 0,
            error_message=message[:500],
            artifacts_json=video.artifacts_json,
        )


def run_video_pipeline(db: Session, video_id: int) -> None:
    VideoPipelineOrchestrator(db).run(video_id)
