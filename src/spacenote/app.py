from spacenote.config import Config
from spacenote.core.core import Core
from spacenote.core.modules.user.models import User, UserView
from spacenote.errors import AccessDeniedError, AuthenticationError, ValidationError


class App:
    """Application facade that provides permission-validated access to core services.

    All methods validate authentication/authorization before delegating to services.
    Never exposes Core or Services directly to web layer.
    """

    def __init__(self, config: Config) -> None:
        self._core = Core(config)

    def start(self) -> None:
        """Initialize all services."""
        self._core.start()

    def stop(self) -> None:
        """Cleanup resources."""
        self._core.stop()

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

    def get_current_user(self, auth_token: str) -> UserView:
        """Get current authenticated user."""
        user = self._get_authenticated_user(auth_token)
        return UserView(username=user.username)

    def get_all_users(self, auth_token: str) -> list[UserView]:
        """Get all users (admin only)."""
        self._ensure_admin(auth_token)
        users = self._core.services.user.get_all_users()
        return [UserView(username=user.username) for user in users]

    def create_user(self, auth_token: str, username: str, token: str) -> UserView:
        """Create a new user (admin only)."""
        self._ensure_admin(auth_token)
        user = self._core.services.user.create_user(username, token)
        return UserView(username=user.username)

    def delete_user(self, auth_token: str, username: str) -> None:
        """Delete a user (admin only)."""
        current_user = self._ensure_admin(auth_token)

        # Prevent admin from deleting themselves
        if username == current_user.username:
            raise ValidationError("Cannot delete yourself")

        # Ensure user exists
        self._resolve_user(username)

        # Delete the user
        self._core.services.user.delete_user(username)
