from celery import Celery
from app.core.config import settings
from dotenv import load_dotenv
import os

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
