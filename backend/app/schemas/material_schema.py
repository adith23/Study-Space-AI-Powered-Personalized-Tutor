from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, HttpUrl

from app.models.material_model import ProcessingStatus

# File type enum
class FileType(str, Enum):
    notes = "notes"
    syllabus = "syllabus"
    pdf = "pdf"
    book = "book"
    video = "video"
    web_link = "web_link"
    youtube = "youtube"

# Uploaded file create schema
class UploadedFileCreate(BaseModel):
    file_type: FileType
    url: Optional[HttpUrl] = None

# Uploaded file response schema
class UploadedFileResponse(BaseModel):
    id: int
    url: Optional[HttpUrl] = None
    file_type: FileType
    name: Optional[str] = None
    status: ProcessingStatus
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# Status response schema
class StatusResponse(BaseModel):
    id: int
    name: str
    status: ProcessingStatus
    error_message: Optional[str] = None
