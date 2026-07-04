import hashlib
from dataclasses import dataclass
from pathlib import Path

from backend.app.config import Settings
from backend.app.schemas.document_schema import (
    ChunkPreviewResponse,
    ChunkingRequest,
    DocumentChunkPreview,
    LoadedDocumentMetadata,
    LoadedDocumentsResponse,
)
from backend.app.schemas.project_schema import ProjectFileMetadata
from backend.app.services.project_loader_service import (
    discover_project_files,
    get_project_path,
    to_relative_project_path,
)

CONTENT_PREVIEW_CHARACTER_LIMIT = 700
AVERAGE_CHARS_PER_TOKEN = 4


@dataclass(frozen=True)
class LoadedDocument:
    metadata: ProjectFileMetadata
    absolute_path: Path
    content: str
    content_hash: str


@dataclass(frozen=True)
class PreparedChunk:
    chunk_id: str
    project_id: str
    file_path: str
    file_type: str
    start_line: int
    end_line: int
    content: str
    content_hash: str


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_text(content: str) -> str:
    return content.replace("\r\n", "\n").replace("\r", "\n")


def _read_text_file(path: Path) -> str:
    return _normalize_text(
        path.read_text(
            encoding="utf-8",
            errors="replace",
        )
    )


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // AVERAGE_CHARS_PER_TOKEN)


def _preview_text(text: str) -> str:
    cleaned_text = text.strip()

    if len(cleaned_text) <= CONTENT_PREVIEW_CHARACTER_LIMIT:
        return cleaned_text

    return cleaned_text[:CONTENT_PREVIEW_CHARACTER_LIMIT].rstrip() + "..."


def _metadata_to_loaded_document_response(
    document: LoadedDocument,
) -> LoadedDocumentMetadata:
    return LoadedDocumentMetadata(
        project_id=document.metadata.project_id,
        file_path=document.metadata.file_path,
        file_type=document.metadata.file_type,
        extension=document.metadata.extension,
        size_bytes=document.metadata.size_bytes,
        line_count=document.metadata.line_count or 0,
        content_hash=document.content_hash,
    )


def _load_single_document(
    project_path: Path,
    file_metadata: ProjectFileMetadata,
) -> LoadedDocument:
    absolute_path = project_path / file_metadata.file_path
    content = _read_text_file(absolute_path)

    return LoadedDocument(
        metadata=file_metadata,
        absolute_path=absolute_path,
        content=content,
        content_hash=_hash_text(content),
    )


def load_project_documents(
    project_id: str,
    settings: Settings,
) -> tuple[Path, list[LoadedDocument]]:
    project_path, discovered_files = discover_project_files(
        project_id=project_id,
        settings=settings,
    )

    loadable_files = [file for file in discovered_files if file.is_loadable]
    documents: list[LoadedDocument] = []

    for file_metadata in loadable_files:
        documents.append(
            _load_single_document(
                project_path=project_path,
                file_metadata=file_metadata,
            )
        )

    return project_path, documents


def get_loaded_documents_summary(
    project_id: str,
    settings: Settings,
) -> LoadedDocumentsResponse:
    project_path, documents = load_project_documents(
        project_id=project_id,
        settings=settings,
    )

    document_metadata = [
        _metadata_to_loaded_document_response(document)
        for document in documents
    ]

    return LoadedDocumentsResponse(
        project_id=project_id,
        project_path=to_relative_project_path(project_path, settings),
        documents_count=len(documents),
        total_lines=sum(document.metadata.line_count or 0 for document in documents),
        total_size_bytes=sum(document.metadata.size_bytes for document in documents),
        documents=document_metadata,
    )


def _create_chunk_id(
    project_id: str,
    file_path: str,
    start_line: int,
    end_line: int,
    content_hash: str,
) -> str:
    raw_id = f"{project_id}:{file_path}:{start_line}:{end_line}:{content_hash}"
    return hashlib.sha256(raw_id.encode("utf-8")).hexdigest()[:24]


def _split_document_into_chunks(
    document: LoadedDocument,
    chunk_size_lines: int,
    overlap_lines: int,
) -> list[PreparedChunk]:
    lines = document.content.splitlines()

    if not lines:
        return []

    chunks: list[PreparedChunk] = []
    start_index = 0

    while start_index < len(lines):
        end_index = min(start_index + chunk_size_lines, len(lines))

        chunk_lines = lines[start_index:end_index]
        chunk_content = "\n".join(chunk_lines).strip()

        if chunk_content:
            start_line = start_index + 1
            end_line = end_index
            chunk_hash = _hash_text(chunk_content)

            chunks.append(
                PreparedChunk(
                    chunk_id=_create_chunk_id(
                        project_id=document.metadata.project_id,
                        file_path=document.metadata.file_path,
                        start_line=start_line,
                        end_line=end_line,
                        content_hash=chunk_hash,
                    ),
                    project_id=document.metadata.project_id,
                    file_path=document.metadata.file_path,
                    file_type=document.metadata.file_type,
                    start_line=start_line,
                    end_line=end_line,
                    content=chunk_content,
                    content_hash=chunk_hash,
                )
            )

        if end_index >= len(lines):
            break

        next_start_index = end_index - overlap_lines

        if next_start_index <= start_index:
            next_start_index = end_index

        start_index = next_start_index

    return chunks


def split_loaded_documents_into_chunks(
    documents: list[LoadedDocument],
    request: ChunkingRequest,
) -> list[PreparedChunk]:
    chunks: list[PreparedChunk] = []

    for document in documents:
        chunks.extend(
            _split_document_into_chunks(
                document=document,
                chunk_size_lines=request.chunk_size_lines,
                overlap_lines=request.overlap_lines,
            )
        )

    return chunks

def prepare_project_chunks(
    project_id: str,
    request: ChunkingRequest,
    settings: Settings,
) -> tuple[Path, list[PreparedChunk], int]:
    project_path = get_project_path(project_id, settings)

    _, documents = load_project_documents(
        project_id=project_id,
        settings=settings,
    )

    chunks = split_loaded_documents_into_chunks(
        documents=documents,
        request=request,
    )

    return project_path, chunks, len(documents)


def get_project_chunk_preview(
    project_id: str,
    request: ChunkingRequest,
    settings: Settings,
) -> ChunkPreviewResponse:
    project_path, chunks, source_documents_count = prepare_project_chunks(
        project_id=project_id,
        request=request,
        settings=settings,
    )

    chunks_preview = chunks[: settings.chunk_preview_limit]

    return ChunkPreviewResponse(
        project_id=project_id,
        project_path=to_relative_project_path(project_path, settings),
        chunk_size_lines=request.chunk_size_lines,
        overlap_lines=request.overlap_lines,
        source_documents_count=source_documents_count,
        chunks_count=len(chunks),
        chunks_preview_count=len(chunks_preview),
        chunks=[
            DocumentChunkPreview(
                chunk_id=chunk.chunk_id,
                project_id=chunk.project_id,
                file_path=chunk.file_path,
                file_type=chunk.file_type,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                line_count=chunk.end_line - chunk.start_line + 1,
                character_count=len(chunk.content),
                estimated_tokens=_estimate_tokens(chunk.content),
                content_hash=chunk.content_hash,
                content_preview=_preview_text(chunk.content),
            )
            for chunk in chunks_preview
        ],
    )

