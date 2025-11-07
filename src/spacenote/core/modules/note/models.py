from datetime import datetime

from pydantic import Field

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
