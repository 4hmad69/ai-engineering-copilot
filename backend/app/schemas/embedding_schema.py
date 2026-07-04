from pydantic import BaseModel, Field


class EmbeddingIndexResponse(BaseModel):
    project_id: str
    chunks_found: int
    chunks_embedded: int
    embedding_model: str
    embedding_dimension: int
    batch_size: int
    message: str


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)


class SemanticSearchResult(BaseModel):
    chunk_id: str
    file_path: str
    file_type: str
    start_line: int
    end_line: int
    similarity_score: float
    distance: float
    content_preview: str


class SemanticSearchResponse(BaseModel):
    project_id: str
    query: str
    top_k: int
    results_count: int
    embedding_model: str
    results: list[SemanticSearchResult]