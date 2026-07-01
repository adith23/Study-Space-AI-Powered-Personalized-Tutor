"""
Database engine and session configuration.

Connection pooling strategy varies by environment:
  - **Development / API server**: ``QueuePool`` with connection reuse to avoid
    per-request SSL handshake overhead against Neon PostgreSQL.
  - **Production Lambda / Celery workers**: ``NullPool`` because each
    invocation is short-lived and connections cannot be shared across
    Lambda freeze/thaw cycles.

The ``get_db`` dependency yields a session that is guaranteed to close
even if the request handler raises an exception.
"""

import logging

from sqlalchemy import NullPool, QueuePool, create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── SSL connect args for Neon PostgreSQL ────────────────────────
connect_args: dict = {}
if settings.DATABASE_SSL_MODE and settings.DATABASE_SSL_MODE != "disable":
    connect_args["sslmode"] = settings.DATABASE_SSL_MODE

# ── Pool strategy based on runtime environment ──────────────────
#
# Lambda and Celery workers should use NullPool (no persistent connections).
# The API server benefits from QueuePool to reuse connections.
_is_worker = settings.ENVIRONMENT == "production" or settings.CELERY_BROKER_URL

if _is_worker:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args=connect_args,
        poolclass=NullPool,
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args=connect_args,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=300,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# ── Dependency ──────────────────────────────────────────────────


def get_db():
    """FastAPI dependency that yields a database session.

    The session is committed on success and rolled back on unhandled
    exceptions, then always closed to return the connection to the pool.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ── Health check helper ─────────────────────────────────────────


def check_db_health() -> bool:
    """Execute a lightweight query to verify database connectivity.

    Returns True if the database is reachable, False otherwise.
    Used by the /health endpoint.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error("Database health check failed: %s", exc)
        return False
