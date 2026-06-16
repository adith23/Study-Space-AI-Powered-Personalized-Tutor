import os

from celery import Celery
from dotenv import load_dotenv

from app.core.config import settings

load_dotenv()

# Prevent HuggingFace Hub from using Xet backend which causes deadlocks in Celery thread pools on Windows
os.environ["HF_HUB_DISABLE_XET"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Initialize Celery
celery_app = Celery(
    "tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.material_tasks",
        "app.tasks.quiz_tasks",
        "app.tasks.flashcard_tasks",
        "app.tasks.video_tasks",
    ],
)

# Optional configuration
celery_app.conf.update(
    task_track_started=True,
)

# Register all SQLAlchemy models so relationship string references resolve correctly
from app.models import (chat_model, flashcard_model,  # noqa: F401, E402
                        material_model, quiz_model, space_model, user_model,
                        video_model)
