from datetime import UTC, datetime
from typing import Any

from pymongo import ASCENDING
from pymongo.asynchronous.database import AsyncDatabase

from spacenote.core.core import Service
from spacenote.core.modules.note.models import Note
from spacenote.core.modules.space.models import FieldType
from spacenote.core.pagination import PaginationResult
from spacenote.errors import NotFoundError, ValidationError


class NoteService(Service):
    def __init__(self, database: AsyncDatabase[dict[str, Any]]) -> None:
        super().__init__(database)
        self._collection = database.get_collection("notes")

    async def on_start(self) -> None:
        await self._collection.create_index(
            [("space_slug", ASCENDING), ("number", ASCENDING)],
            unique=True,
        )

    async def create_note(self, space_slug: str, author_username: str, raw_fields: dict[str, str]) -> Note:
        space = self.core.services.space.get_space(space_slug)

        next_number = await self.core.services.counter.get_next_note_number(space_slug)

        validated_fields: dict[str, str | list[str] | int | float | None] = {}

        for field_def in space.fields:
            field_id = field_def.id
            raw_value = raw_fields.get(field_id)

            if field_def.required and raw_value is None:
                raise ValidationError(f"Required field '{field_id}' is missing")

            if raw_value is None:
                validated_fields[field_id] = field_def.default
                continue

            if field_def.type == FieldType.INT:
                try:
                    validated_fields[field_id] = int(raw_value)
                except ValueError as e:
                    raise ValidationError(f"Field '{field_id}' must be an integer, got '{raw_value}'") from e
            elif field_def.type == FieldType.FLOAT:
                try:
                    validated_fields[field_id] = float(raw_value)
                except ValueError as e:
                    raise ValidationError(f"Field '{field_id}' must be a float, got '{raw_value}'") from e
            elif field_def.type == FieldType.TAGS:
                if isinstance(raw_value, str):
                    validated_fields[field_id] = [tag.strip() for tag in raw_value.split(",") if tag.strip()]
                else:
                    validated_fields[field_id] = raw_value
            else:
                validated_fields[field_id] = raw_value

        note = Note(
            space_slug=space_slug,
            number=next_number,
            author_username=author_username,
            created_at=datetime.now(UTC),
            fields=validated_fields,
        )

        await self._collection.insert_one(note.model_dump())
        return note

    async def get_note(self, space_slug: str, number: int) -> Note:
        """Get note by space slug and number."""
        doc = await self._collection.find_one({"space_slug": space_slug, "number": number})
        if not doc:
            raise NotFoundError(f"Note not found: space={space_slug}, number={number}")
        return Note.model_validate(doc)

    async def list_notes(self, space_slug: str, limit: int = 50, offset: int = 0) -> PaginationResult[Note]:
        """Get paginated notes in space, sorted by number descending (newest first)."""
        query = {"space_slug": space_slug}

        total = await self._collection.count_documents(query)

        cursor = self._collection.find(query)
        cursor = cursor.sort("number", -1)
        cursor = cursor.skip(offset).limit(limit)

        docs = await cursor.to_list()
        items = [Note.model_validate(doc) for doc in docs]

        return PaginationResult(items=items, total=total, limit=limit, offset=offset)
