import logging
from app.core.celery_worker import celery_app
from app.core.database import SessionLocal
from app.services.document_processor import process_and_embed_document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@celery_app.task(name="tasks.process_document_task")
def process_document_task(file_id: int):
    """
    Celery task to process an uploaded document.
    It creates a new database session to be independent of the web server's session.
    """
    logger.info(f"Celery task started for file_id: {file_id}")
    db = SessionLocal()
    try:
        process_and_embed_document(db=db, file_id=file_id)
        logger.info(f"Celery task finished for file_id: {file_id}")
    finally:
        db.close()

