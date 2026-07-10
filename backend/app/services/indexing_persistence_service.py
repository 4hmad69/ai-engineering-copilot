import uuid
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import Settings
from backend.app.core.exceptions import (
    DatabaseConnectionError,
    InvalidInputError,
    ResourceNotFoundError,
)
from backend.app.models.chunk import ChunkRecord
from backend.app.models.document import DocumentRecord
from backend.app.models.project import ProjectRecord
from backend.app.schemas.document_schema import ChunkingRequest
from backend.app.schemas.persistence_schema import PersistedChunksResponse
from backend.app.services.document_loader_service import (
    load_project_documents,
    split_loaded_documents_into_chunks,
)

AVERAGE_CHARS_PER_TOKEN = 4


def _parse_project_uuid(project_id: str) -> UUID:
    try:
        return UUID(project_id)
    except ValueError as exc:
        raise InvalidInputError(
            "Invalid project_id format.",
            details={"project_id": project_id},
        ) from exc


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // AVERAGE_CHARS_PER_TOKEN)


async def persist_project_documents_and_chunks(
    project_id: str,
    request: ChunkingRequest,
    settings: Settings,
    session: AsyncSession,
) -> PersistedChunksResponse:
    project_uuid = _parse_project_uuid(project_id)

    _, documents = load_project_documents(
        project_id=project_id,
        settings=settings,
    )

    chunks = split_loaded_documents_into_chunks(
        documents=documents,
        request=request,
    )

    document_records: list[DocumentRecord] = []
    document_id_by_file_path: dict[str, uuid.UUID] = {}

    for document in documents:
        document_id = uuid.uuid4()
        document_id_by_file_path[document.metadata.file_path] = document_id

        document_records.append(
            DocumentRecord(
                id=document_id,
                project_id=project_uuid,
                file_path=document.metadata.file_path,
                file_type=document.metadata.file_type,
                extension=document.metadata.extension,
                size_bytes=document.metadata.size_bytes,
                line_count=document.metadata.line_count or 0,
                content_hash=document.content_hash,
            )
        )

    chunk_records: list[ChunkRecord] = []

    for chunk in chunks:
        document_id = document_id_by_file_path.get(chunk.file_path)

        if document_id is None:
            raise InvalidInputError(
                "Chunk does not match any loaded document.",
                details={"file_path": chunk.file_path},
            )

        chunk_records.append(
            ChunkRecord(
                id=uuid.uuid4(),
                chunk_uid=chunk.chunk_id,
                project_id=project_uuid,
                document_id=document_id,
                file_path=chunk.file_path,
                file_type=chunk.file_type,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                line_count=chunk.end_line - chunk.start_line + 1,
                character_count=len(chunk.content),
                estimated_tokens=_estimate_tokens(chunk.content),
                content_hash=chunk.content_hash,
                content=chunk.content,
            )
        )

    try:
        async with session.begin():
            project = await session.get(ProjectRecord, project_uuid)

            if project is None:
                raise ResourceNotFoundError(
                    "Project record was not found in the database.",
                    details={"project_id": project_id},
                )

            await session.execute(delete(ChunkRecord).where(ChunkRecord.project_id == project_uuid))
            await session.execute(
                delete(DocumentRecord).where(DocumentRecord.project_id == project_uuid)
            )

            session.add_all(document_records)
            session.add_all(chunk_records)

            project.documents_count = len(document_records)
            project.chunks_count = len(chunk_records)
            project.status = "chunked"

    except ResourceNotFoundError:
        raise

    except SQLAlchemyError as exc:
        raise DatabaseConnectionError(
            "Failed to persist documents and chunks.",
            details={"error_type": exc.__class__.__name__},
        ) from exc

    return PersistedChunksResponse(
        project_id=project_id,
        documents_persisted=len(document_records),
        chunks_persisted=len(chunk_records),
        chunk_size_lines=request.chunk_size_lines,
        overlap_lines=request.overlap_lines,
        message="Documents and chunks persisted successfully.",
    )
