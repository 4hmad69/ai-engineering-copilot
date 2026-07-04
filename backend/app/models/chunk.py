from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.document import DocumentRecord
    from backend.app.models.project import ProjectRecord

DB_SCHEMA = "ai_copilot"


class ChunkRecord(Base):
    __tablename__ = "chunks"
    __table_args__ = (
        UniqueConstraint("project_id", "chunk_uid", name="uq_chunks_project_chunk_uid"),
        Index("ix_chunks_project_file_path", "project_id", "file_path"),
        Index("ix_chunks_project_file_lines", "project_id", "file_path", "start_line", "end_line"),
        {"schema": DB_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    chunk_uid: Mapped[str] = mapped_column(String(64), nullable=False)

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{DB_SCHEMA}.projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{DB_SCHEMA}.documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_type: Mapped[str] = mapped_column(String(100), nullable=False)

    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    line_count: Mapped[int] = mapped_column(Integer, nullable=False)

    character_count: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_tokens: Mapped[int] = mapped_column(Integer, nullable=False)

    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    project: Mapped[ProjectRecord] = relationship(back_populates="chunks")
    document: Mapped[DocumentRecord] = relationship(back_populates="chunks")