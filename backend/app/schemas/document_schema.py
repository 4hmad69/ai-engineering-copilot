from pydantic import BaseModel, Field, model_validator


class LoadedDocumentMetadata(BaseModel):
    project_id: str
    file_path: str
    file_type: str
    extension: str
    size_bytes: int
    line_count: int
    content_hash: str


class LoadedDocumentsResponse(BaseModel):
    project_id: str
    project_path: str
    documents_count: int
    total_lines: int
    total_size_bytes: int
    documents: list[LoadedDocumentMetadata]


class ChunkingRequest(BaseModel):
    chunk_size_lines: int = Field(
        default=80,
        ge=20,
        le=250,
        description="Number of lines per chunk",
    )
    overlap_lines: int = Field(
        default=12,
        ge=0,
        le=80,
        description="Number of overlapping lines between chunks",
    )

    @model_validator(mode="after")
    def validate_overlap(self) -> "ChunkingRequest":
        if self.overlap_lines >= self.chunk_size_lines:
            raise ValueError("overlap_lines must be smaller than chunk_size_lines")

        return self


class DocumentChunkPreview(BaseModel):
    chunk_id: str
    project_id: str
    file_path: str
    file_type: str
    start_line: int
    end_line: int
    line_count: int
    character_count: int
    estimated_tokens: int
    content_hash: str
    content_preview: str


class ChunkPreviewResponse(BaseModel):
    project_id: str
    project_path: str
    chunk_size_lines: int
    overlap_lines: int
    source_documents_count: int
    chunks_count: int
    chunks_preview_count: int
    chunks: list[DocumentChunkPreview]
