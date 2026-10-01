"""A fake store, for the suites that read a script off one and the one that
writes one to it.

The routes are `control`'s and documented there (rails49/control#586); what is
here answers the three this repository asks for. `GET /scripts/<railroad>`,
which the translator reads, as that document says:
`{"script": "<railroad>", "text": "..."}`, and `404` for a railroad with no
script. `PUT /scripts/<railroad>`, taking the same document and answering
`{"saved": "<railroad>"}`, which is what the face does with an applied script
(#185). And `GET /drawings`, `{"drawings": [...]}`, which is the railroads
there are — a railroad's drawing is what the store keeps under its name, so
that list is the list of railroads. No copy of the store is taken and none is
imported — a test here runs against a fake and `control` owns the routes
(ADR-0014, consequences).

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
from typing import Any, cast

import pytest

from tests.ports import free_port

SCRIPTS = "/scripts/"
DRAWINGS = "/drawings"


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
        # Every script the store was asked to save, in the order it was asked:
        # what a test reads to say whether a text reached the store at all.
        self.saved: list[tuple[str, Any]] = []
        # What the list route answers, which is the railroads there are. A
        # test names them and it is answered as it stands, typed loosely for
        # the reason `scripts` above is: a list this app cannot read is one of
        # the things the reader tells apart. `holds()` below adds a name the
        # way saving a script does.
        self.drawings: list[Any] = []
        # Set by a test to have every answer carry this status instead, and
        # to have every answer dropped halfway through its body: a store
        # restarting while it answers.
        self.fails: int | None = None
        self.cuts = False
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
            if railroad not in self.drawings:
                self.drawings.append(railroad)

    def _answer(self, railroad: str) -> tuple[int, dict[str, Any]]:
        with self._lock:
            self.asked.append(railroad)
            text = self.scripts.get(railroad)
        if text is None:
            return 404, {"error": f"no script for '{railroad}'"}
        return 200, {"script": railroad, "text": text}

    def _put(self, railroad: str, document: Any) -> tuple[int, dict[str, Any]]:
        """A script saved, as the store's own `PUT` routes do it: the document
        names the railroad it is for, and one that names another cannot be
        saved under this name."""
        if not isinstance(document, dict):
            return 400, {"error": "a script document is required"}
        named = cast(dict[str, Any], document).get("script")
        if named != railroad:
            return 400, {"error": f"script '{named}' cannot be saved as '{railroad}'"}
        with self._lock:
            said = cast(dict[str, Any], document)
            self.saved.append((railroad, said))
            self.scripts[railroad] = said.get("text")
            if railroad not in self.drawings:
                self.drawings.append(railroad)
        return 200, {"saved": railroad}

    def _handler(self) -> type[BaseHTTPRequestHandler]:
        store = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # http.server's own name
                if self.path == DRAWINGS:
                    self._said(200, {"drawings": store.drawings})
                    return
                if not self.path.startswith(SCRIPTS):
                    self._said(404, {"error": f"no route {self.path}"})
                    return
                status, body = store._answer(self.path[len(SCRIPTS) :])
                self._said(status, body)

            def do_PUT(self) -> None:  # http.server's own name
                if not self.path.startswith(SCRIPTS):
                    self._said(404, {"error": f"no route {self.path}"})
                    return
                length = int(self.headers.get("Content-Length", 0))
                try:
                    document = json.loads(self.rfile.read(length))
                except ValueError:
                    self._said(400, {"error": "a script document is required"})
                    return
                status, body = store._put(self.path[len(SCRIPTS) :], document)
                self._said(status, body)

            def _said(self, status: int, body: dict[str, Any]) -> None:
                said = json.dumps(body).encode()
                self.send_response(store.fails or status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(said)))
                self.end_headers()
                self.wfile.write(said[: len(said) // 2] if store.cuts else said)
                self.close_connection = store.cuts

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
