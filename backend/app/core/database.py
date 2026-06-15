from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from app.core.config import settings

# Build connect_args for Neon PostgreSQL SSL
connect_args = {}
if settings.DATABASE_SSL_MODE and settings.DATABASE_SSL_MODE != "disable":
    connect_args["sslmode"] = settings.DATABASE_SSL_MODE

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_size=5,           # Neon free tier: limited connections
    max_overflow=2,        # Small overflow for burst
    pool_timeout=30,
    pool_recycle=300,      # Recycle connections every 5 min (Neon idle timeout)
    pool_pre_ping=True,    # Detect stale connections from Neon's auto-suspend
    poolclass=QueuePool,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()