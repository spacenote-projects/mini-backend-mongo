from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def customize_openapi(app: FastAPI) -> None:
    """Customize OpenAPI schema with security schemes."""

    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Add Bearer token security scheme
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "description": "Enter your authentication token",
            }
        }

        # Apply security to all endpoints except those explicitly marked as public
        for path in openapi_schema["paths"].values():
            for operation in path.values():
                if isinstance(operation, dict) and "security" not in operation:
                    # Add security requirement if not explicitly public
                    operation["security"] = [{"BearerAuth": []}]

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi  # type: ignore[method-assign]
