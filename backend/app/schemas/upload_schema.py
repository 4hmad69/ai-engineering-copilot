from pydantic import BaseModel, Field


class ExtractedFileSummary(BaseModel):
    file_path: str = Field(..., description="Relative path of the extracted file")
    size_bytes: int = Field(..., description="File size in bytes")


class UploadCodebaseResponse(BaseModel):
    project_id: str = Field(..., description="Unique ID assigned to this uploaded project")
    original_filename: str = Field(..., description="Original uploaded archive filename")
    saved_archive_path: str = Field(
        ..., description="Relative path where the ZIP archive was saved"
    )
    extracted_project_path: str = Field(
        ..., description="Relative path where the project was extracted"
    )
    upload_size_bytes: int = Field(..., description="Size of uploaded ZIP archive in bytes")
    extracted_files_count: int = Field(..., description="Number of files extracted from the ZIP")
    files_preview: list[ExtractedFileSummary] = Field(
        default_factory=list,
        description="Small preview of extracted files",
    )
    message: str
