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
from app.tasks.material_tasks import process_document_task

UPLOAD_DIR = "storage/uploads"


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


async def create_uploaded_file(
    *,
    file_type: SchemaFileType,
    file: Optional[UploadFile],
    url: Optional[str],
    db: Session,
    current_user: User,
) -> UploadedFile:
    if not file and not url:
        raise HTTPException(status_code=400, detail="Provide either a file or a URL.")

    validated_url_str = _validate_url(url)

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

    new_file = UploadedFile(
        stored_path=stored_path,
        url=validated_url_str,
        file_type=ModelFileType(file_type.value),
        name=original_name,
        user_id=current_user.id,
    )
    db.add(new_file)
    db.commit()
    db.refresh(new_file)

    process_document_task.delay(new_file.id)
    return new_file


def get_user_file_status(*, file_id: int, db: Session, current_user: User) -> UploadedFile:
    file_record = (
        db.query(UploadedFile)
        .filter(UploadedFile.id == file_id, UploadedFile.user_id == current_user.id)
        .first()
    )

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    return file_record


def list_user_files(*, db: Session, current_user: User) -> List[UploadedFile]:
    return (
        db.query(UploadedFile)
        .filter(UploadedFile.user_id == current_user.id)
        .order_by(UploadedFile.uploaded_at.desc())
        .all()
    )
