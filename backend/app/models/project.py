from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.chunk import ChunkRecord
    from backend.app.models.document import DocumentRecord

DB_SCHEMA = "ai_copilot"


class ProjectRecord(Base):
    __tablename__ = "projects"
    __table_args__ = {"schema": DB_SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    saved_archive_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    extracted_project_path: Mapped[str] = mapped_column(String(1000), nullable=False)

    upload_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    extracted_files_count: Mapped[int] = mapped_column(Integer, nullable=False)

    documents_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chunks_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="uploaded")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    documents: Mapped[list[DocumentRecord]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    chunks: Mapped[list[ChunkRecord]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
