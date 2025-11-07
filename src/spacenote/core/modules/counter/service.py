from typing import Any

from pymongo import ASCENDING, ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase

from spacenote.core.core import Service
from spacenote.core.modules.counter.models import CounterType


class CounterService(Service):
    def __init__(self, database: AsyncDatabase[dict[str, Any]]) -> None:
        super().__init__(database)
        self._collection = database.get_collection("counters")

    async def on_start(self) -> None:
        await self._collection.create_index(
            [("space_slug", ASCENDING), ("counter_type", ASCENDING)],
            unique=True,
        )

    async def get_next_sequence(self, space_slug: str, counter_type: CounterType) -> int:
        result = await self._collection.find_one_and_update(
            {"space_slug": space_slug, "counter_type": counter_type},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        if result is None:
            raise RuntimeError("Failed to get next sequence number")
        return int(result["seq"])
