"""
Global test fixtures for the Study Space backend test suite.

Provides:
- In-memory SQLite test database with transactional rollback per test
- FastAPI TestClient with overridden DB dependency
- Pre-built user fixtures and JWT auth headers
- Sample PDF fixture for multipart upload tests
- Celery task mocks

See qa_testing_plan.md Section 5 for design rationale.
"""

import os
import sys
import uuid
from datetime import timedelta
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Base, get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
)
from app.main import app
from app.models.user_model import User

# ---------------------------------------------------------------------------
# SQLite in-memory engine with StaticPool
# ---------------------------------------------------------------------------
# StaticPool keeps a single persistent connection so that all operations within
# a test share the same in-memory database.
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


# Register a listener to handle PostgreSQL UUID columns on SQLite.
# SQLite stores UUIDs as plain strings; this ensures uuid values are
# serialised/deserialised correctly during tests.
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Database lifecycle (session-scoped: create tables once, drop at the end)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    """Create all tables once for the entire test session."""
    # Import every model module so SQLAlchemy registers them on Base.metadata
    from app.models import (  # noqa: F401
        chat_model,
        flashcard_model,
        material_model,
        quiz_model,
        user_model,
        video_model,
    )

    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# Per-test database session (transactional rollback for isolation)
# ---------------------------------------------------------------------------
@pytest.fixture()
def db_session():
    """Yield a DB session that is rolled back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# FastAPI TestClient with DB override
# ---------------------------------------------------------------------------
@pytest.fixture()
def client(db_session):
    """FastAPI TestClient wired to the transactional test database."""

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# User fixtures
# ---------------------------------------------------------------------------
_TEST_PASSWORD = "TestPassword123"
_SECOND_PASSWORD = "SecondPass456!"


@pytest.fixture()
def test_user(db_session):
    """A standard test user with known credentials."""
    user = User(
        username="teststudent",
        email="student@study-space.test",
        hashed_password=get_password_hash(_TEST_PASSWORD),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def second_user(db_session):
    """A second test user for cross-user data isolation tests."""
    user = User(
        username="otherstudent",
        email="other@study-space.test",
        hashed_password=get_password_hash(_SECOND_PASSWORD),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Auth header fixtures
# ---------------------------------------------------------------------------
@pytest.fixture()
def auth_headers(test_user):
    """Valid ``Authorization: Bearer <token>`` headers for *test_user*."""
    token = create_access_token(
        data={"sub": test_user.email, "user_id": str(test_user.id)}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def second_user_headers(second_user):
    """Valid ``Authorization: Bearer <token>`` headers for *second_user*."""
    token = create_access_token(
        data={"sub": second_user.email, "user_id": str(second_user.id)}
    )
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Sample file fixture for multipart upload tests
# ---------------------------------------------------------------------------
@pytest.fixture()
def sample_pdf(tmp_path):
    """Create a minimal (but technically valid) PDF file.

    Returns a tuple ``(path, bytes)`` suitable for use with TestClient::

        files = {"file": ("test.pdf", sample_pdf[1], "application/pdf")}
    """
    # Minimal valid PDF (Adobe spec says this is the smallest legal PDF)
    pdf_bytes = (
        b"%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj"
        b" 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj"
        b" 3 0 obj<</Type/Page/MediaBox[0 0 3 3]>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n"
        b"0000000058 00000 n \n0000000115 00000 n \n"
        b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF\n"
    )
    file_path = tmp_path / "test_document.pdf"
    file_path.write_bytes(pdf_bytes)
    return file_path, pdf_bytes


# ---------------------------------------------------------------------------
# Celery task mocks
# ---------------------------------------------------------------------------
@pytest.fixture()
def mock_celery_tasks():
    """Patch all Celery .delay() calls to be no-ops and record calls.

    Returns a dict of MagicMock objects keyed by task module path.
    """
    patches = [
        "app.services.material_service.process_document_task",
        "app.tasks.quiz_tasks.generate_quiz_task",
        "app.tasks.flashcard_tasks.generate_flashcard_deck_task",
        "app.tasks.video_tasks.generate_video_task",
    ]
    mocks = {}
    patchers = []
    for target in patches:
        p = patch(target)
        mock_obj = p.start()
        mocks[target] = mock_obj
        patchers.append(p)

    yield mocks

    for p in patchers:
        p.stop()
