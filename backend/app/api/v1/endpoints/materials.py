import os
from uuid import uuid4
from typing import Optional
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
    Depends,
    BackgroundTasks,
)
from pydantic import AnyUrl, ValidationError, BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.material import UploadedFile, FileType, ProcessingStatus
from app.schemas.material import UploadedFileResponse, FileType
from app.models.user import User
from app.api.deps import get_current_active_user
from app.core.config import settings
from app.tasks.material_tasks import process_document_task

from app.services.document_processor import embeddings
from langchain.chat_models import ChatOpenAI
from langchain.schema.runnable import RunnablePassthrough
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser

router = APIRouter()
UPLOAD_DIR = "storage/uploads"


@router.post("/file", response_model=UploadedFileResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file_type: FileType = Form(...),
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # This endpoint now handles validation correctly.
    if not file and not url:
        raise HTTPException(status_code=400, detail="Provide either a file or a URL.")

    # This block ensures the URL is valid *before* we try to save it.
    validated_url_str: Optional[str] = None
    if url:
        try:
            validated_url = AnyUrl(url)
            validated_url_str = str(validated_url)
        except ValidationError:
            # If validation fails, immediately raise a 422 error with a clear message.
            raise HTTPException(
                status_code=422,
                detail=[
                    {
                        "loc": ["body", "url"],
                        "msg": "Invalid URL format provided.",
                        "type": "value_error.url.parsing",
                    }
                ],
            )

    stored_path = None
    original_name = None
    if file:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        ext = os.path.splitext(file.filename or "default.bin")[1]
        unique_name = f"{uuid4()}{ext}"
        stored_path = os.path.join(UPLOAD_DIR, unique_name)

        original_name = file.filename
        with open(stored_path, "wb") as f:
            f.write(await file.read())

    # Create the DB record using the pre-validated URL string.
    new_file = UploadedFile(
        stored_path=stored_path,
        url=validated_url_str,
        file_type=file_type,
        name=original_name,
        user_id=current_user.id,
    )
    db.add(new_file)
    db.commit()
    db.refresh(new_file)

    # *** TRIGGER THE BACKGROUND TASK ***
    # Instead of processing here, we call the Celery task.
    process_document_task.delay(new_file.id)

    return new_file


# NEW: Endpoint to check the processing status of a file
class StatusResponse(BaseModel):
    id: int
    name: str
    status: ProcessingStatus
    error_message: Optional[str] = None


@router.get("/{file_id}/status", response_model=StatusResponse)
def get_file_status(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    file_record = (
        db.query(UploadedFile)
        .filter(UploadedFile.id == file_id, UploadedFile.user_id == current_user.id)
        .first()
    )

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    return file_record
