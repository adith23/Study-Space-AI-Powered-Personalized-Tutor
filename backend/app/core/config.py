from typing import List
from pydantic_settings import BaseSettings
from pydantic import validator
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "Study Space API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "AI-Powered Personalized Learning Platform"
    API_V1_STR: str = "/api/v1"

    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # NEW: Redis/Celery Configuration
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND")

    # NEW: AI Model Configuration
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME")

    # NEW: Switched to Google Gemini
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    GEMINI_CHAT_MODEL: str = "gemini-3.1-flash-lite-preview"

    # NEW: Pinecone Configuration
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME")
    PINECONE_INDEX_HOST: str = os.getenv("PINECONE_INDEX_HOST", "")
    PINECONE_NAMESPACE: str = os.getenv("PINECONE_NAMESPACE", "__default__")
    PINECONE_INTEGRATED_TEXT_FIELD: str = os.getenv(
        "PINECONE_INTEGRATED_TEXT_FIELD", "text"
    )

    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",  # Vite dev server alternative
        "http://localhost:3000",  # React dev server
        "http://127.0.0.1:3000",  # React dev server alternative
    ]

    # Video Generation Configuration
    VIDEO_STORAGE_PATH: str = os.getenv(
        "VIDEO_STORAGE_PATH", "storage/generated/videos"
    )
    FFMPEG_PATH: str = os.getenv("FFMPEG_PATH", "ffmpeg")
    VIDEO_MAX_SCENES: int = int(os.getenv("VIDEO_MAX_SCENES", "3"))
    VIDEO_IMAGE_MODEL: str = os.getenv("VIDEO_IMAGE_MODEL", "gemini-2.5-flash-image")
    VIDEO_TTS_MODEL: str = os.getenv("VIDEO_TTS_MODEL", "gemini-2.5-flash-preview-tts")
    VIDEO_TTS_VOICE: str = os.getenv("VIDEO_TTS_VOICE", "Kore")

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
