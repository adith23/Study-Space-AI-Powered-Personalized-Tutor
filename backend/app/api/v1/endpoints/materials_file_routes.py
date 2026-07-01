import os
from typing import List, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user_model import User
from app.schemas.material_schema import FileType as SchemaFileType
from app.schemas.material_schema import (
    StatusResponse,
    UploadedFileResponse,
    UploadedFileUpdate,
)
from app.services.material_service import (
    create_uploaded_file,
    delete_uploaded_file,
    get_user_file_status,
    list_user_files,
    rename_uploaded_file,
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


# Stream file status updates for real-time frontend monitoring using SSE
@router.get("/files/status/stream")
async def stream_file_statuses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Stream file status updates for the current user using Server-Sent Events (SSE).
    """
    import asyncio
    import json

    async def event_generator():
        try:
            while True:
                files = list_user_files(db=db, current_user=current_user)
                payload = [
                    {
                        "id": f.id,
                        "name": f.name,
                        "status": f.status,
                        "error_message": getattr(f, "error_message", None),
                    }
                    for f in files
                ]
                yield f"data: {json.dumps(payload)}\n\n"
                await asyncio.sleep(2)
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# Get the status of a file
@router.get("/{file_id}/status", response_model=StatusResponse)
def get_file_status(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return get_user_file_status(file_id=file_id, db=db, current_user=current_user)


# Serve raw file content for the document viewer
@router.get("/files/{file_id}/content")
def download_file_content(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    file_record = get_user_file_status(
        file_id=file_id, db=db, current_user=current_user
    )

    if not file_record.stored_path:
        raise HTTPException(status_code=404, detail="File content path not found")

    stored_path = str(file_record.stored_path)
    if stored_path.startswith("r2://") or stored_path.startswith("s3://"):
        from fastapi.responses import RedirectResponse

        from app.core.storage import get_storage

        storage = get_storage()
        key = stored_path.split("//", 1)[1].split("/", 1)[1]
        presigned_url = storage.get_presigned_url(key, expires_in=3600)
        return RedirectResponse(url=presigned_url)

    if not os.path.exists(stored_path):
        raise HTTPException(status_code=404, detail="File content not found on disk")

    return FileResponse(
        path=stored_path,
        filename=file_record.name or "document",
        media_type="application/octet-stream",
    )


# Rename a file
@router.put("/files/{file_id}/rename", response_model=UploadedFileResponse)
def rename_file(
    file_id: int,
    payload: UploadedFileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return rename_uploaded_file(
        file_id=file_id, new_name=payload.name, db=db, current_user=current_user
    )


# Delete a file
@router.delete("/files/{file_id}", status_code=204)
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    delete_uploaded_file(file_id=file_id, db=db, current_user=current_user)
    return None
