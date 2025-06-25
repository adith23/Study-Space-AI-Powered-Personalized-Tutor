from typing import List
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "Study Space API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "AI-Powered Personalized Learning Platform"
    API_V1_STR: str = "/api/v1"
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://postgres:password1234@localhost:5432/StudySpace"
    
    # JWT Configuration
    JWT_SECRET_KEY: str = "your-secret-key-here"  # Change this to a secure secret key
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
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