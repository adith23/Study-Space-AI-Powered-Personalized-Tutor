from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user_model import User
from app.schemas.space_schema import (ExploreSpaceResponse, SpaceCreate,
                                      SpaceListResponse, SpaceResponse,
                                      SpaceUpdate)
from app.services.space_service import (create_space, delete_space,
                                        explore_public_spaces, get_space,
                                        list_user_spaces, touch_space_access,
                                        update_space)

router = APIRouter()


@router.post("/", response_model=SpaceResponse, status_code=201)
def create_new_space(
    payload: SpaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new space for the authenticated user."""
    return create_space(data=payload.model_dump(), db=db, current_user=current_user)


@router.get("/", response_model=List[SpaceListResponse])
def list_spaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all spaces owned by the authenticated user."""
    return list_user_spaces(db=db, current_user=current_user)


@router.get("/explore", response_model=List[ExploreSpaceResponse])
def explore_spaces(
    query: Optional[str] = Query(
        None, description="Search query to filter public spaces by name"
    ),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Discover public spaces from other users."""
    return explore_public_spaces(db=db, query=query, limit=limit, offset=offset)


@router.get("/{space_id}", response_model=SpaceResponse)
def get_single_space(
    space_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get full details for a space owned by the authenticated user."""
    space = get_space(space_id=space_id, db=db, current_user=current_user)
    touch_space_access(space_id=space_id, db=db)
    return space


@router.put("/{space_id}", response_model=SpaceResponse)
def update_existing_space(
    space_id: int,
    payload: SpaceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update space metadata (name, description, icon, color, is_public)."""
    return update_space(
        space_id=space_id,
        data=payload.model_dump(exclude_unset=True),
        db=db,
        current_user=current_user,
    )


@router.delete("/{space_id}", status_code=204)
def delete_existing_space(
    space_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a space and permanently remove all its contents (files, vectors, videos)."""
    delete_space(space_id=space_id, db=db, current_user=current_user)
    return None
