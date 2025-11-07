from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Application configuration loaded from environment variables."""

    database_url: str
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False

    model_config = {
        "env_file": [".env"],
        "env_prefix": "SPACENOTE_",
        "extra": "ignore",
    }
