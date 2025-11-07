from enum import StrEnum

from spacenote.core.db import MongoModel


class CounterType(StrEnum):
    NOTE = "note"


class Counter(MongoModel):
    space_slug: str
    counter_type: CounterType
    seq: int = 0
