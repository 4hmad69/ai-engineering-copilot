import mimetypes
from pathlib import Path

from backend.app.config import Settings
from backend.app.core.exceptions import ResourceNotFoundError
from backend.app.schemas.project_schema import ProjectFileMetadata, ProjectFilesResponse

SUPPORTED_FILE_TYPES: dict[str, str] = {
    ".py": "python",
    ".md": "markdown",
    ".txt": "text",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".ini": "config",
    ".env.example": "environment_example",
    ".gitignore": "gitignore",
    ".dockerignore": "dockerignore",
    "Dockerfile": "dockerfile",
}

EXCLUDED_DIR_NAMES: set[str] = {
    ".git",
    ".github",
    ".idea",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".turbo",
    "coverage",
    "htmlcov",
}

EXCLUDED_FILE_NAMES: set[str] = {
    ".DS_Store",
    "Thumbs.db",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "Pipfile.lock",
}

BINARY_EXTENSIONS: set[str] = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".7z",
    ".rar",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".pyc",
    ".pyo",
    ".sqlite",
    ".db",
    ".mp3",
    ".mp4",
    ".mov",
    ".avi",
    ".woff",
    ".woff2",
    ".ttf",
}


def get_project_path(project_id: str, settings: Settings) -> Path:
    project_path = settings.projects_path / project_id

    if not project_path.exists() or not project_path.is_dir():
        raise ResourceNotFoundError(
            "Project was not found.",
            details={"project_id": project_id},
        )

    return project_path


def to_relative_project_path(path: Path, settings: Settings) -> str:
    return str(path.relative_to(settings.project_root)).replace("\\", "/")


def to_relative_file_path(path: Path, project_path: Path) -> str:
    return str(path.relative_to(project_path)).replace("\\", "/")


def _is_inside_excluded_directory(path: Path, project_path: Path) -> bool:
    relative_parts = path.relative_to(project_path).parts
    return any(part in EXCLUDED_DIR_NAMES for part in relative_parts)


def _detect_file_type(path: Path) -> tuple[str | None, str]:
    file_name = path.name
    extension = path.suffix.lower()

    if file_name in SUPPORTED_FILE_TYPES:
        return SUPPORTED_FILE_TYPES[file_name], extension

    if extension in SUPPORTED_FILE_TYPES:
        return SUPPORTED_FILE_TYPES[extension], extension

    if extension in BINARY_EXTENSIONS:
        return None, extension

    guessed_type, _ = mimetypes.guess_type(path.name)

    if guessed_type and not guessed_type.startswith("text"):
        return None, extension

    return None, extension


def _looks_like_binary_file(path: Path, sample_size: int = 2048) -> bool:
    try:
        with path.open("rb") as file:
            sample = file.read(sample_size)
    except OSError:
        return True

    return b"\x00" in sample


def _count_lines(path: Path) -> int | None:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as file:
            return sum(1 for _ in file)
    except OSError:
        return None


def _create_skipped_file_metadata(
    path: Path,
    project_path: Path,
    project_id: str,
    skip_reason: str,
    file_type: str = "unknown",
) -> ProjectFileMetadata:
    return ProjectFileMetadata(
        project_id=project_id,
        file_path=to_relative_file_path(path, project_path),
        file_type=file_type,
        extension=path.suffix.lower(),
        size_bytes=path.stat().st_size,
        line_count=None,
        is_loadable=False,
        skip_reason=skip_reason,
    )


def _inspect_file(
    path: Path,
    project_path: Path,
    project_id: str,
    settings: Settings,
) -> ProjectFileMetadata:
    size_bytes = path.stat().st_size

    if path.name in EXCLUDED_FILE_NAMES:
        return _create_skipped_file_metadata(
            path=path,
            project_path=project_path,
            project_id=project_id,
            skip_reason="excluded_file_name",
        )

    if size_bytes > settings.max_single_file_size_bytes:
        return _create_skipped_file_metadata(
            path=path,
            project_path=project_path,
            project_id=project_id,
            skip_reason="file_too_large",
        )

    file_type, detected_extension = _detect_file_type(path)

    if file_type is None:
        return ProjectFileMetadata(
            project_id=project_id,
            file_path=to_relative_file_path(path, project_path),
            file_type="unknown",
            extension=detected_extension,
            size_bytes=size_bytes,
            line_count=None,
            is_loadable=False,
            skip_reason="unsupported_file_type",
        )

    if _looks_like_binary_file(path):
        return ProjectFileMetadata(
            project_id=project_id,
            file_path=to_relative_file_path(path, project_path),
            file_type=file_type,
            extension=detected_extension,
            size_bytes=size_bytes,
            line_count=None,
            is_loadable=False,
            skip_reason="binary_file",
        )

    line_count = _count_lines(path)

    return ProjectFileMetadata(
        project_id=project_id,
        file_path=to_relative_file_path(path, project_path),
        file_type=file_type,
        extension=detected_extension,
        size_bytes=size_bytes,
        line_count=line_count,
        is_loadable=True,
        skip_reason=None,
    )


def discover_project_files(
    project_id: str,
    settings: Settings,
) -> tuple[Path, list[ProjectFileMetadata]]:
    project_path = get_project_path(project_id, settings)

    files: list[ProjectFileMetadata] = []

    for path in project_path.rglob("*"):
        if not path.is_file():
            continue

        if _is_inside_excluded_directory(path, project_path):
            files.append(
                _create_skipped_file_metadata(
                    path=path,
                    project_path=project_path,
                    project_id=project_id,
                    skip_reason="excluded_directory",
                )
            )
            continue

        files.append(
            _inspect_file(
                path=path,
                project_path=project_path,
                project_id=project_id,
                settings=settings,
            )
        )

    return project_path, files


def list_project_files(
    project_id: str,
    settings: Settings,
) -> ProjectFilesResponse:
    project_path, all_files = discover_project_files(
        project_id=project_id,
        settings=settings,
    )

    loadable_files = [file for file in all_files if file.is_loadable]
    skipped_files = [file for file in all_files if not file.is_loadable]
    files_preview = all_files[: settings.file_preview_limit]

    return ProjectFilesResponse(
        project_id=project_id,
        project_path=to_relative_project_path(project_path, settings),
        total_files_seen=len(all_files),
        loadable_files_count=len(loadable_files),
        skipped_files_count=len(skipped_files),
        files=files_preview,
    )
