"""
Reusable SQLAlchemy column mixins for cross-cutting concerns.

Usage:
    class MyModel(SoftDeleteMixin, TimestampMixin, Base):
        __tablename__ = "my_models"
        id = Column(Integer, primary_key=True)

Mixins are applied via multiple inheritance. Place them *before* Base
so their columns are added to the model's table.
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy.sql import func


class TimestampMixin:
    """Adds created_at and updated_at columns with timezone-aware defaults.

    Uses ``server_default=func.now()`` so the database clock is authoritative,
    avoiding drift between application servers.
    """

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """Adds an ``is_deleted`` flag and ``deleted_at`` timestamp.

    Models using this mixin are never physically removed from the database.
    Instead, ``is_deleted`` is set to True and ``deleted_at`` records when.

    Queries should filter with ``.filter(Model.is_deleted == False)``
    (or use a custom query manager) to exclude soft-deleted rows.

    This enables:
      - Audit trails and compliance (data is never lost)
      - Easy undo / restore operations
      - Referential integrity (foreign keys remain valid)
    """

    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    def soft_delete(self) -> None:
        """Mark this record as deleted without removing it from the database."""
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
