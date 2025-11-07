from __future__ import annotations

from typing import Any

from pymongo import MongoClient
from pymongo.database import Database

from spacenote.config import Config


class Service:
    """Base class for services with direct database access."""

    def __init__(self, database: Database[dict[str, Any]]) -> None:
        self.database = database
        self._core: Core | None = None

    def on_start(self) -> None:
        """Initialize service on application startup."""

    def on_stop(self) -> None:
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

    def __init__(self, database: Database[dict[str, Any]]) -> None:
        from spacenote.core.modules.space.service import SpaceService  # noqa: PLC0415
        from spacenote.core.modules.user.service import UserService  # noqa: PLC0415

        self.user = UserService(database)
        self.space = SpaceService(database)

    def set_core(self, core: Core) -> None:
        """Set core reference for all services."""
        self.user.set_core(core)
        self.space.set_core(core)

    def start_all(self) -> None:
        """Initialize all services."""
        self.user.on_start()
        self.space.on_start()

    def stop_all(self) -> None:
        """Cleanup all services."""
        self.user.on_stop()
        self.space.on_stop()


class Core:
    """Core application context with services and database."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.client: MongoClient[dict[str, Any]] = MongoClient(config.database_url)
        # Extract database name from URL
        db_name = config.database_url.split("/")[-1].split("?")[0]
        self.database: Database[dict[str, Any]] = self.client[db_name]
        self.services = Services(self.database)
        self.services.set_core(self)

    def start(self) -> None:
        """Initialize all services."""
        self.services.start_all()

    def stop(self) -> None:
        """Cleanup resources."""
        self.services.stop_all()
        self.client.close()
