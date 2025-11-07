from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from spacenote.core.core import Service
from spacenote.core.modules.space.models import Space
from spacenote.errors import NotFoundError, ValidationError


class SpaceService(Service):
    """Manages spaces with in-memory cache indexed by natural key (slug)."""

    def __init__(self, database: AsyncDatabase[dict[str, Any]]) -> None:
        super().__init__(database)
        self._collection = database.get_collection("spaces")
        # Cache by natural key (slug) instead of ObjectId
        self._spaces: dict[str, Space] = {}

    def get_space(self, slug: str) -> Space:
        """Get space by slug (natural key) from cache."""
        if slug not in self._spaces:
            raise NotFoundError(f"Space '{slug}' not found")
        return self._spaces[slug]

    def has_slug(self, slug: str) -> bool:
        """Check if slug exists in cache."""
        return slug in self._spaces

    def get_all_spaces(self) -> list[Space]:
        """Get all spaces from cache."""
        return list(self._spaces.values())

    async def create_space(self, slug: str, title: str) -> Space:
        """Create space with empty members list."""
        if self.has_slug(slug):
            raise ValidationError(f"Space '{slug}' already exists")

        space = Space(slug=slug, title=title, members=[])
        await self._collection.insert_one(space.to_mongo())

        # Update cache
        self._spaces[slug] = space

        return space

    async def add_member(self, slug: str, username: str) -> Space:
        """Add member to space with username validation via UserService."""
        if not self.has_slug(slug):
            raise NotFoundError(f"Space '{slug}' not found")

        # Validate that user exists
        if self._core is None:
            raise RuntimeError("SpaceService not properly initialized with Core")
        self._core.services.user.get_user(username)  # Raises NotFoundError if user doesn't exist

        space = self._spaces[slug]

        # Check if already a member
        if username in space.members:
            raise ValidationError(f"User '{username}' is already a member of space '{slug}'")

        # Add member to list
        space.members.append(username)

        # Update database
        await self._collection.update_one({"slug": slug}, {"$set": {"members": space.members}})

        return space

    async def update_all_spaces_cache(self) -> None:
        """Reload all spaces cache from database."""
        spaces = await Space.list_cursor(self._collection.find())
        self._spaces = {space.slug: space for space in spaces}

    async def on_start(self) -> None:
        """Initialize indexes and cache."""
        # Create unique index on natural key
        await self._collection.create_index([("slug", 1)], unique=True)

        # Load all spaces into cache
        await self.update_all_spaces_cache()
