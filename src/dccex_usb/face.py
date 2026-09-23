"""The mirror's own face: what the UI asks this app about this app.

A face is an app's own interface, served on the UI's origin and behind the
same door, about the app rather than about a railroad (ADR-0002). This one is
the mirror's, and it is what the page for the command station talks to and the
only thing it talks to: a command station is not a fact about a railroad, so
there is no bus here to carry the question and no store to keep the answer
(ADR-0001).

**Routing is a function of a method, a path and a body, and it answers with a
status and a body.** Nothing in it touches a socket, which is what lets every
question about what the face says be asked of it directly: what carries it
over TCP is a way of reaching this function and has no answers of its own.

**The source of releases is configuration and never payload.** The LAN carries
no authentication on purpose (ADR-0042), so a request that could name where to
read releases from would be a request that decides what the station is offered
to run. The face is constructed with the source the app was started with, and
a request cannot reach it: a query string is not read, and a body is not read
for one either.

**A source that cannot be reached is an answer with a reason on it.** The
release API is somebody else's service on somebody else's network, and the
mirror's job is to mirror what it is doing rather than to fall over with it: a
source that is away, or that answers with something that is not a list of
releases, is a status and a sentence, and the app goes on mirroring the cable
either way.
"""

import asyncio
import json
from collections.abc import Callable
from http import HTTPStatus
from typing import NamedTuple, cast
from urllib.parse import urlsplit

from dccex_usb.firmware import RELEASES, Fetch, fetch
from dccex_usb.station import HOST, to_stderr

PORT = 8080
"""The port the face is served on unless a box says otherwise. Not the
mirror's: 2560 is the station's own conversation, and what the door reaches is
this one."""

PATIENCE_S = 10.0
"""How long one request is given, from its first byte to its answer being
taken. The loop this is on is the mirror's, so a caller that says nothing, or
that stops reading half way through its answer, is let go rather than waited
on for as long as the railroad runs."""

MAX_BODY_BYTES = 1 << 16
"""How much body the face reads. What a page asks this app is a tag and a
gesture; anything larger is not a question this answers, and reading it would
be a buffer somebody else decides the size of (ADR-0042)."""

CRLF = "\r\n"
HEAD_END = b"\r\n\r\n"
LENGTH = "content-length"
JSON = "application/json"

RELEASES_PATH = "/releases"
"""What the releases the source carries are asked for at. The answer is their
tags, because a tag is the only thing a caller ever names (CONTEXT.md)."""

TAG = "tag_name"
"""What the release API calls a release's tag."""


class Answered(NamedTuple):
    """What routing comes to: a status, and a body to be rendered as JSON."""

    status: HTTPStatus
    body: dict[str, object]


def tags(document: object) -> list[str] | None:
    """The tags the releases in `document` are named by, or None where it is
    not a list of releases at all.

    Read the way a document from a service is read — one field at a time, and
    every shape it is not is None rather than an exception — because this is
    somebody else's API and a reader that reached into it would be taken down
    by whatever it returned the day it returned something else. A source that
    lists nothing carries no releases yet, which is an answer; a source that
    lists entries and names none of them is not answering about releases,
    which is not.
    """
    if not isinstance(document, list):
        return None
    listed = cast(list[object], document)
    named: list[str] = []
    for entry in listed:
        if not isinstance(entry, dict):
            continue
        tag = cast(dict[str, object], entry).get(TAG)
        if isinstance(tag, str) and tag:
            named.append(tag)
    if listed and not named:
        return None
    return named


class Face:
    """What the mirror answers, and the configuration it answers out of.

    Constructed with the source of releases the app was started with and with
    what fetches a URL, which the suite substitutes so that nothing in the
    gate reaches the release API.
    """

    def __init__(
        self,
        releases: str = RELEASES,
        *,
        fetch: Fetch = fetch,
    ) -> None:
        self._releases = releases
        self._fetch = fetch

    async def answer(self, method: str, path: str, body: bytes) -> Answered:
        """One request answered: the method, the path as it arrived, and the
        bytes that came with it.

        The path arrives whole, query string and all, and the query is split
        off and dropped here rather than somewhere a reader has to go and
        check: this is the function that would have to read a source out of a
        request for one to redirect the face, and it does not.

        No route reads the body yet. It is here because it is half of what a
        route is asked with, and what will read one is the flash the UI asks
        for by tag (#13).
        """
        asked = urlsplit(path).path
        if asked != RELEASES_PATH:
            return refused(
                HTTPStatus.NOT_FOUND, f"the mirror's face does not answer {asked}"
            )
        if method != "GET":
            return refused(
                HTTPStatus.METHOD_NOT_ALLOWED,
                f"{asked} is read with GET, and this was {method}",
            )
        return await self._carried()

    async def _carried(self) -> Answered:
        """The tags the configured source carries, or why they could not be
        read: the source is away, or what it said is not a list of releases."""
        try:
            document = json.loads(await self._fetch(self._releases))
        except (OSError, ValueError) as away:
            return refused(
                HTTPStatus.BAD_GATEWAY,
                f"the releases at {self._releases} could not be read: {away}",
            )
        carried = tags(document)
        if carried is None:
            return refused(
                HTTPStatus.BAD_GATEWAY,
                f"the releases at {self._releases} are not a list of releases",
            )
        return Answered(HTTPStatus.OK, {"tags": carried})


def refused(status: HTTPStatus, reason: str) -> Answered:
    """A status and the sentence that goes with it.

    One field and one sentence: what is on the other end is a page, and a
    caller that cannot say what went wrong makes a person go and read a log on
    a box (ADR-0050).
    """
    return Answered(status, {"reason": reason})


class Asked(NamedTuple):
    """What a request says before its body: the method, the path it names as
    it was written, and how many bytes of body it says are coming."""

    method: str
    path: str
    length: int


def requested(head: bytes) -> Asked | None:
    """What a request head asks for, or None where it is not a request.

    The head is read and nothing else of HTTP is: the method, the target and
    the length of the body. This is a face on a private origin behind the
    door, spoken to by one page (ADR-0002), so the parts of the protocol a
    general server owes the world — negotiation, encodings, a connection kept
    open for the next request — are parts this would carry without ever being
    asked for them.
    """
    lines = head.decode("latin-1").split(CRLF)
    asked = lines[0].split(" ")
    if len(asked) != 3 or not asked[2].startswith("HTTP/"):
        return None
    length = 0
    for line in lines[1:]:
        name, found, value = line.partition(":")
        if not found or name.strip().lower() != LENGTH:
            continue
        try:
            length = int(value.strip())
        except ValueError:
            return None
        if length < 0:
            return None
    return Asked(asked[0], asked[1], length)


def response(answered: Answered) -> bytes:
    """One answer on the wire: the status, the JSON body, and the connection
    ending.

    The connection is closed after each answer rather than kept for the next
    one. Keeping it would make this a server that has to track a request
    boundary it has no other reason to know, for a page that asks a question
    at a time.
    """
    body = json.dumps(answered.body).encode()
    head = (
        f"HTTP/1.1 {int(answered.status)} {answered.status.phrase}{CRLF}"
        f"Content-Type: {JSON}{CRLF}"
        f"Content-Length: {len(body)}{CRLF}"
        f"Connection: close{CRLF}{CRLF}"
    )
    return head.encode() + body


class Server:
    """The port the face is reached on, and nothing about what it says.

    **Handed back unstarted.** Constructing one binds nothing; `start()`
    binds and serves, `port` is the port the OS chose when asked for 0, and
    `close()` gives it back — the same split `Station` is driven by, and what
    lets a test start and stop one without a process around it.

    It is a port of its own and not the mirror's: 2560 is a serial
    conversation that JMRI and the throttles are in the middle of, and an
    HTTP request arriving on it would be bytes typed at the command station.
    The device is not reached from here at all.
    """

    def __init__(
        self,
        face: Face,
        port: int = PORT,
        *,
        log: Callable[[str], None] = to_stderr,
        patience_s: float = PATIENCE_S,
        max_body_bytes: int = MAX_BODY_BYTES,
    ) -> None:
        self._face = face
        self._port = port
        self._log = log
        self._patience_s = patience_s
        self._max_body_bytes = max_body_bytes
        self._server: asyncio.Server | None = None
        self._asking: set[asyncio.StreamWriter] = set()

    async def start(self) -> None:
        """Bind the port and answer on it.

        Every interface, for the reason the mirror's port is: the container
        publishes what the door reaches, and what limits the reach is the LAN
        (ADR-0042). A port already taken raises out of here, which is a
        process that ends rather than one that is up with a face nobody can
        reach (#526).
        """
        self._server = await asyncio.start_server(self._asked, HOST, self._port)

    @property
    def port(self) -> int:
        """The port being served: the one the OS chose, when asked for 0."""
        return int(self._serving().sockets[0].getsockname()[1])

    async def close(self) -> None:
        """Stop answering and give the port back."""
        server, self._server = self._server, None
        if server is not None:
            server.close()
        # Aborted, and before the wait: `wait_closed()` does not return while
        # a handler is running, and a caller that has stopped reading its
        # answer is a handler that waits on a client that is not there. The
        # app ends through here, so this wait has to be one that ends
        # (station.py, `close`).
        for writer in tuple(self._asking):
            writer.transport.abort()
        if server is not None:
            await server.wait_closed()

    async def _asked(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """One request answered, and the connection ended either way.

        Bounded by `patience_s`, because this loop is the mirror's: a caller
        that opened a connection and said nothing, or that is not taking its
        answer, is not something the process that holds the command station
        waits on for ever.
        """
        self._asking.add(writer)
        try:
            await asyncio.wait_for(self._exchange(reader, writer), self._patience_s)
        except (TimeoutError, OSError, asyncio.IncompleteReadError):
            writer.transport.abort()
        finally:
            self._asking.discard(writer)
            writer.close()

    async def _exchange(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        writer.write(response(await self._answered(reader)))
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    async def _answered(self, reader: asyncio.StreamReader) -> Answered:
        """The request read off the connection, and routing's answer to it.

        What a request is not is a status too: a head longer than this reads,
        a first line that is not a request, and a body larger than a face
        asked questions by a page has any use for.
        """
        try:
            head = await reader.readuntil(HEAD_END)
        except asyncio.LimitOverrunError:
            return refused(
                HTTPStatus.REQUEST_HEADER_FIELDS_TOO_LARGE,
                "the request head is longer than the mirror's face reads",
            )
        asked = requested(head)
        if asked is None:
            return refused(
                HTTPStatus.BAD_REQUEST, "that is not a request the mirror's face reads"
            )
        if asked.length > self._max_body_bytes:
            return refused(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                f"a body of {asked.length} bytes is more than the mirror's face"
                f" reads ({self._max_body_bytes})",
            )
        body = await reader.readexactly(asked.length) if asked.length else b""
        return await self._face.answer(asked.method, asked.path, body)

    def _serving(self) -> asyncio.Server:
        if self._server is None:
            raise RuntimeError("the face is not served")
        return self._server
