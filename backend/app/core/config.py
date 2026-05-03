from typing import List
from pydantic_settings import BaseSettings
from pydantic import validator
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "Study Space API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "AI-Powered Personalized Learning Platform"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str = os.getenv("DATABASE_URL")

    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND")

    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME")

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    GEMINI_CHAT_MODEL: str = "gemini-3.1-flash-lite-preview"

    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME")
    PINECONE_INDEX_HOST: str = os.getenv("PINECONE_INDEX_HOST", "")
    PINECONE_NAMESPACE: str = os.getenv("PINECONE_NAMESPACE", "__default__")
    PINECONE_INTEGRATED_TEXT_FIELD: str = os.getenv(
        "PINECONE_INTEGRATED_TEXT_FIELD", "text"
    )

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    VIDEO_STORAGE_PATH: str = os.getenv("VIDEO_STORAGE_PATH", "storage/generated/videos")
    FFMPEG_PATH: str = os.getenv("FFMPEG_PATH", "ffmpeg")
    FFPROBE_PATH: str = os.getenv("FFPROBE_PATH", "ffprobe")
    VIDEO_MAX_SCENES: int = int(os.getenv("VIDEO_MAX_SCENES", "3"))
    VIDEO_IMAGE_MODEL: str = os.getenv("VIDEO_IMAGE_MODEL", "gemini-2.5-flash-image")
    VIDEO_TTS_MODEL: str = os.getenv("VIDEO_TTS_MODEL", "gemini-2.5-flash-preview-tts")
    VIDEO_TTS_VOICE: str = os.getenv("VIDEO_TTS_VOICE", "Kore")

    MANIM_PYTHON_BIN: str = os.getenv("MANIM_PYTHON_BIN", "python")
    MANIM_CLI_BIN: str = os.getenv("MANIM_CLI_BIN", "manim")
    MANIM_RENDER_QUALITY: str = os.getenv("MANIM_RENDER_QUALITY", "m")
    MANIM_MEDIA_DIR: str = os.getenv("MANIM_MEDIA_DIR", "")
    MANIM_DISABLE_CACHING: bool = os.getenv("MANIM_DISABLE_CACHING", "true").lower() == "true"
    MANIM_TEX_ENABLED: bool = os.getenv("MANIM_TEX_ENABLED", "false").lower() == "true"
    MANIM_RENDER_TIMEOUT_SECONDS: int = int(
        os.getenv("MANIM_RENDER_TIMEOUT_SECONDS", "300")
    )
    MANIM_MAX_SCENES: int = int(os.getenv("MANIM_MAX_SCENES", "8"))
    MANIM_MAX_BLOCKS_PER_SCENE: int = int(os.getenv("MANIM_MAX_BLOCKS_PER_SCENE", "5"))
    MANIM_MAX_TEXT_LENGTH: int = int(os.getenv("MANIM_MAX_TEXT_LENGTH", "240"))
    MANIM_MAX_PLOT_POINTS: int = int(os.getenv("MANIM_MAX_PLOT_POINTS", "12"))
    MANIM_MAX_TABLE_COLUMNS: int = int(os.getenv("MANIM_MAX_TABLE_COLUMNS", "4"))
    MANIM_MAX_TABLE_ROWS: int = int(os.getenv("MANIM_MAX_TABLE_ROWS", "6"))
    MANIM_MAX_FLOW_NODES: int = int(os.getenv("MANIM_MAX_FLOW_NODES", "6"))
    MANIM_MAX_EQUATION_STEPS: int = int(os.getenv("MANIM_MAX_EQUATION_STEPS", "6"))
    VIDEO_ALIGNMENT_TOLERANCE_SECONDS: float = float(
        os.getenv("VIDEO_ALIGNMENT_TOLERANCE_SECONDS", "0.35")
    )

    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
