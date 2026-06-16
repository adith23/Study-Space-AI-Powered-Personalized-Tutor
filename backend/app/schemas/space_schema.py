from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SpaceCreate(BaseModel):
    """Schema for creating a new space."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    icon: Optional[str] = "layout-grid"
    color: Optional[str] = "#00c875"
    is_public: Optional[bool] = False


class SpaceUpdate(BaseModel):
    """Schema for updating an existing space."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_public: Optional[bool] = None


class SpaceResponse(BaseModel):
    """Full space detail response."""

    id: int
    user_id: int
    name: str
    description: Optional[str] = None
    icon: str
    color: str
    content_count: int
    is_public: bool
    created_at: datetime
    updated_at: datetime
    last_accessed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SpaceListResponse(BaseModel):
    """Lightweight space listing response."""

    id: int
    name: str
    icon: str
    color: str
    content_count: int
    is_public: bool
    last_accessed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ExploreSpaceResponse(BaseModel):
    """Public space listing for explore/discovery."""

    id: int
    user_id: int
    name: str
    description: Optional[str] = None
    icon: str
    color: str
    content_count: int
    owner_username: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
