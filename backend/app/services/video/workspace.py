from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.config import settings


@dataclass(frozen=True)
class VideoWorkspace:
    video_id: int
    root: Path

    @classmethod
    def build(cls, video_id: int) -> "VideoWorkspace":
        return cls(video_id=video_id, root=Path(settings.VIDEO_STORAGE_PATH) / str(video_id))

    def ensure_dirs(self) -> None:
        for path in (
            self.root,
            self.logs_dir(),
            self.audio_dir(),
            self.scene_clip_dir(),
            self.aligned_clip_dir(),
            self.assembled_dir(),
            self.manim_media_dir(),
        ):
            path.mkdir(parents=True, exist_ok=True)

    def logs_dir(self) -> Path:
        return self.root / "logs"

    def audio_dir(self) -> Path:
        return self.root / "audio"

    def scene_clip_dir(self) -> Path:
        return self.root / "clips"

    def aligned_clip_dir(self) -> Path:
        return self.root / "aligned_clips"

    def assembled_dir(self) -> Path:
        return self.root / "assembled"

    def manim_media_dir(self) -> Path:
        return self.root / "manim_media"

    def script_path(self) -> Path:
        return self.root / "script.json"

    def spec_path(self) -> Path:
        return self.root / "render_spec.json"

    def manim_module_path(self) -> Path:
        return self.root / "manim_scene.py"

    def render_log_path(self) -> Path:
        return self.logs_dir() / "manim_render.log"

    def ffmpeg_log_path(self) -> Path:
        return self.logs_dir() / "ffmpeg.log"

    def artifacts_manifest_path(self) -> Path:
        return self.root / "artifacts.json"

    def output_video_path(self) -> Path:
        return self.root / "output.mp4"

    def thumbnail_path(self) -> Path:
        return self.root / "thumbnail.jpg"


def build_video_workspace(video_id: int) -> VideoWorkspace:
    workspace = VideoWorkspace.build(video_id)
    workspace.ensure_dirs()
    return workspace


def ensure_workspace_dirs(workspace: VideoWorkspace) -> None:
    workspace.ensure_dirs()


def write_json_artifact(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_text_artifact(path: str | Path, content: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
