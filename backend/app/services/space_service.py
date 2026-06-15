import logging
import os
import shutil
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.models.material_model import DocumentChunk, UploadedFile
from app.models.space_model import Space
from app.models.user_model import User

logger = logging.getLogger(__name__)


def create_space(*, data: dict, db: Session, current_user: User) -> Space:
    """Create a new space for the user."""
    space = Space(
        user_id=current_user.id,
        name=data["name"],
        description=data.get("description"),
        icon=data.get("icon", "layout-grid"),
        color=data.get("color", "#00c875"),
        is_public=data.get("is_public", False),
    )
    db.add(space)
    db.commit()
    db.refresh(space)
    return space


def create_default_space(*, db: Session, user: User) -> Space:
    """Create a default space for a newly registered user."""
    space = Space(
        user_id=user.id,
        name="My First Space",
        description="Your default study space — start adding content!",
        icon="layout-grid",
        color="#00c875",
        is_public=False,
    )
    db.add(space)
    db.commit()
    db.refresh(space)
    return space


def list_user_spaces(*, db: Session, current_user: User) -> List[Space]:
    """List all spaces for a user, ordered by last accessed."""
    return (
        db.query(Space)
        .filter(Space.user_id == current_user.id)
        .order_by(Space.last_accessed_at.desc())
        .all()
    )


def get_space(*, space_id: int, db: Session, current_user: User) -> Space:
    """Get a single space, verify ownership."""
    space = (
        db.query(Space)
        .filter(Space.id == space_id, Space.user_id == current_user.id)
        .first()
    )
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    return space


def get_space_or_public(*, space_id: int, db: Session) -> Space:
    """Get a space by ID — returns it if it's public (for explore feature)."""
    space = db.query(Space).filter(Space.id == space_id).first()
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    if not space.is_public:
        raise HTTPException(status_code=403, detail="Space is not public")
    return space


def update_space(*, space_id: int, data: dict, db: Session, current_user: User) -> Space:
    """Update space metadata."""
    space = get_space(space_id=space_id, db=db, current_user=current_user)
    for key, value in data.items():
        if value is not None:
            setattr(space, key, value)
    db.commit()
    db.refresh(space)
    return space


def delete_space(*, space_id: int, db: Session, current_user: User) -> None:
    """
    Delete a space and permanently clean up all its contents:
    - Pinecone vectors for all files in the space
    - Physical files on disk
    - Video files on disk
    - Database records (cascade handles child rows)
    """
    space = get_space(space_id=space_id, db=db, current_user=current_user)

    # 1. Clean up Pinecone vectors for all files in the space
    files = db.query(UploadedFile).filter(UploadedFile.space_id == space_id).all()
    for file_record in files:
        chunks = db.query(DocumentChunk).filter(DocumentChunk.source_file_id == file_record.id).all()
        if chunks:
            vector_ids = [chunk.vector_id for chunk in chunks]
            try:
                from app.services.document_processor import get_pinecone_index
                from app.core.config import settings
                index = get_pinecone_index()
                index.delete(ids=vector_ids, namespace=settings.PINECONE_NAMESPACE)
            except Exception as e:
                logger.error(f"Failed to delete Pinecone vectors for file {file_record.id}: {e}")

        # 2. Clean up physical file on disk
        if file_record.stored_path and os.path.exists(file_record.stored_path):
            try:
                os.remove(file_record.stored_path)
            except Exception as e:
                logger.error(f"Failed to delete physical file {file_record.stored_path}: {e}")

    # 3. Clean up video files on disk
    from app.models.video_model import GeneratedVideo
    from app.core.config import settings

    videos = db.query(GeneratedVideo).filter(GeneratedVideo.space_id == space_id).all()
    for video in videos:
        video_dir = os.path.join(settings.VIDEO_STORAGE_PATH, str(video.id))
        if os.path.isdir(video_dir):
            shutil.rmtree(video_dir, ignore_errors=True)

    # 4. Delete space (cascades to all child records)
    db.delete(space)
    db.commit()


def touch_space_access(*, space_id: int, db: Session) -> None:
    """Update last_accessed_at timestamp."""
    db.query(Space).filter(Space.id == space_id).update(
        {"last_accessed_at": func.now()}
    )
    db.commit()


def recalculate_content_count(*, space_id: int, db: Session) -> None:
    """Recalculate the content_count for a space based on uploaded files."""
    count = db.query(UploadedFile).filter(UploadedFile.space_id == space_id).count()
    db.query(Space).filter(Space.id == space_id).update({"content_count": count})
    db.commit()


def explore_public_spaces(
    *, db: Session, query: Optional[str] = None, limit: int = 20, offset: int = 0
) -> List[dict]:
    """
    List public spaces for the explore/discovery feature.
    Optionally filter by name using a search query.
    """
    q = (
        db.query(Space, User.username)
        .join(User, Space.user_id == User.id)
        .filter(Space.is_public == True)
    )
    if query:
        q = q.filter(Space.name.ilike(f"%{query}%"))

    results = (
        q.order_by(Space.content_count.desc(), Space.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": space.id,
            "user_id": space.user_id,
            "name": space.name,
            "description": space.description,
            "icon": space.icon,
            "color": space.color,
            "content_count": space.content_count,
            "owner_username": username,
            "created_at": space.created_at,
        }
        for space, username in results
    ]
