from typing import List, Optional

from pydantic import BaseModel


# ── Request Schemas ──────────────────────────────────────────────────────────


class VideoGenerateRequest(BaseModel):
    file_ids: List[int]
    focus_prompt: Optional[str] = None
    style: str = "explainer"  # explainer | summary | deep_dive


# ── Internal Pipeline Schemas ────────────────────────────────────────────────


class VideoScene(BaseModel):
    scene_number: int
    narration_text: str
    visual_description: str
    duration_seconds: float
    key_concept: str


class VideoScript(BaseModel):
    title: str
    scenes: List[VideoScene]
    total_duration_seconds: float


# ── Response Schemas ─────────────────────────────────────────────────────────


class VideoGenerateResponse(BaseModel):
    id: int
    status: str

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

    class Config:
        from_attributes = True


class VideoListItem(BaseModel):
    id: int
    title: Optional[str] = None
    status: str
    duration_seconds: Optional[float] = None
    style: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
