import os
from typing import List, Optional
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from pydantic import AnyUrl, ValidationError
from sqlalchemy.orm import Session

from app.models.material_model import FileType as ModelFileType
from app.models.material_model import UploadedFile
from app.models.user_model import User
from app.schemas.material_schema import FileType as SchemaFileType
from app.core.task_dispatcher import dispatch_task
from app.core.storage import get_storage

UPLOAD_PREFIX = "uploads"


# Validate the URL
def _validate_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None

    try:
        validated_url = AnyUrl(url)
        return str(validated_url)
    except ValidationError:
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


# Create a uploaded file
async def create_uploaded_file(
    *,
    file_type: SchemaFileType,
    file: Optional[UploadFile],
    url: Optional[str],
    db: Session,
    current_user: User,
    space_id: Optional[int] = None,
) -> UploadedFile:
    if not file and not url:
        raise HTTPException(status_code=400, detail="Provide either a file or a URL.")

    validated_url_str = _validate_url(url)

    stored_path = None
    original_name = None
    if file:
        ext = os.path.splitext(file.filename or "default.bin")[1]
        unique_name = f"{uuid4()}{ext}"
        key = f"{UPLOAD_PREFIX}/{current_user.id}/{unique_name}"
        storage = get_storage()
        original_name = file.filename
        content = await file.read()
        stored_path = storage.upload(content, key)

    new_file = UploadedFile(
        stored_path=stored_path,
        url=validated_url_str,
        file_type=ModelFileType(file_type.value),
        name=original_name,
        user_id=current_user.id,
        space_id=space_id,
    )
    db.add(new_file)
    db.commit()
    db.refresh(new_file)

    # Update space content count if scoped to a space
    if space_id:
        from app.services.space_service import recalculate_content_count

        recalculate_content_count(space_id=space_id, db=db)

    dispatch_task("process_document", {"file_id": new_file.id})
    return new_file


# Get the status of a file
def get_user_file_status(
    *, file_id: int, db: Session, current_user: User
) -> UploadedFile:
    file_record = (
        db.query(UploadedFile)
        .filter(UploadedFile.id == file_id, UploadedFile.user_id == current_user.id)
        .first()
    )

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    return file_record


# List all files for a user
def list_user_files(
    *, db: Session, current_user: User, space_id: Optional[int] = None
) -> List[UploadedFile]:
    query = db.query(UploadedFile).filter(UploadedFile.user_id == current_user.id)
    if space_id is not None:
        query = query.filter(UploadedFile.space_id == space_id)
    return query.order_by(UploadedFile.uploaded_at.desc()).all()


# Rename an uploaded file
def rename_uploaded_file(
    *, file_id: int, new_name: str, db: Session, current_user: User
) -> UploadedFile:
    file_record = (
        db.query(UploadedFile)
        .filter(UploadedFile.id == file_id, UploadedFile.user_id == current_user.id)
        .first()
    )
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    file_record.name = new_name
    db.commit()
    db.refresh(file_record)
    return file_record


# Delete an uploaded file
def delete_uploaded_file(*, file_id: int, db: Session, current_user: User) -> None:
    file_record = (
        db.query(UploadedFile)
        .filter(UploadedFile.id == file_id, UploadedFile.user_id == current_user.id)
        .first()
    )
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    # 1. Clean up Pinecone vectors if the file has chunks
    from app.models.material_model import DocumentChunk
    from app.services.document_processor import get_pinecone_index
    from app.core.config import settings

    chunks = (
        db.query(DocumentChunk).filter(DocumentChunk.source_file_id == file_id).all()
    )
    if chunks:
        vector_ids = [chunk.vector_id for chunk in chunks]
        try:
            index = get_pinecone_index()
            index.delete(ids=vector_ids, namespace=settings.PINECONE_NAMESPACE)
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(
                f"Failed to delete Pinecone vectors for file {file_id}: {e}"
            )

    # 2. Clean up file from storage backend
    if file_record.stored_path:
        try:
            storage = get_storage()
            stored = file_record.stored_path
            if stored.startswith("r2://"):
                # Extract R2 key: "r2://bucket/key" → "key"
                key = stored.split("//", 1)[1].split("/", 1)[1]
                storage.delete(key)
            elif os.path.exists(stored):
                os.remove(stored)
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(
                f"Failed to delete stored file {file_record.stored_path}: {e}"
            )

    # 3. Delete database record (cascades to document_chunks)
    db.delete(file_record)
    db.commit()
