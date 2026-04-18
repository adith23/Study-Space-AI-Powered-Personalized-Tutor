import logging

from app.core.celery_worker import celery_app
from app.core.database import SessionLocal
from app.services.video.video_generation_service import run_video_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.generate_video_task")
def generate_video_task(video_id: int):
    """
    Celery task to run the full video generation pipeline.
    Creates its own database session independent of the web server.
    """
    logger.info("Celery video task started for video_id: %d", video_id)
    db = SessionLocal()
    try:
        run_video_pipeline(db=db, video_id=video_id)
        logger.info("Celery video task finished for video_id: %d", video_id)
    finally:
        db.close()
