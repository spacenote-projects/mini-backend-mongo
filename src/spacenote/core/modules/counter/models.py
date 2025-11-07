from spacenote.core.db import MongoModel


class NoteCounter(MongoModel):
    """Counter for sequential note numbering within a space."""

    space_slug: str
    seq: int = 0


class CommentCounter(MongoModel):
    """Counter for sequential comment numbering within a note."""

    space_slug: str
    note_number: int
    seq: int = 0
