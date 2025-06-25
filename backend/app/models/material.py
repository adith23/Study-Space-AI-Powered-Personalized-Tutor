from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class FileType(str, enum.Enum):
    notes = "notes"
    syllabus = "syllabus"
    pdf = "pdf"
    book = "book"
    video = "video"
    web_link = "web_link"
    youtube = "youtube"

class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)
    stored_path = Column(String, nullable=True)
    url = Column(String, nullable=True)
    file_type = Column(Enum(FileType), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())