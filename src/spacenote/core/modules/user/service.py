from types import MappingProxyType
from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from spacenote.core.core import Service
from spacenote.core.modules.user.models import User
from spacenote.errors import AuthenticationError, NotFoundError, ValidationError


class UserService(Service):
    """Manages users with in-memory cache indexed by natural key (username)."""

    def __init__(self, database: AsyncDatabase[dict[str, Any]]) -> None:
        super().__init__(database)
        self._collection = database.get_collection("users")
        # Cache by natural key (username) instead of ObjectId
        self._users: dict[str, User] = {}
        # Additional index for fast token lookup
        self._users_by_token: dict[str, User] = {}

    def get_user(self, username: str) -> User:
        """Get user by username (natural key) from cache."""
        if username not in self._users:
            raise NotFoundError(f"User '{username}' not found")
        return self._users[username]

    def get_user_by_token(self, token: str) -> User:
        """Get user by authentication token from cache."""
        if token not in self._users_by_token:
            raise AuthenticationError("Invalid token")
        return self._users_by_token[token]

    def has_username(self, username: str) -> bool:
        """Check if username exists in cache."""
        return username in self._users

    def get_all_users(self) -> list[User]:
        """Get all users from cache."""
        return list(self._users.values())

    def get_user_cache(self) -> MappingProxyType[str, User]:
        """Get read-only view of user cache."""
        return MappingProxyType(self._users)

    async def create_user(self, username: str, token: str) -> User:
        """Create user with explicitly provided token."""
        if self.has_username(username):
            raise ValidationError(f"User '{username}' already exists")

        user = User(username=username, token=token)
        await self._collection.insert_one(user.to_mongo())

        # Update both caches
        self._users[username] = user
        self._users_by_token[token] = user

        return user

    async def delete_user(self, username: str) -> None:
        """Delete a user from the system."""
        if not self.has_username(username):
            raise NotFoundError(f"User '{username}' not found")

        user = self._users[username]

        # Delete from database
        await self._collection.delete_one({"username": username})

        # Remove from caches
        del self._users[username]
        if user.token in self._users_by_token:
            del self._users_by_token[user.token]

    async def ensure_admin_user_exists(self) -> None:
        """Create default admin user if not exists."""
        if not self.has_username("admin"):
            await self.create_user("admin", "admin")

    async def update_all_users_cache(self) -> None:
        """Reload all users cache from database."""
        users = await User.list_cursor(self._collection.find())
        self._users = {user.username: user for user in users}
        self._users_by_token = {user.token: user for user in users}

    async def on_start(self) -> None:
        """Initialize indexes, cache, and admin user."""
        # Create unique indexes on natural and authentication keys
        await self._collection.create_index([("username", 1)], unique=True)
        await self._collection.create_index([("token", 1)], unique=True)

        # Load all users into cache
        await self.update_all_users_cache()

        # Ensure admin user exists for testing
        await self.ensure_admin_user_exists()
