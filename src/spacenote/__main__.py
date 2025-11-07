"""Main entry point for running the application."""

import uvicorn

from spacenote.app import App
from spacenote.config import Config
from spacenote.web.server import create_fastapi_app


def main() -> None:
    """Run the FastAPI application."""
    config = Config()
    app_instance = App(config)
    fastapi_app = create_fastapi_app(app_instance, config)

    uvicorn.run(
        fastapi_app,
        host=config.host,
        port=config.port,
        log_level="info" if config.debug else "warning",
    )


if __name__ == "__main__":
    main()
