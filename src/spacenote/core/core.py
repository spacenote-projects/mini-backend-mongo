from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any
from urllib.parse import urlparse

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from spacenote.config import Config


class Service:
    """Base class for services with direct database access."""

    def __init__(self, database: AsyncDatabase[dict[str, Any]]) -> None:
        self.database = database
        self._core: Core | None = None

    async def on_start(self) -> None:
        """Initialize service on application startup."""

    async def on_stop(self) -> None:
        """Cleanup service on application shutdown."""

    @property
    def core(self) -> Core:
        """Get the core application context."""
        if self._core is None:
            raise RuntimeError("Core not set for service")
        return self._core

    def set_core(self, core: Core) -> None:
        """Set the core application context."""
        self._core = core


class Services:
    """Service registry for all application services."""

    def __init__(self, database: AsyncDatabase[dict[str, Any]]) -> None:
        from spacenote.core.modules.space.service import SpaceService  # noqa: PLC0415
        from spacenote.core.modules.user.service import UserService  # noqa: PLC0415

        self.user = UserService(database)
        self.space = SpaceService(database)

    def set_core(self, core: Core) -> None:
        """Set core reference for all services."""
        self.user.set_core(core)
        self.space.set_core(core)

    async def start_all(self) -> None:
        """Initialize all services."""
        await self.user.on_start()
        await self.space.on_start()

    async def stop_all(self) -> None:
        """Cleanup all services."""
        await self.user.on_stop()
        await self.space.on_stop()


class Core:
    """Core application context with services and database."""

    def __init__(self, config: Config) -> None:
        self.config = config
        # Create async client synchronously (no await needed)
        self.mongo_client: AsyncMongoClient[dict[str, Any]] = AsyncMongoClient(
            config.database_url,
            uuidRepresentation="standard",
            tz_aware=True,
        )
        # Extract database name from URL and get database
        db_name = urlparse(config.database_url).path[1:]
        self.database: AsyncDatabase[dict[str, Any]] = self.mongo_client.get_database(db_name)
        self.services = Services(self.database)
        self.services.set_core(self)

    @asynccontextmanager
    async def lifespan(self) -> AsyncGenerator[None]:
        """Manage application lifecycle - startup and shutdown."""
        await self.on_start()
        try:
            yield
        finally:
            await self.on_stop()

    async def on_start(self) -> None:
        """Start all services on application startup."""
        await self.services.start_all()

    async def on_stop(self) -> None:
        """Stop services and close MongoDB connection on shutdown."""
        await self.services.stop_all()
        await self.mongo_client.aclose()
