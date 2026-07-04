import os
import shutil
import uuid
from pathlib import Path, PurePosixPath
from zipfile import BadZipFile, ZipFile

from fastapi import UploadFile

from backend.app.config import Settings
from backend.app.core.exceptions import InvalidInputError, UploadTooLargeError
from backend.app.schemas.upload_schema import ExtractedFileSummary, UploadCodebaseResponse

READ_CHUNK_SIZE = 1024 * 1024
ALLOWED_ARCHIVE_EXTENSIONS = {".zip"}
PREVIEW_FILE_LIMIT = 10


def _get_safe_archive_name(filename: str | None) -> str:
    if not filename:
        raise InvalidInputError("Uploaded file must have a filename.")

    safe_name = Path(filename).name
    extension = Path(safe_name).suffix.lower()

    if extension not in ALLOWED_ARCHIVE_EXTENSIONS:
        raise InvalidInputError(
            "Only .zip codebase uploads are supported.",
            details={"filename": filename, "allowed_extensions": list(ALLOWED_ARCHIVE_EXTENSIONS)},
        )

    return safe_name


def _to_relative_project_path(path: Path, settings: Settings) -> str:
    return str(path.relative_to(settings.project_root)).replace("\\", "/")


def _ensure_storage_directories(settings: Settings) -> None:
    settings.uploads_path.mkdir(parents=True, exist_ok=True)
    settings.projects_path.mkdir(parents=True, exist_ok=True)


async def _save_upload_file(
    file: UploadFile,
    destination_path: Path,
    max_size_bytes: int,
) -> int:
    total_size = 0

    try:
        with destination_path.open("wb") as output_file:
            while True:
                chunk = await file.read(READ_CHUNK_SIZE)

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > max_size_bytes:
                    raise UploadTooLargeError(
                        "Uploaded file is larger than the allowed limit.",
                        details={
                            "max_size_bytes": max_size_bytes,
                            "current_size_bytes": total_size,
                        },
                    )

                output_file.write(chunk)

        return total_size

    except Exception:
        destination_path.unlink(missing_ok=True)
        raise

    finally:
        await file.close()


def _is_safe_zip_member(member_name: str, extract_dir: Path) -> bool:
    normalized_name = member_name.replace("\\", "/")

    if "\x00" in normalized_name:
        return False

    if os.path.isabs(normalized_name):
        return False

    if os.path.splitdrive(normalized_name)[0]:
        return False

    posix_path = PurePosixPath(normalized_name)

    if any(part in {"..", ""} for part in posix_path.parts):
        return False

    target_path = (extract_dir / normalized_name).resolve()
    extract_root = extract_dir.resolve()

    return target_path == extract_root or str(target_path).startswith(str(extract_root) + os.sep)


def _build_files_preview(extract_dir: Path) -> list[ExtractedFileSummary]:
    preview: list[ExtractedFileSummary] = []

    for path in extract_dir.rglob("*"):
        if not path.is_file():
            continue

        relative_path = str(path.relative_to(extract_dir)).replace("\\", "/")

        preview.append(
            ExtractedFileSummary(
                file_path=relative_path,
                size_bytes=path.stat().st_size,
            )
        )

        if len(preview) >= PREVIEW_FILE_LIMIT:
            break

    return preview


def _extract_zip_safely(
    archive_path: Path,
    extract_dir: Path,
    settings: Settings,
) -> tuple[int, list[ExtractedFileSummary]]:
    extracted_files_count = 0
    total_uncompressed_size = 0

    try:
        with ZipFile(archive_path, "r") as zip_file:
            members = zip_file.infolist()

            if not members:
                raise InvalidInputError("Uploaded ZIP file is empty.")

            for member in members:
                if member.is_dir():
                    continue

                if not _is_safe_zip_member(member.filename, extract_dir):
                    raise InvalidInputError(
                        "ZIP file contains an unsafe file path.",
                        details={"unsafe_path": member.filename},
                    )

                extracted_files_count += 1
                total_uncompressed_size += member.file_size

                if extracted_files_count > settings.max_project_files:
                    raise InvalidInputError(
                        "ZIP file contains too many files.",
                        details={
                            "max_project_files": settings.max_project_files,
                            "current_files": extracted_files_count,
                        },
                    )

                if total_uncompressed_size > settings.max_extracted_size_bytes:
                    raise UploadTooLargeError(
                        "Extracted project is larger than the allowed limit.",
                        details={
                            "max_extracted_size_bytes": settings.max_extracted_size_bytes,
                            "current_extracted_size_bytes": total_uncompressed_size,
                        },
                    )

            zip_file.extractall(extract_dir)

    except BadZipFile as exc:
        raise InvalidInputError("Uploaded file is not a valid ZIP archive.") from exc

    if extracted_files_count == 0:
        raise InvalidInputError("ZIP file does not contain any files.")

    files_preview = _build_files_preview(extract_dir)

    return extracted_files_count, files_preview


async def ingest_codebase_upload(
    file: UploadFile,
    settings: Settings,
) -> UploadCodebaseResponse:
    _ensure_storage_directories(settings)

    project_id = str(uuid.uuid4())
    safe_archive_name = _get_safe_archive_name(file.filename)

    project_upload_dir = settings.uploads_path / project_id
    project_extract_dir = settings.projects_path / project_id

    project_upload_dir.mkdir(parents=True, exist_ok=False)
    project_extract_dir.mkdir(parents=True, exist_ok=False)

    archive_path = project_upload_dir / safe_archive_name

    try:
        upload_size_bytes = await _save_upload_file(
            file=file,
            destination_path=archive_path,
            max_size_bytes=settings.max_upload_size_bytes,
        )

        extracted_files_count, files_preview = _extract_zip_safely(
            archive_path=archive_path,
            extract_dir=project_extract_dir,
            settings=settings,
        )

        return UploadCodebaseResponse(
            project_id=project_id,
            original_filename=safe_archive_name,
            saved_archive_path=_to_relative_project_path(archive_path, settings),
            extracted_project_path=_to_relative_project_path(project_extract_dir, settings),
            upload_size_bytes=upload_size_bytes,
            extracted_files_count=extracted_files_count,
            files_preview=files_preview,
            message="Codebase uploaded and extracted successfully.",
        )

    except Exception:
        shutil.rmtree(project_upload_dir, ignore_errors=True)
        shutil.rmtree(project_extract_dir, ignore_errors=True)
        raise


def cleanup_project_storage(project_id: str, settings: Settings) -> None:
    shutil.rmtree(settings.uploads_path / project_id, ignore_errors=True)
    shutil.rmtree(settings.projects_path / project_id, ignore_errors=True)

