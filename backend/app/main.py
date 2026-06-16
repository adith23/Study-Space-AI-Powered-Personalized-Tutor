from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api_routes import api_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.logging_config import setup_logging

# Configure structured logging
setup_logging(environment=settings.ENVIRONMENT)

# Import models to register them with SQLAlchemy
from app.models import (
    chat_model,
    flashcard_model,
    material_model,
    quiz_model,
    space_model,
    user_model,
    video_model,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Set up metrics middleware (Prometheus counters/histograms)
from app.core.middleware import MetricsMiddleware

app.add_middleware(MetricsMiddleware)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {
        "message": "Welcome to Study Space API",
        "version": settings.VERSION,
        "docs_url": f"{settings.API_V1_STR}/docs",
    }
