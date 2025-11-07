from pydantic import BaseModel

from spacenote.core.db import MongoModel


class User(MongoModel):
    """User model with embedded authentication token.

    Natural key: username
    Technical key: _id (ObjectId)
    """

    username: str
    token: str


class UserView(BaseModel):
    """Public user representation for API responses.

    Token is intentionally hidden for security.
    """

    username: str
