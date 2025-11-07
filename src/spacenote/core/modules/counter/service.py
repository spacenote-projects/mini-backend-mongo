from typing import Any

from pymongo import ASCENDING, ReturnDocument
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase

from spacenote.core.core import Service


class CounterService(Service):
    def __init__(self, database: AsyncDatabase[dict[str, Any]]) -> None:
        super().__init__(database)
        self._note_counters: AsyncCollection[dict[str, Any]] = database.get_collection("note_counters")
        self._comment_counters: AsyncCollection[dict[str, Any]] = database.get_collection("comment_counters")

    async def on_start(self) -> None:
        await self._note_counters.create_index(
            [("space_slug", ASCENDING)],
            unique=True,
        )
        await self._comment_counters.create_index(
            [("space_slug", ASCENDING), ("note_number", ASCENDING)],
            unique=True,
        )

    async def get_next_note_number(self, space_slug: str) -> int:
        """Get next sequential note number for a space."""
        result = await self._note_counters.find_one_and_update(
            {"space_slug": space_slug},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        if result is None:
            raise RuntimeError("Failed to get next note number")
        return int(result["seq"])

    async def get_next_comment_number(self, space_slug: str, note_number: int) -> int:
        """Get next sequential comment number for a note."""
        result = await self._comment_counters.find_one_and_update(
            {"space_slug": space_slug, "note_number": note_number},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        if result is None:
            raise RuntimeError("Failed to get next comment number")
        return int(result["seq"])
