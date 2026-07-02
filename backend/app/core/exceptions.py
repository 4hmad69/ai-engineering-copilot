class AppError(Exception):
    """Base exception for application-specific errors."""


class ResourceNotFoundError(AppError):
    """Raised when a requested resource does not exist."""


class InvalidInputError(AppError):
    """Raised when user input is invalid."""