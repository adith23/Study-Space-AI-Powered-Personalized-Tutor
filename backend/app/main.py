# Load secrets from SSM before anything else (Lambda cold start)
from app.core.secrets import load_ssm_secrets

load_ssm_secrets()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.api.v1.api_routes import api_router

# Configure structured logging
setup_logging(environment=settings.ENVIRONMENT)

# Import models to register them with SQLAlchemy
from app.models import user_model, material_model, chat_model, flashcard_model, quiz_model, video_model, space_model  

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
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


@app.on_event("startup")
def on_startup():
    # In production, use Alembic migrations instead of auto-create
    if settings.ENVIRONMENT == "development":
        Base.metadata.create_all(bind=engine)


@app.get("/health")
async def health_check():
    """Health check for CloudFront origin checks and monitoring."""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/")   
async def root():
    return {
        "message": "Welcome to Study Space API",
        "version": settings.VERSION,
        "docs_url": f"{settings.API_V1_STR}/docs",
    } 
