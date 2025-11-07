from typing import Any

from pymongo import ASCENDING
from pymongo.asynchronous.database import AsyncDatabase

from spacenote.core.core import Service
from spacenote.core.modules.comment.models import Comment
from spacenote.core.pagination import PaginationResult


class CommentService(Service):
    def __init__(self, database: AsyncDatabase[dict[str, Any]]) -> None:
        super().__init__(database)
        self._collection = database.get_collection("comments")

    async def on_start(self) -> None:
        await self._collection.create_index(
            [("space_slug", ASCENDING), ("note_number", ASCENDING), ("number", ASCENDING)],
            unique=True,
        )

    async def create_comment(self, space_slug: str, note_number: int, author_username: str, content: str) -> Comment:
        """Create a new comment on a note."""
        await self.core.services.note.get_note(space_slug, note_number)

        next_number = await self.core.services.counter.get_next_comment_number(space_slug, note_number)

        comment = Comment(
            space_slug=space_slug,
            note_number=note_number,
            author_username=author_username,
            number=next_number,
            content=content,
        )

        await self._collection.insert_one(comment.model_dump())
        return comment

    async def list_comments(
        self,
        space_slug: str,
        note_number: int,
        limit: int = 100,
        offset: int = 0,
    ) -> PaginationResult[Comment]:
        """Get paginated comments for a note, sorted by number ascending (oldest first)."""
        query = {"space_slug": space_slug, "note_number": note_number}

        total = await self._collection.count_documents(query)

        cursor = self._collection.find(query)
        cursor = cursor.sort("number", 1)
        cursor = cursor.skip(offset).limit(limit)

        docs = await cursor.to_list()
        items = [Comment.model_validate(doc) for doc in docs]

        return PaginationResult(items=items, total=total, limit=limit, offset=offset)
