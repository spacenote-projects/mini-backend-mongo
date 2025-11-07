from fastapi import Request, status
from fastapi.responses import JSONResponse

from spacenote.errors import (
    AccessDeniedError,
    AuthenticationError,
    NotFoundError,
    UserError,
    ValidationError,
)


def user_error_handler(request: Request, exc: UserError) -> JSONResponse:  # noqa: ARG001
    """Handle user-facing errors and convert to appropriate HTTP responses."""
    status_code = status.HTTP_400_BAD_REQUEST
    error_type = "validation_error"

    if isinstance(exc, NotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
        error_type = "not_found"
    elif isinstance(exc, AuthenticationError):
        status_code = status.HTTP_401_UNAUTHORIZED
        error_type = "authentication_error"
    elif isinstance(exc, AccessDeniedError):
        status_code = status.HTTP_403_FORBIDDEN
        error_type = "access_denied"
    elif isinstance(exc, ValidationError):
        status_code = status.HTTP_400_BAD_REQUEST
        error_type = "validation_error"

    return JSONResponse(
        status_code=status_code,
        content={
            "message": str(exc),
            "type": error_type,
        },
    )


def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:  # noqa: ARG001
    """Handle unexpected exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "Internal server error",
            "type": "internal_error",
        },
    )
