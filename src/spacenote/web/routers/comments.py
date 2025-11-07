from typing import Annotated

from fastapi import APIRouter, Query, status
from pydantic import BaseModel, Field

from spacenote.core.modules.comment.models import CommentView
from spacenote.core.pagination import PaginationResult
from spacenote.web.deps import AppDep, AuthTokenDep

router = APIRouter(tags=["comments"])


class CreateCommentRequest(BaseModel):
    """Request model for creating a new comment."""

    content: str = Field(
        ...,
        description="Comment content",
        min_length=1,
        examples=["This is a great note!"],
    )


class ErrorResponse(BaseModel):
    """Standard error response format."""

    message: str = Field(..., description="Human-readable error message")
    type: str = Field(..., description="Machine-readable error type")


@router.post(
    "/spaces/{space_slug}/notes/{note_number}/comments",
    summary="Create comment on note",
    description=(
        "Creates a new comment on the specified note. "
        "Requires space membership. "
        "Comments are numbered sequentially within each note."
    ),
    operation_id="createComment",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Comment created successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Space access required (not a member)"},
        404: {"model": ErrorResponse, "description": "Space or note not found"},
    },
)
async def create_comment(
    space_slug: str,
    note_number: int,
    create_data: CreateCommentRequest,
    app: AppDep,
    auth_token: AuthTokenDep,
) -> CommentView:
    """Create a new comment (members only)."""
    return await app.create_comment(auth_token, space_slug, note_number, create_data.content)


@router.get(
    "/spaces/{space_slug}/notes/{note_number}/comments",
    summary="List note comments",
    description="Get paginated list of comments on a note. Only space members can view comments.",
    operation_id="listComments",
    responses={
        200: {"description": "Paginated list of comments"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Not a member of this space"},
        404: {"model": ErrorResponse, "description": "Space or note not found"},
    },
)
async def list_comments(
    space_slug: str,
    note_number: int,
    app: AppDep,
    auth_token: AuthTokenDep,
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum items per page")] = 100,
    offset: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
) -> PaginationResult[CommentView]:
    """List comments with pagination (members only)."""
    return await app.list_comments(auth_token, space_slug, note_number, limit, offset)
