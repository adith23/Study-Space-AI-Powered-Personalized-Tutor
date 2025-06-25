from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import AnyUrl, ValidationError
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.material import UploadedFile
from app.schemas.material import UploadedFileResponse, FileType
from typing import Optional
import os
from uuid import uuid4

router = APIRouter()
UPLOAD_DIR = "storage/uploads"

@router.post("/file", response_model=UploadedFileResponse)
async def upload_file(
    file_type: FileType = Form(...),
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    db: Session = Depends(get_db)
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
                detail=[{"loc": ["body", "url"], "msg": "Invalid URL format provided.", "type": "value_error.url.parsing"}],
            )

    stored_path = None
    if file:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        if file.filename is None:
            raise HTTPException(status_code=400, detail="File must have a filename")
        ext = os.path.splitext(file.filename)[1]
        unique_name = f"{uuid4()}{ext}"
        stored_path = os.path.join(UPLOAD_DIR, unique_name)
        with open(stored_path, "wb") as f:
            f.write(await file.read())

    # Create the DB record using the pre-validated URL string.
    new_file = UploadedFile(
        stored_path=stored_path,
        url=validated_url_str,
        file_type=file_type,
    )
    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    
    return new_file