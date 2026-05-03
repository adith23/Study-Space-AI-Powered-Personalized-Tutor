from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class VideoGenerateRequest(BaseModel):
    file_ids: list[int]
    focus_prompt: Optional[str] = None
    style: str = "explainer"
    renderer: Literal["image", "manim"] = "image"


class VideoScene(BaseModel):
    scene_number: int
    narration_text: str
    visual_description: str
    duration_seconds: float
    key_concept: str


class VideoScript(BaseModel):
    title: str
    scenes: list[VideoScene]
    total_duration_seconds: float


class ArtifactMeta(BaseModel):
    path: str
    kind: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RenderedSceneClip(BaseModel):
    scene_number: int
    scene_name: str
    clip_path: str
    duration_seconds: float | None = None


class AudioClipResult(BaseModel):
    scene_number: int
    audio_path: str
    duration_seconds: float


class RenderedVisualResult(BaseModel):
    scene_clips: list[RenderedSceneClip] = Field(default_factory=list)
    image_paths: list[str] = Field(default_factory=list)
    preview_path: str | None = None
    duration_hint_seconds: float | None = None
    artifacts: dict[str, ArtifactMeta] = Field(default_factory=dict)


class AssemblyResult(BaseModel):
    video_path: str
    thumbnail_path: str
    duration_seconds: float


class VideoGenerateResponse(BaseModel):
    id: int
    status: str
    renderer: str = "image"

    class Config:
        from_attributes = True


class VideoStatusResponse(BaseModel):
    id: int
    status: str
    progress_pct: int
    title: Optional[str] = None
    duration_seconds: Optional[float] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    created_at: Optional[str] = None
    error_message: Optional[str] = None
    style: Optional[str] = None
    renderer: str = "image"

    class Config:
        from_attributes = True


class VideoListItem(BaseModel):
    id: int
    title: Optional[str] = None
    status: str
    duration_seconds: Optional[float] = None
    style: Optional[str] = None
    created_at: Optional[str] = None
    renderer: str = "image"

    class Config:
        from_attributes = True
