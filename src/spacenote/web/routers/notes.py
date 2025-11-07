from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from spacenote.core.modules.note.models import NoteView
from spacenote.web.deps import AppDep, AuthTokenDep

router = APIRouter(tags=["notes"])


class CreateNoteRequest(BaseModel):
    """Request model for creating a new note."""

    fields: dict[str, str] = Field(
        ...,
        description="Field values for the note (all values as strings, will be converted based on field type)",
        examples=[{"title": "My Note", "description": "Note content", "priority": "5"}],
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
