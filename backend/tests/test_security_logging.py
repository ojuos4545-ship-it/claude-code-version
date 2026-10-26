"""PRD 7 / Q6: unhandled errors must not put meal text or secrets in server logs.

Starts a real uvicorn process, because the leak was uvicorn printing the traceback
and exception message that Starlette's ServerErrorMiddleware re-raised to it.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import httpx
import pytest

from tests.crash_app import SECRET

BACKEND = Path(__file__).resolve().parent.parent
ERROR_BODY = {
    "error": {"code": "internal_error", "message": "Internal server error.", "details": []}
}


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextmanager
def uvicorn_server(db_path: Path):
    """Yields (base_url, output); output["text"] is uvicorn's stdout+stderr after exit."""
    port = _free_port()
    proc = subprocess.Popen(  # noqa: S603 - fixed arguments
        [sys.executable, "-m", "uvicorn", "tests.crash_app:create", "--factory"]
        + ["--host", "127.0.0.1", "--port", str(port)],
        cwd=BACKEND,
        env={**os.environ, "CRASH_APP_DB": str(db_path)},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    base = f"http://127.0.0.1:{port}"
    output: dict[str, str] = {}
    try:
        deadline = time.monotonic() + 20
        while True:
            try:
                if httpx.get(f"{base}/healthz", timeout=1).status_code == 200:
                    break
            except httpx.TransportError:
                pass
            if proc.poll() is not None or time.monotonic() > deadline:
                pytest.fail("uvicorn did not start")
            time.sleep(0.1)
        yield base, output
    finally:
        proc.terminate()
        try:
            out, err = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            out, err = proc.communicate()
        output["text"] = out + err


def test_unhandled_errors_do_not_leak_into_server_logs(tmp_path):
    body = {"description": SECRET}
    with uvicorn_server(tmp_path / "crash.db") as (base, output):
        responses = [
            httpx.post(f"{base}/crash/sync?q=query-part", json=body),
            httpx.post(f"{base}/crash/async", json=body),
            httpx.get(f"{base}/crash/response"),  # ResponseValidationError
        ]
        assert httpx.get(f"{base}/healthz").status_code == 200  # still serving

    for r in responses:
        assert r.status_code == 500
        assert r.json() == ERROR_BODY
        assert SECRET not in r.text

    logs = output["text"]
    assert SECRET not in logs
    assert "Traceback" not in logs
    assert "Exception in ASGI application" not in logs
    ours = [line for line in logs.splitlines() if line.startswith("unhandled ")]
    assert ours == [
        "unhandled ValueError on POST '/crash/sync'",  # no query string
        "unhandled RuntimeError on POST '/crash/async'",
        "unhandled ResponseValidationError on GET '/crash/response'",
    ]


def test_unhandled_error_response_format(client, app):
    @app.get("/crash/inline")
    def crash():
        raise KeyError(SECRET)

    r = client.get("/crash/inline")
    assert r.status_code == 500
    assert r.json() == ERROR_BODY


def test_control_characters_in_path_are_escaped_in_log(client, app, caplog):
    @app.get("/crash/{name}")
    def crash(name: str):
        raise ValueError(name)

    client.get("/crash/a%0Aunhandled%20Forged")
    messages = [r.getMessage() for r in caplog.records if r.name == "easy_meal_log"]
    assert messages == ["unhandled ValueError on GET '/crash/a\\nunhandled Forged'"]
