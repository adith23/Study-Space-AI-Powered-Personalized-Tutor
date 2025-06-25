from pydantic import BaseModel, HttpUrl
from typing import Optional
from enum import Enum

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

    class Config:
        orm_mode = True