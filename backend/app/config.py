from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Engineering Copilot"
    app_env: str = "development"
    app_version: str = "0.1.0"
    debug: bool = True

    api_prefix: str = "/api/v1"

    backend_host: str = "127.0.0.1"
    backend_port: int = 8000

    storage_dir: str = "storage"
    max_upload_size_mb: int = 50
    max_extracted_size_mb: int = 200
    max_project_files: int = 3000

    max_single_file_size_mb: int = 2
    file_preview_limit: int = 200

    chunk_preview_limit: int = 50
    default_chunk_size_lines: int = 80
    default_chunk_overlap_lines: int = 12

    postgres_user: str = "ai_copilot"
    postgres_password: str = "ai_copilot_password"
    postgres_db: str = "ai_copilot"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    database_url: str = (
        "postgresql+asyncpg://ai_copilot:ai_copilot_password@localhost:5432/ai_copilot"
    )
    database_echo: bool = False
    database_schema: str = "ai_copilot"

    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    embedding_batch_size: int = 16
    search_preview_character_limit: int = 900

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:3b"
    ollama_timeout_seconds: int = 120
    llm_temperature: float = 0.1

    rag_default_top_k: int = 5
    rag_max_context_characters: int = 12000
    rag_context_chunk_preview_limit: int = 900

    rag_retrieval_candidate_k: int = 20
    rag_mmr_lambda: float = 0.65
    rag_min_answer_similarity: float = 0.15

    model_config = SettingsConfigDict(
        env_file="backend/.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def storage_path(self) -> Path:
        return self.project_root / self.storage_dir

    @property
    def uploads_path(self) -> Path:
        return self.storage_path / "uploads"

    @property
    def projects_path(self) -> Path:
        return self.storage_path / "projects"

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def max_extracted_size_bytes(self) -> int:
        return self.max_extracted_size_mb * 1024 * 1024

    @property
    def max_single_file_size_bytes(self) -> int:
        return self.max_single_file_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
