from typing import Annotated, Any

from fastapi import APIRouter, Query, status
from pydantic import BaseModel, Field

from spacenote.core.modules.note.models import NoteView
from spacenote.core.pagination import PaginationResult
from spacenote.web.deps import AppDep, AuthTokenDep

router = APIRouter(tags=["notes"])


class CreateNoteRequest(BaseModel):
    """Request model for creating a new note."""

    fields: dict[str, str] = Field(
        ...,
        description="Field values for the note (all values as strings, will be converted based on field type)",
        examples=[{"title": "My Note", "description": "Note content", "priority": "5"}],
    )


class SearchNotesRequest(BaseModel):
    """Request model for searching/filtering notes with MongoDB query syntax."""

    filter: dict[str, Any] = Field(
        default_factory=dict,
        description="MongoDB query filter (e.g., {'fields.status': 'in_progress', 'fields.priority': {'$gte': 5}})",
        examples=[
            {"fields.status": "in_progress"},
            {"fields.tags": {"$in": ["bug", "urgent"]}},
            {"$and": [{"fields.status": {"$ne": "completed"}}, {"author_username": "alice"}]},
        ],
    )
    sort: dict[str, Any] = Field(
        default_factory=lambda: {"number": -1},
        description="MongoDB sort specification (e.g., {'created_at': -1, 'number': -1}). Use -1 for descending, 1 for ascending",
        examples=[
            {"created_at": -1},
            {"fields.priority": -1, "number": -1},
        ],
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Maximum items per page",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of items to skip",
    )


class ErrorResponse(BaseModel):
    """Standard error response format."""

    message: str = Field(..., description="Human-readable error message")
    type: str = Field(..., description="Machine-readable error type")


@router.post(
    "/spaces/{space_slug}/notes",
    summary="Create new note",
    description=(
        "Creates a new note in the specified space. "
        "Requires space membership. "
        "All field values should be provided as strings and will be converted based on field type definitions."
    ),
    operation_id="createNote",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Note created successfully"},
        400: {
            "model": ErrorResponse,
            "description": "Validation error (e.g., missing required field, invalid field value)",
        },
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Space access required (not a member)"},
        404: {"model": ErrorResponse, "description": "Space not found"},
    },
)
async def create_note(
    space_slug: str,
    create_data: CreateNoteRequest,
    app: AppDep,
    auth_token: AuthTokenDep,
) -> NoteView:
    """Create a new note (members only)."""
    return await app.create_note(auth_token, space_slug, create_data.fields)


@router.get(
    "/spaces/{space_slug}/notes",
    summary="List space notes",
    description="Get paginated list of notes in a space. Only space members can view notes.",
    operation_id="listNotes",
    responses={
        200: {"description": "Paginated list of notes"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Not a member of this space"},
        404: {"model": ErrorResponse, "description": "Space not found"},
    },
)
async def list_notes(
    space_slug: str,
    app: AppDep,
    auth_token: AuthTokenDep,
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum items per page")] = 50,
    offset: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
) -> PaginationResult[NoteView]:
    """List notes with pagination (members only)."""
    return await app.list_notes(auth_token, space_slug, limit, offset)


@router.get(
    "/spaces/{space_slug}/notes/{number}",
    summary="Get note by number",
    description="Get a specific note by its number within a space. Only space members can view notes.",
    operation_id="getNote",
    responses={
        200: {"description": "Note details"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Not a member of this space"},
        404: {"model": ErrorResponse, "description": "Space or note not found"},
    },
)
async def get_note(
    space_slug: str,
    number: int,
    app: AppDep,
    auth_token: AuthTokenDep,
) -> NoteView:
    """Get single note by number (members only)."""
    return await app.get_note(auth_token, space_slug, number)


@router.post(
    "/spaces/{space_slug}/notes/search",
    summary="Search/filter notes",
    description=(
        "Search and filter notes in a space using MongoDB query syntax. "
        "Supports complex filtering with MongoDB operators ($eq, $ne, $gt, $gte, $lt, $lte, $in, $nin, $all, $regex, $and, $or) "
        "and custom sorting. Only space members can search notes."
    ),
    operation_id="searchNotes",
    responses={
        200: {"description": "Paginated search results"},
        400: {"model": ErrorResponse, "description": "Invalid filter or sort specification"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Not a member of this space"},
        404: {"model": ErrorResponse, "description": "Space not found"},
    },
)
async def search_notes(
    space_slug: str,
    search_data: SearchNotesRequest,
    app: AppDep,
    auth_token: AuthTokenDep,
) -> PaginationResult[NoteView]:
    """Search notes with MongoDB query syntax (members only)."""
    return await app.search_notes(
        auth_token,
        space_slug,
        search_data.filter,
        search_data.sort,
        search_data.limit,
        search_data.offset,
    )
