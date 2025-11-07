from enum import StrEnum

from pydantic import BaseModel, Field

from spacenote.core.db import MongoModel

# Type for field option values (VALUES, MIN, MAX, MAX_WIDTH)
FieldOptionValueType = list[str] | int

# Type for actual field values in notes
FieldValueType = str | list[str] | int | float | None


class FieldType(StrEnum):
    """Available field types for space schemas."""

    STRING = "string"
    SELECT = "select"  # Single select from predefined values
    TAGS = "tags"  # Free-form tags
    USER = "user"  # Reference to space member
    INT = "int"
    FLOAT = "float"
    IMAGE = "image"  # Reference to image attachment with preview


class FieldOption(StrEnum):
    """Configuration options for field types."""

    VALUES = "values"  # list[str] for SELECT
    MIN = "min"  # int/float for numeric types
    MAX = "max"  # int/float for numeric types
    MAX_WIDTH = "max_width"  # int for IMAGE preview max width


class SpaceField(BaseModel):
    """Field definition in a space schema."""

    id: str = Field(..., description="Field identifier (must be unique within space)")
    type: FieldType = Field(..., description="Field data type")
    required: bool = Field(False, description="Whether this field is required")
    options: dict[FieldOption, FieldOptionValueType] = Field(
        default_factory=dict,
        description=(
            "Field type-specific options (e.g., 'values' for select, 'min'/'max' for numeric types, 'max_width' for image)"
        ),
    )
    default: FieldValueType = Field(None, description="Default value for this field")


class Space(MongoModel):
    """Container for notes with custom schemas."""

    slug: str = Field(
        ...,
        description=(
            "Natural key and unique identifier for the space (e.g., 'my-project'). "
            "Used everywhere instead of _id for cleaner API and URLs."
        ),
    )
    title: str = Field(..., description="Display name of the space")
    members: list[str] = Field(
        default_factory=list,
        description=("List of usernames with access to this space. Validated against existing users via UserService."),
    )
    fields: list[SpaceField] = Field(
        default_factory=list,
        description="Custom field definitions for notes in this space",
    )


class SpaceView(BaseModel):
    """Public space representation for API responses."""

    slug: str = Field(..., description="Unique identifier for the space")
    title: str = Field(..., description="Display name of the space")
    members: list[str] = Field(..., description="List of usernames with access to this space")
    fields: list[SpaceField] = Field(..., description="Custom field definitions for notes in this space")
