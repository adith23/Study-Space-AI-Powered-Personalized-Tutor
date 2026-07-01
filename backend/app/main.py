import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api_routes import api_router
from app.core.config import settings
from app.core.database import check_db_health
from app.core.logging_config import setup_logging

# Configure structured logging
setup_logging(environment=settings.ENVIRONMENT)

logger = logging.getLogger(__name__)

# Import all models to register them with SQLAlchemy's metadata registry.
# This is required for Alembic autogenerate and relationship resolution.
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events.

    Startup:
      - Verifies database connectivity (fails fast if unreachable).
      - Schema creation is handled by Alembic migrations, NOT create_all().

    Shutdown:
      - Placeholder for future cleanup (connection pool disposal, etc.).
    """
    # Verify database is reachable at startup
    if not check_db_health():
        logger.warning(
            "Database health check failed at startup. "
            "The application will start but some endpoints may fail."
        )
    else:
        logger.info("Database health check passed.")

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


@app.get("/health")
async def health():
    """Health check endpoint for Docker HEALTHCHECK and AWS Lambda Web Adapter.

    Returns 200 with service status if the API is running.
    Includes a database connectivity check.
    """
    db_healthy = check_db_health()
    status_code = 200 if db_healthy else 503

    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if db_healthy else "degraded",
            "version": settings.VERSION,
            "database": "connected" if db_healthy else "unreachable",
        },
    )
