"""
SQLAlchemy model registry.

Importing this package ensures all models are registered on ``Base.metadata``,
which is required for Alembic autogenerate and ``Base.metadata.create_all()``
to work correctly.

Usage:
    import app.models  # registers all tables
"""

from app.models.chat_model import ChatMessage, ChatSession  # noqa: F401
from app.models.flashcard_model import (  # noqa: F401
    Flashcard,
    FlashcardDeck,
    FlashcardDeckSource,
)
from app.models.material_model import DocumentChunk, UploadedFile  # noqa: F401
from app.models.quiz_model import (  # noqa: F401
    Quiz,
    QuizAnswer,
    QuizAttempt,
    QuizQuestion,
    QuizSource,
)
from app.models.space_model import Space  # noqa: F401
from app.models.user_model import User  # noqa: F401
from app.models.video_model import GeneratedVideo  # noqa: F401
