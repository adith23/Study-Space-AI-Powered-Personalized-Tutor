import enum
from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.user import User


class FileType(str, enum.Enum):
    notes = "notes"
    syllabus = "syllabus"
    pdf = "pdf"
    book = "book"
    video = "video"
    web_link = "web_link"
    youtube = "youtube"


# NEW: Enum for processing status
class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)  # Add this line
    stored_path = Column(String, nullable=True)
    url = Column(String, nullable=True)
    file_type = Column(Enum(FileType), nullable=False)

    # NEW/MODIFIED Fields
    status = Column(
        Enum(ProcessingStatus), default=ProcessingStatus.PENDING, nullable=False
    )
    error_message = Column(String, nullable=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False
    )  # Ensure you have a users table

    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User")  # Define relationship to User model
    chunks = relationship(
        "DocumentChunk", back_populates="source_file", cascade="all, delete-orphan"
    )

    # NEW: Model for text chunks and their embeddings


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)

    # NEW: A reference to the ID of the vector stored in Pinecone
    vector_id = Column(String, nullable=False, unique=True)

    metadata_ = Column(JSON, name="metadata", nullable=True)  # Store page number, etc.

    source_file_id = Column(Integer, ForeignKey("uploaded_files.id"), nullable=False)
    source_file = relationship("UploadedFile", back_populates="chunks")
