from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import (
    DatabaseConnectionError,
    InvalidInputError,
    ResourceNotFoundError,
)
from backend.app.models.project import ProjectRecord
from backend.app.schemas.persistence_schema import ProjectRecordResponse
from backend.app.schemas.upload_schema import UploadCodebaseResponse


def _parse_project_uuid(project_id: str) -> UUID:
    try:
        return UUID(project_id)
    except ValueError as exc:
        raise InvalidInputError(
            "Invalid project_id format.",
            details={"project_id": project_id},
        ) from exc


def _project_record_to_response(project: ProjectRecord) -> ProjectRecordResponse:
    return ProjectRecordResponse(
        project_id=str(project.id),
        original_filename=project.original_filename,
        saved_archive_path=project.saved_archive_path,
        extracted_project_path=project.extracted_project_path,
        upload_size_bytes=project.upload_size_bytes,
        extracted_files_count=project.extracted_files_count,
        documents_count=project.documents_count,
        chunks_count=project.chunks_count,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


async def create_project_record_from_upload(
    upload_response: UploadCodebaseResponse,
    session: AsyncSession,
) -> ProjectRecordResponse:
    project_uuid = _parse_project_uuid(upload_response.project_id)

    project = ProjectRecord(
        id=project_uuid,
        original_filename=upload_response.original_filename,
        saved_archive_path=upload_response.saved_archive_path,
        extracted_project_path=upload_response.extracted_project_path,
        upload_size_bytes=upload_response.upload_size_bytes,
        extracted_files_count=upload_response.extracted_files_count,
        documents_count=0,
        chunks_count=0,
        status="uploaded",
    )

    try:
        session.add(project)
        await session.commit()
        await session.refresh(project)

        return _project_record_to_response(project)

    except SQLAlchemyError as exc:
        await session.rollback()

        raise DatabaseConnectionError(
            "Failed to save project metadata to the database.",
            details={"error_type": exc.__class__.__name__},
        ) from exc


async def get_project_record_by_id(
    project_id: str,
    session: AsyncSession,
) -> ProjectRecordResponse:
    project_uuid = _parse_project_uuid(project_id)

    try:
        project = await session.get(ProjectRecord, project_uuid)

    except SQLAlchemyError as exc:
        raise DatabaseConnectionError(
            "Failed to fetch project metadata from the database.",
            details={"error_type": exc.__class__.__name__},
        ) from exc

    if project is None:
        raise ResourceNotFoundError(
            "Project record was not found in the database.",
            details={"project_id": project_id},
        )

    return _project_record_to_response(project)
