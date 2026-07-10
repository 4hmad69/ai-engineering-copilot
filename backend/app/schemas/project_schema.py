from pydantic import BaseModel, Field


class ProjectFileMetadata(BaseModel):
    project_id: str = Field(..., description="Unique project ID")
    file_path: str = Field(..., description="Relative file path inside the extracted project")
    file_type: str = Field(..., description="Detected file type")
    extension: str = Field(..., description="File extension")
    size_bytes: int = Field(..., description="File size in bytes")
    line_count: int | None = Field(None, description="Number of lines if the file is text-readable")
    is_loadable: bool = Field(..., description="Whether this file can be loaded for RAG")
    skip_reason: str | None = Field(None, description="Reason the file was skipped")


class ProjectFilesResponse(BaseModel):
    project_id: str
    project_path: str
    total_files_seen: int
    loadable_files_count: int
    skipped_files_count: int
    files: list[ProjectFileMetadata]
