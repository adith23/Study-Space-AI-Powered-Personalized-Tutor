import logging

from app.core.celery_worker import celery_app
from app.core.database import SessionLocal
from app.services.quiz_service import generate_quiz_for_id

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.generate_quiz_task")
def generate_quiz_task(quiz_id: int):
    logger.info("Celery quiz task started for quiz_id: %s", quiz_id)
    db = SessionLocal()
    try:
        generate_quiz_for_id(db=db, quiz_id=quiz_id)
        logger.info("Celery quiz task finished for quiz_id: %s", quiz_id)
    finally:
        db.close()
