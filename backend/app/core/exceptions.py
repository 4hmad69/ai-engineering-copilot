from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code: int = 500
    code: str = "app_error"

    def __init__(
        self,
        message: str = "Application error",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class InvalidInputError(AppError):
    status_code = 400
    code = "invalid_input"


class UploadTooLargeError(AppError):
    status_code = 413
    code = "upload_too_large"


class ResourceNotFoundError(AppError):
    status_code = 404
    code = "resource_not_found"


class DatabaseConnectionError(AppError):
    status_code = 503
    code = "database_unavailable"


class LLMProviderError(AppError):
    status_code = 502
    code = "llm_provider_error"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(
        request: Request,
        exc: AppError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )
