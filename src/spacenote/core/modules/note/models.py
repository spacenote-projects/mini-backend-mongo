from datetime import datetime

from pydantic import BaseModel, Field

from spacenote.core.db import MongoModel
from spacenote.core.modules.space.models import FieldValueType
from spacenote.core.utils import now


class Note(MongoModel):
    """Note with custom fields stored in a space."""

    space_slug: str
    number: int  # Sequential per space, used in URLs: /spaces/{slug}/notes/{number}
    author_username: str
    created_at: datetime = Field(default_factory=now)
    fields: dict[str, FieldValueType]  # Values for space-defined fields


class NoteView(BaseModel):
    """Public note representation for API responses."""

    space_slug: str = Field(..., description="Space identifier")
    number: int = Field(..., description="Sequential note number within space")
    author_username: str = Field(..., description="Username of note creator")
    created_at: datetime = Field(..., description="Note creation timestamp")
    fields: dict[str, FieldValueType] = Field(..., description="Custom field values")
