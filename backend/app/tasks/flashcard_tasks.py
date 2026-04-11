import logging

from app.core.celery_worker import celery_app
from app.core.database import SessionLocal
from app.services.flashcard_service import generate_flashcard_deck_for_id

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.generate_flashcard_deck_task")
def generate_flashcard_deck_task(deck_id: int):
    logger.info("Celery flashcard task started for deck_id: %s", deck_id)
    db = SessionLocal()
    try:
        generate_flashcard_deck_for_id(db=db, deck_id=deck_id)
        logger.info("Celery flashcard task finished for deck_id: %s", deck_id)
    finally:
        db.close()
