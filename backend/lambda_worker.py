"""
AWS Lambda entry point for the SQS-triggered worker.

Receives task messages from SQS and routes them to the appropriate
service function. Each SQS message contains:
    {"task_name": "...", "payload": {...}}

This handler creates its own database session per task, matching
the pattern used by the existing Celery tasks.
"""

import json
import logging
import os
import traceback

# Redirect caches to writeable /tmp directory for AWS Lambda execution
os.environ["HF_HOME"] = "/tmp/huggingface"
os.environ["TORCH_HOME"] = "/tmp/torch"
os.environ["XDG_CACHE_HOME"] = "/tmp/cache"
os.environ["DOCLING_ARTIFACTS_PATH"] = "/var/task/docling-artifacts"

# Load secrets from SSM at cold start (before importing app modules)
os.environ.setdefault("ENVIRONMENT", "production")
from app.core.secrets import load_ssm_secrets  # noqa: E402

load_ssm_secrets()

# Register all SQLAlchemy models so relationship string references resolve correctly
from app.models import (  # noqa: F401, E402
    chat_model,
    flashcard_model,
    material_model,
    quiz_model,
    space_model,
    user_model,
    video_model,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handler(event, context):
    """
    Lambda handler triggered by SQS.

    Args:
        event: SQS event containing Records[].body with task JSON.
        context: Lambda context object.

    Returns:
        Summary dict of processed tasks.
    """
    from app.core.database import SessionLocal

    results = []
    failures = []

    for record in event.get("Records", []):
        message_body = json.loads(record["body"])
        task_name = message_body.get("task_name")
        payload = message_body.get("payload", {})

        logger.info("Processing task: %s | payload: %s", task_name, json.dumps(payload))

        db = SessionLocal()
        try:
            result = _route_task(task_name, payload, db)
            results.append(
                {"task": task_name, "status": "success", "result": str(result)}
            )
            logger.info("Task %s completed successfully", task_name)
        except Exception as e:
            logger.error("Task %s failed: %s\n%s", task_name, e, traceback.format_exc())
            results.append({"task": task_name, "status": "error", "error": str(e)})
            failures.append((task_name, e))
        finally:
            db.close()

    if failures:
        # Re-raise the first exception to signal Lambda failure to SQS (enables SQS retries & DLQ routing)
        raise failures[0][1]

    return {"processed": len(results), "results": results}


def _route_task(task_name: str, payload: dict, db):
    """Route task to the appropriate service function."""
    if task_name == "process_document":
        from app.services.document_processor import process_and_embed_document

        return process_and_embed_document(db=db, file_id=payload["file_id"])

    elif task_name == "generate_quiz":
        from app.services.quiz_service import generate_quiz_for_id

        return generate_quiz_for_id(db=db, quiz_id=payload["quiz_id"])

    elif task_name == "generate_flashcard":
        from app.services.flashcard_service import generate_flashcard_deck_for_id

        return generate_flashcard_deck_for_id(db=db, deck_id=payload["deck_id"])

    elif task_name == "generate_video":
        from app.services.video.video_generation_service import run_video_pipeline

        return run_video_pipeline(db=db, video_id=payload["video_id"])

    else:
        raise ValueError(f"Unknown task: {task_name}")
