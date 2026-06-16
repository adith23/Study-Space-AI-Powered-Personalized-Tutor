from sqlalchemy import NullPool, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# Build connect_args for Neon PostgreSQL SSL
connect_args = {}
if settings.DATABASE_SSL_MODE and settings.DATABASE_SSL_MODE != "disable":
    connect_args["sslmode"] = settings.DATABASE_SSL_MODE

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    poolclass=NullPool,
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
