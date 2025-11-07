from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from spacenote.config import Config
from spacenote.core.core import Core
from spacenote.core.modules.space.models import SpaceView
from spacenote.core.modules.user.models import User, UserView
from spacenote.errors import AccessDeniedError, AuthenticationError, ValidationError


class App:
    """Application facade that provides permission-validated access to core services.

    All methods validate authentication/authorization before delegating to services.
    Never exposes Core or Services directly to web layer.
    """

    def __init__(self, config: Config) -> None:
        self._core = Core(config)

    @asynccontextmanager
    async def lifespan(self) -> AsyncGenerator[None]:
        """Manage application lifecycle - startup and shutdown."""
        await self._core.on_start()
        try:
            yield
        finally:
            await self._core.on_stop()

    # Authentication helpers

    def is_auth_token_valid(self, auth_token: str) -> bool:
        """Check if authentication token is valid."""
        try:
            self._core.services.user.get_user_by_token(auth_token)
        except AuthenticationError:
            return False
        else:
            return True

    def _get_authenticated_user(self, auth_token: str) -> User:
        """Get authenticated user or raise AuthenticationError."""
        return self._core.services.user.get_user_by_token(auth_token)

    def _ensure_admin(self, auth_token: str) -> User:
        """Ensure user is authenticated and is admin."""
        user = self._get_authenticated_user(auth_token)
        if user.username != "admin":
            raise AccessDeniedError("Admin privileges required")
        return user

    def _resolve_user(self, username: str) -> User:
        """Resolve username to User or raise NotFoundError."""
        return self._core.services.user.get_user(username)

    # User management methods

    async def get_current_user(self, auth_token: str) -> UserView:
        """Get current authenticated user."""
        user = self._get_authenticated_user(auth_token)
        return UserView(username=user.username)

    async def get_all_users(self, auth_token: str) -> list[UserView]:
        """Get all users (admin only)."""
        self._ensure_admin(auth_token)
        users = self._core.services.user.get_all_users()
        return [UserView(username=user.username) for user in users]

    async def create_user(self, auth_token: str, username: str, token: str) -> UserView:
        """Create a new user (admin only)."""
        self._ensure_admin(auth_token)
        user = await self._core.services.user.create_user(username, token)
        return UserView(username=user.username)

    async def delete_user(self, auth_token: str, username: str) -> None:
        """Delete a user (admin only)."""
        current_user = self._ensure_admin(auth_token)

        # Prevent admin from deleting themselves
        if username == current_user.username:
            raise ValidationError("Cannot delete yourself")

        # Ensure user exists
        self._resolve_user(username)

        # Delete the user
        await self._core.services.user.delete_user(username)

    # Space management methods

    async def get_spaces(self, auth_token: str) -> list[SpaceView]:
        """Get all spaces accessible to current user.

        Admin sees all spaces, regular users see only spaces where they are members.
        """
        user = self._get_authenticated_user(auth_token)
        spaces = self._core.services.space.get_all_spaces()

        # Admin sees all, regular users see only their spaces
        visible_spaces = spaces if user.username == "admin" else [s for s in spaces if user.username in s.members]

        return [SpaceView(**s.model_dump()) for s in visible_spaces]

    async def create_space(self, auth_token: str, slug: str, title: str) -> SpaceView:
        """Create a new space (admin only)."""
        self._ensure_admin(auth_token)
        space = await self._core.services.space.create_space(slug, title)
        return SpaceView(**space.model_dump())

    async def add_space_member(self, auth_token: str, slug: str, username: str) -> SpaceView:
        """Add member to space (admin only)."""
        self._ensure_admin(auth_token)
        space = await self._core.services.space.add_member(slug, username)
        return SpaceView(**space.model_dump())
