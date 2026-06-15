"""
Task dispatcher — sends async tasks to SQS (production) or Celery (development).

This abstraction allows the same API code to work in both environments:
- Production (Lambda): sends a JSON message to SQS → triggers Worker Lambda
- Development (local): calls Celery task.delay() as before
"""
import json
import logging
from typing import Any, Dict, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


def dispatch_task(
    task_name: str,
    payload: Dict[str, Any],
    *,
    delay_seconds: int = 0,
) -> Optional[str]:
    """
    Dispatch an async task.

    Args:
        task_name: One of "process_document", "generate_quiz",
                   "generate_flashcard", "generate_video".
        payload: Dict of kwargs for the task (e.g. {"file_id": 123}).
        delay_seconds: SQS delivery delay (0-900). Ignored for Celery.

    Returns:
        SQS MessageId or Celery task ID.
    """
    if settings.ENVIRONMENT == "production" and settings.SQS_QUEUE_URL:
        return _dispatch_sqs(task_name, payload, delay_seconds)
    else:
        return _dispatch_celery(task_name, payload)


def _dispatch_sqs(
    task_name: str, payload: Dict[str, Any], delay_seconds: int
) -> str:
    import boto3

    sqs = boto3.client("sqs", region_name=settings.AWS_REGION)
    message_body = json.dumps({
        "task_name": task_name,
        "payload": payload,
    })

    response = sqs.send_message(
        QueueUrl=settings.SQS_QUEUE_URL,
        MessageBody=message_body,
        DelaySeconds=min(delay_seconds, 900),
        MessageAttributes={
            "TaskName": {
                "DataType": "String",
                "StringValue": task_name,
            }
        },
    )
    message_id = response["MessageId"]
    logger.info("Dispatched task '%s' to SQS: %s", task_name, message_id)
    return message_id


def _dispatch_celery(task_name: str, payload: Dict[str, Any]) -> str:
    """Fall back to Celery for local development."""
    from app.tasks.material_tasks import process_document_task
    from app.tasks.quiz_tasks import generate_quiz_task
    from app.tasks.flashcard_tasks import generate_flashcard_deck_task
    from app.tasks.video_tasks import generate_video_task

    task_map = {
        "process_document": process_document_task,
        "generate_quiz": generate_quiz_task,
        "generate_flashcard": generate_flashcard_deck_task,
        "generate_video": generate_video_task,
    }

    task_func = task_map.get(task_name)
    if not task_func:
        raise ValueError(f"Unknown task: {task_name}")

    # All tasks accept a single positional int ID argument
    task_id_key = list(payload.keys())[0]  # e.g. "file_id", "quiz_id", etc.
    result = task_func.delay(payload[task_id_key])
    logger.info("Dispatched task '%s' to Celery: %s", task_name, result.id)
    return result.id
