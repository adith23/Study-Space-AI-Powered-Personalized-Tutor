from celery import Celery
from app.core.config import settings
from dotenv import load_dotenv

load_dotenv()

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
