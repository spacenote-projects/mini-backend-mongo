from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from spacenote.config import Config
from spacenote.core.core import Core
from spacenote.core.modules.comment.models import CommentView
from spacenote.core.modules.note.models import NoteView
from spacenote.core.modules.space.models import SpaceField, SpaceView
from spacenote.core.modules.user.models import User, UserView
from spacenote.core.pagination import PaginationResult
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

    def _ensure_space_member(self, auth_token: str, space_slug: str) -> User:
        """Ensure user is authenticated and is a member of the space (or admin)."""
        user = self._get_authenticated_user(auth_token)

        # Admin can access all spaces
        if user.username == "admin":
            return user

        # Check if user is a member
        space = self._core.services.space.get_space(space_slug)
        if user.username not in space.members:
            raise AccessDeniedError(f"Access to space '{space_slug}' denied")

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

    async def add_field_to_space(self, auth_token: str, slug: str, field: SpaceField) -> SpaceView:
        """Add field to space (admin only)."""
        self._ensure_admin(auth_token)
        space = await self._core.services.space.add_field(slug, field)
        return SpaceView(**space.model_dump())

    async def remove_field_from_space(self, auth_token: str, slug: str, field_id: str) -> SpaceView:
        """Remove field from space (admin only). Field data in notes is preserved."""
        self._ensure_admin(auth_token)
        space = await self._core.services.space.remove_field(slug, field_id)
        return SpaceView(**space.model_dump())

    # Note management methods

    async def create_note(self, auth_token: str, space_slug: str, raw_fields: dict[str, str]) -> NoteView:
        """Create a new note (members only)."""
        user = self._ensure_space_member(auth_token, space_slug)
        note = await self._core.services.note.create_note(space_slug, user.username, raw_fields)
        return NoteView(**note.model_dump())

    async def get_note(self, auth_token: str, space_slug: str, number: int) -> NoteView:
        """Get single note by number (members only)."""
        self._ensure_space_member(auth_token, space_slug)
        note = await self._core.services.note.get_note(space_slug, number)
        return NoteView(**note.model_dump())

    async def list_notes(self, auth_token: str, space_slug: str, limit: int = 50, offset: int = 0) -> PaginationResult[NoteView]:
        """List notes with pagination (members only)."""
        self._ensure_space_member(auth_token, space_slug)
        result = await self._core.services.note.list_notes(space_slug, limit, offset)
        note_views = [NoteView(**note.model_dump()) for note in result.items]
        return PaginationResult(items=note_views, total=result.total, limit=result.limit, offset=result.offset)

    async def search_notes(
        self,
        auth_token: str,
        space_slug: str,
        filter_dict: dict[str, Any],
        sort_dict: dict[str, Any],
        limit: int = 50,
        offset: int = 0,
    ) -> PaginationResult[NoteView]:
        """Search notes with MongoDB query syntax (members only)."""
        self._ensure_space_member(auth_token, space_slug)
        result = await self._core.services.note.search_notes(space_slug, filter_dict, sort_dict, limit, offset)
        note_views = [NoteView(**note.model_dump()) for note in result.items]
        return PaginationResult(items=note_views, total=result.total, limit=result.limit, offset=result.offset)

    # Comment management methods

    async def create_comment(self, auth_token: str, space_slug: str, note_number: int, content: str) -> CommentView:
        """Create a new comment on a note (members only)."""
        user = self._ensure_space_member(auth_token, space_slug)
        comment = await self._core.services.comment.create_comment(space_slug, note_number, user.username, content)
        return CommentView(**comment.model_dump())

    async def list_comments(
        self,
        auth_token: str,
        space_slug: str,
        note_number: int,
        limit: int = 100,
        offset: int = 0,
    ) -> PaginationResult[CommentView]:
        """List comments with pagination (members only)."""
        self._ensure_space_member(auth_token, space_slug)
        result = await self._core.services.comment.list_comments(space_slug, note_number, limit, offset)
        comment_views = [CommentView(**comment.model_dump()) for comment in result.items]
        return PaginationResult(items=comment_views, total=result.total, limit=result.limit, offset=result.offset)
