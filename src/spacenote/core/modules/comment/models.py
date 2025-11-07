from datetime import datetime

from pydantic import BaseModel, Field

from spacenote.core.db import MongoModel
from spacenote.core.utils import now


class Comment(MongoModel):
    """Comment on a note."""

    space_slug: str
    note_number: int
    author_username: str
    number: int  # Sequential number per note
    content: str
    created_at: datetime = Field(default_factory=now)


class CommentView(BaseModel):
    """Public comment representation for API responses."""

    space_slug: str = Field(..., description="Space identifier")
    note_number: int = Field(..., description="Note number within space")
    author_username: str = Field(..., description="Username of comment author")
    number: int = Field(..., description="Sequential comment number within note")
    content: str = Field(..., description="Comment content")
    created_at: datetime = Field(..., description="Comment creation timestamp")
