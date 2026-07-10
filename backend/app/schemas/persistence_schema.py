from datetime import datetime

from pydantic import BaseModel, Field


class ProjectRecordResponse(BaseModel):
    project_id: str
    original_filename: str
    saved_archive_path: str
    extracted_project_path: str
    upload_size_bytes: int
    extracted_files_count: int
    documents_count: int
    chunks_count: int
    status: str
    created_at: datetime
    updated_at: datetime


class PersistedChunksResponse(BaseModel):
    project_id: str = Field(..., description="Project ID")
    documents_persisted: int = Field(..., description="Number of documents saved to PostgreSQL")
    chunks_persisted: int = Field(..., description="Number of chunks saved to PostgreSQL")
    chunk_size_lines: int
    overlap_lines: int
    message: str
