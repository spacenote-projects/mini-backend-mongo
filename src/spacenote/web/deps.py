from typing import Annotated

from fastapi import Depends, Header, Request

from spacenote.app import App
from spacenote.errors import AuthenticationError


def get_app(request: Request) -> App:
    """Get App instance from FastAPI app state."""
    return request.app.state.app  # type: ignore[no-any-return]


def get_auth_token(authorization: str | None = Header(None)) -> str:
    """Extract and validate authentication token from Authorization header.

    Expects: Authorization: Bearer <token>
    """
    if not authorization:
        raise AuthenticationError("Missing Authorization header")

    if not authorization.startswith("Bearer "):
        raise AuthenticationError("Invalid Authorization header format. Expected 'Bearer <token>'")

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise AuthenticationError("Empty token")

    return token


# Type aliases for dependency injection
AppDep = Annotated[App, Depends(get_app)]
AuthTokenDep = Annotated[str, Depends(get_auth_token)]
