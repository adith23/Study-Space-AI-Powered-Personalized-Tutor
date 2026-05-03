import enum

from sqlalchemy import Column, String, Integer, Float, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class VideoStatus(str, enum.Enum):
    PENDING = "pending"
    SCRIPTING = "scripting"
    PLANNING_VISUALS = "planning_visuals"
    COMPILING_MANIM = "compiling_manim"
    RENDERING_MANIM = "rendering_manim"
    GENERATING_IMAGES = "generating_images"
    GENERATING_AUDIO = "generating_audio"
    ASSEMBLING = "assembling"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoStyle(str, enum.Enum):
    EXPLAINER = "explainer"
    SUMMARY = "summary"
    DEEP_DIVE = "deep_dive"


class VideoRenderer(str, enum.Enum):
    IMAGE = "image"
    MANIM = "manim"


class GeneratedVideo(Base):
    __tablename__ = "generated_videos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=True)

    status = Column(Enum(VideoStatus), default=VideoStatus.PENDING, nullable=False)
    progress_pct = Column(Integer, default=0, nullable=False)

    script_json = Column(JSON, nullable=True)
    render_spec_json = Column(JSON, nullable=True)
    artifacts_json = Column(JSON, nullable=True)

    style = Column(Enum(VideoStyle), default=VideoStyle.EXPLAINER, nullable=False)
    renderer = Column(Enum(VideoRenderer), default=VideoRenderer.IMAGE, nullable=False)
    duration_seconds = Column(Float, nullable=True)

    video_path = Column(String, nullable=True)
    thumbnail_path = Column(String, nullable=True)
    error_message = Column(String, nullable=True)

    source_file_ids = Column(JSON, nullable=False)
    focus_prompt = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User")
