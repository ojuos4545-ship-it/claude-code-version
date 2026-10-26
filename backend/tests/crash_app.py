"""App factory for test_security_logging: real routes plus routes that fail on purpose.

Run by a real uvicorn process (`tests.crash_app:create --factory`).
"""

from __future__ import annotations

import os

from pydantic import BaseModel

from app.config import load_settings
from app.main import create_app

SECRET = "SECRET-MEAL-kimchi-7f3a"


class _Out(BaseModel):
    count: int


def create():
    settings = load_settings({"APP_ENV": "test", "APP_DATABASE_PATH": os.environ["CRASH_APP_DB"]})
    app = create_app(settings)

    @app.post("/crash/sync")
    def crash_sync(body: dict):
        raise ValueError(f"cannot store {body['description']}")

    @app.post("/crash/async")
    async def crash_async(body: dict):
        raise RuntimeError(f"cannot store {body['description']}")

    @app.get("/crash/response", response_model=_Out)
    def crash_response():
        # Fails response validation: FastAPI raises ResponseValidationError whose
        # message includes this input value.
        return {"count": SECRET}

    return app
