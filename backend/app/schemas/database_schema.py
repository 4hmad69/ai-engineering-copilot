from typing import Literal

from pydantic import BaseModel, Field


class DatabaseHealthResponse(BaseModel):
    status: Literal["ok"] = Field(..., description="Database health status")
    database_name: str = Field(..., description="Connected PostgreSQL database name")
    database_user: str = Field(..., description="Connected PostgreSQL user")
    pgvector_enabled: bool = Field(..., description="Whether pgvector extension is enabled")
    pgvector_version: str | None = Field(None, description="Installed pgvector extension version")
    latency_ms: float = Field(..., description="Database health query latency in milliseconds")