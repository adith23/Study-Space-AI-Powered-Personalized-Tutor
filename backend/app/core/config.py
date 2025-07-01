from typing import List
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator
from pinecone import Pinecone


class Settings(BaseSettings):
    PROJECT_NAME: str = "Study Space API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "AI-Powered Personalized Learning Platform"
    API_V1_STR: str = "/api/v1"

    # Database Configuration
    DATABASE_URL: str = "postgresql://postgres:password1234@localhost:5432/StudySpace"

    # NEW: Redis/Celery Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # NEW: AI Model Configuration
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    OPENAI_API_KEY: str = "your-openai-api-key-here"  # IMPORTANT: Add your key

    # NEW: Pinecone Configuration
    PINECONE_API_KEY: str = (
        "pcsk_2hbFSb_6QL7j82EkvfPKSSgrp13H35ApaY5hkxVh1Mu56RRBtnvZehGRwAi8byZMKZLpmH"
    )
    PINECONE_ENVIRONMENT: str = "your-pinecone-environment-here"  # e.g., "gcp-starter"
    PINECONE_INDEX_NAME: str = "study-space-index"

    # JWT Configuration
    JWT_SECRET_KEY: str = "your-secret-key-here"  # Change this to a secure secret key
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 300000

    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",  # Vite dev server alternative
        "http://localhost:3000",  # React dev server
        "http://127.0.0.1:3000",  # React dev server alternative
    ]

    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v

    class Config:
        env_file = ".env"  # This will load environment variables from .env file


settings = Settings()
