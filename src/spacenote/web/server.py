from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from spacenote.app import App
from spacenote.config import Config
from spacenote.errors import UserError
from spacenote.web.error_handlers import general_exception_handler, user_error_handler
from spacenote.web.openapi import customize_openapi
from spacenote.web.routers import notes, spaces, users


def create_fastapi_app(app_instance: App, config: Config) -> FastAPI:
    """Create and configure FastAPI application."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:  # noqa: ARG001
        """Manage application lifecycle (startup and shutdown)."""
        async with app_instance.lifespan():
            yield

    fastapi_app = FastAPI(
        title="SpaceNote Mini API",
        description="Minimal version of SpaceNote backend for MongoDB/PostgreSQL comparison",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Store app instance in state for dependency injection
    fastapi_app.state.app = app_instance
    fastapi_app.state.config = config

    # Register routers with /api/v1 prefix
    fastapi_app.include_router(users.router, prefix="/api/v1")
    fastapi_app.include_router(spaces.router, prefix="/api/v1")
    fastapi_app.include_router(notes.router, prefix="/api/v1")

    # Register error handlers
    fastapi_app.add_exception_handler(UserError, user_error_handler)  # type: ignore[arg-type]
    fastapi_app.add_exception_handler(Exception, general_exception_handler)

    # Customize OpenAPI schema
    customize_openapi(fastapi_app)

    return fastapi_app
