from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user_model import User
from app.schemas.material_schema import FileType as SchemaFileType
from app.schemas.material_schema import StatusResponse
from app.schemas.material_schema import UploadedFileResponse
from app.services.material_service import (
    create_uploaded_file,
    get_user_file_status,
    list_user_files,
)

router = APIRouter()

# Upload a file
@router.post("/file", response_model=UploadedFileResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file_type: SchemaFileType = Form(...),
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return await create_uploaded_file(
        file_type=file_type,
        file=file,
        url=url,
        db=db,
        current_user=current_user,
    )

# Get all files for a user
@router.get("/files", response_model=List[UploadedFileResponse])
def get_files(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return list_user_files(db=db, current_user=current_user)

# Get the status of a file
@router.get("/{file_id}/status", response_model=StatusResponse)
def get_file_status(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return get_user_file_status(file_id=file_id, db=db, current_user=current_user)
