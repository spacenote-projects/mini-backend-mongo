from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from spacenote.core.modules.user.models import UserView
from spacenote.web.deps import AppDep, AuthTokenDep

router = APIRouter(tags=["users"])


class CreateUserRequest(BaseModel):
    """Request model for creating a new user."""

    username: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Unique username for the user",
        examples=["alice"],
    )
    token: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Authentication token for the user",
        examples=["alice_secret_token"],
    )


class ErrorResponse(BaseModel):
    """Standard error response format."""

    message: str = Field(..., description="Human-readable error message")
    type: str = Field(..., description="Machine-readable error type")


@router.get(
    "/users/me",
    summary="Get current user",
    description="Returns information about the currently authenticated user.",
    operation_id="getCurrentUser",
    responses={
        200: {"description": "User information retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def get_current_user(
    app: AppDep,
    auth_token: AuthTokenDep,
) -> UserView:
    """Get current authenticated user."""
    return await app.get_current_user(auth_token)


@router.get(
    "/users",
    summary="List all users",
    description="Returns a list of all users in the system. Requires admin privileges.",
    operation_id="getAllUsers",
    responses={
        200: {"description": "User list retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Admin privileges required"},
    },
)
async def get_all_users(
    app: AppDep,
    auth_token: AuthTokenDep,
) -> list[UserView]:
    """Get all users (admin only)."""
    return await app.get_all_users(auth_token)


@router.post(
    "/users",
    summary="Create new user",
    description="Creates a new user with the specified username and token. Requires admin privileges.",
    operation_id="createUser",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "User created successfully"},
        400: {"model": ErrorResponse, "description": "Validation error (e.g., username already exists)"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Admin privileges required"},
    },
)
async def create_user(
    create_data: CreateUserRequest,
    app: AppDep,
    auth_token: AuthTokenDep,
) -> UserView:
    """Create a new user (admin only)."""
    return await app.create_user(auth_token, create_data.username, create_data.token)


@router.delete(
    "/users/{username}",
    summary="Delete user",
    description="Deletes the specified user. Admin cannot delete themselves. Requires admin privileges.",
    operation_id="deleteUser",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "User deleted successfully"},
        400: {"model": ErrorResponse, "description": "Validation error (e.g., cannot delete yourself)"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Admin privileges required"},
        404: {"model": ErrorResponse, "description": "User not found"},
    },
)
async def delete_user(
    username: str,
    app: AppDep,
    auth_token: AuthTokenDep,
) -> None:
    """Delete a user (admin only)."""
    await app.delete_user(auth_token, username)
