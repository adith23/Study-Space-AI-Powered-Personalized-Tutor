from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, HttpUrl

from app.models.material_model import ProcessingStatus

class FileType(str, Enum):
    notes = "notes"
    syllabus = "syllabus"
    pdf = "pdf"
    book = "book"
    video = "video"
    web_link = "web_link"
    youtube = "youtube"

class UploadedFileCreate(BaseModel):
    file_type: FileType
    url: Optional[HttpUrl] = None

class UploadedFileResponse(BaseModel):
    id: int
    stored_path: Optional[str] = None
    url: Optional[HttpUrl] = None
    file_type: FileType
    name: Optional[str] = None
    status: ProcessingStatus
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class StatusResponse(BaseModel):
    id: int
    name: str
    status: ProcessingStatus
    error_message: Optional[str] = None
