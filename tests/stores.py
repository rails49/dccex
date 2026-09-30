"""A fake store, for the suites that read a script off one.

The routes are `control`'s and documented there (rails49/control#586); what is
here answers the one the translator reads, `GET /scripts/<railroad>`, as that
document says: `{"script": "<railroad>", "text": "..."}`, and `404` for a
railroad with no script. No copy of the store is taken and none is imported —
a test here runs against a fake and `control` owns the routes (ADR-0014,
consequences).

Bound when `opens()` is called and not before, so a test can have the
translator come up against a store that is not there yet and one that goes
away while it runs. The port is taken from the same place a broker's is and
held only by having been asked for, which is the shape `test_main.py`'s
station has.
"""

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import pytest

from tests.ports import free_port

SCRIPTS = "/scripts/"


class Store:
    """The store's face on loopback, holding one script per railroad.

    `scripts` is written by the test at any moment: a script edited on the
    page and applied is a document that changes under a translator that is
    running, which is the whole of what the translator watches for.
    """

    def __init__(self) -> None:
        self.port = free_port()
        # What the store holds, by railroad. Typed loosely so a test can
        # have it answer a document with no text in it, which is one of the
        # three things the reader tells apart.
        self.scripts: dict[str, Any] = {}
        self.asked: list[str] = []
        self._serving: ThreadingHTTPServer | None = None
        self._lock = threading.Lock()

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def opens(self) -> None:
        serving = ThreadingHTTPServer(("127.0.0.1", self.port), self._handler())
        self._serving = serving
        threading.Thread(target=serving.serve_forever, daemon=True).start()

    def closes(self) -> None:
        """The store gone: a socket nothing is listening on, which is the
        outage a translator meets when the store's container restarts."""
        serving = self._serving
        if serving is not None:
            serving.shutdown()
            serving.server_close()
            self._serving = None

    def holds(self, railroad: str, text: str) -> None:
        with self._lock:
            self.scripts[railroad] = text

    def _answer(self, railroad: str) -> tuple[int, dict[str, Any]]:
        with self._lock:
            self.asked.append(railroad)
            text = self.scripts.get(railroad)
        if text is None:
            return 404, {"error": f"no script for '{railroad}'"}
        return 200, {"script": railroad, "text": text}

    def _handler(self) -> type[BaseHTTPRequestHandler]:
        store = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # http.server's own name
                if not self.path.startswith(SCRIPTS):
                    self._said(404, {"error": f"no route {self.path}"})
                    return
                status, body = store._answer(self.path[len(SCRIPTS) :])
                self._said(status, body)

            def _said(self, status: int, body: dict[str, Any]) -> None:
                said = json.dumps(body).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(said)))
                self.end_headers()
                self.wfile.write(said)

            def log_message(self, format: str, *args: Any) -> None:
                """Quiet: what the suite reads is the translator's rows and
                the bytes on the wire."""

        return Handler


@pytest.fixture
def store() -> Iterator[Store]:
    serving = Store()
    try:
        yield serving
    finally:
        serving.closes()
