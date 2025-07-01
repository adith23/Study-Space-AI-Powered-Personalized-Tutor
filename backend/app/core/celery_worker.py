from celery import Celery
from app.core.config import settings
from dotenv import load_dotenv

load_dotenv()

# Initialize Celery
# The first argument is the name of the current module.
# The `broker` argument specifies the URL of the message broker (Redis).
# The `backend` argument specifies the result backend.
celery_app = Celery(
    "tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.material_tasks"],  # Point to the module where tasks are defined
)

# Optional configuration
celery_app.conf.update(
    task_track_started=True,
)
