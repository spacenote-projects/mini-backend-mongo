from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from spacenote.core.modules.space.models import SpaceView
from spacenote.web.deps import AppDep, AuthTokenDep

router = APIRouter(tags=["spaces"])


class CreateSpaceRequest(BaseModel):
    """Request model for creating a new space."""

    slug: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern="^[a-z0-9-]+$",
        description="Unique identifier for the space (lowercase letters, numbers, hyphens only)",
        examples=["my-project"],
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Display name of the space",
        examples=["My Project"],
    )


class AddMemberRequest(BaseModel):
    """Request model for adding a member to a space."""

    username: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Username of the user to add as a member",
        examples=["alice"],
    )


class ErrorResponse(BaseModel):
    """Standard error response format."""

    message: str = Field(..., description="Human-readable error message")
    type: str = Field(..., description="Machine-readable error type")


@router.get(
    "/spaces",
    summary="List spaces",
    description=(
        "Returns a list of spaces accessible to the current user. "
        "Admin sees all spaces, regular users see only spaces where they are members."
    ),
    operation_id="getSpaces",
    responses={
        200: {"description": "Space list retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def get_spaces(
    app: AppDep,
    auth_token: AuthTokenDep,
) -> list[SpaceView]:
    """Get all accessible spaces."""
    return await app.get_spaces(auth_token)


@router.post(
    "/spaces",
    summary="Create new space",
    description="Creates a new space with the specified slug and title. Requires admin privileges.",
    operation_id="createSpace",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Space created successfully"},
        400: {"model": ErrorResponse, "description": "Validation error (e.g., slug already exists or invalid format)"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Admin privileges required"},
    },
)
async def create_space(
    create_data: CreateSpaceRequest,
    app: AppDep,
    auth_token: AuthTokenDep,
) -> SpaceView:
    """Create a new space (admin only)."""
    return await app.create_space(auth_token, create_data.slug, create_data.title)


@router.post(
    "/spaces/{slug}/members",
    summary="Add member to space",
    description="Adds a user as a member of the specified space. Requires admin privileges.",
    operation_id="addSpaceMember",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Member added successfully"},
        400: {"model": ErrorResponse, "description": "Validation error (e.g., user already a member)"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Admin privileges required"},
        404: {"model": ErrorResponse, "description": "Space or user not found"},
    },
)
async def add_space_member(
    slug: str,
    member_data: AddMemberRequest,
    app: AppDep,
    auth_token: AuthTokenDep,
) -> SpaceView:
    """Add member to space (admin only)."""
    return await app.add_space_member(auth_token, slug, member_data.username)
