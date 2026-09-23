"""The mirror's own face: what the UI asks this app about this app.

A face is an app's own interface, served on the UI's origin and behind the
same door, about the app rather than about a railroad (ADR-0002). This one is
the mirror's, and it is what the page for the command station talks to and the
only thing it talks to: a command station is not a fact about a railroad, so
there is no bus here to carry the question and no store to keep the answer
(ADR-0001).

**Two things are asked of it: what releases the source carries, and that one
of them be written onto the station.** The second is what the face was wanted
for. Writing means owning the serial port, so the app that holds the device is
the only thing that can do it (ADR-0065, `firmware.py`); what this adds is
that whoever asked is told what happened, where a refusal used to be a line in
a log addressed to nobody (ADR-0001 d.2, ADR-0050).

**Nothing here guards the railroad.** This face cannot read a run state or a
track row — the mirror is not on the bus and a command station is not a fact
about a railroad — so the guarantee that a station is not written under a
moving train is the operator's, by way of the page that sequences it
(ADR-0006). The mirror checks nothing, as it never has.

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

**A browser reaches this through the door and never the LAN** (ADR-0004). The
page is served at the box's `dccex` label and the face is the same label under
a path prefix the door strips, so the two share one origin and one certificate
and the routing below is asked for `/releases` rather than for the address a
browser typed. What that buys is what is enforced here: a page from another
origin is refused, because on one origin the browser names the page that asked
and a face is private to its app.

**A source that cannot be reached is an answer with a reason on it.** The
release API is somebody else's service on somebody else's network, and the
mirror's job is to mirror what it is doing rather than to fall over with it: a
source that is away, or that answers with something that is not a list of
releases, is a status and a sentence, and the app goes on mirroring the cable
either way.
"""

import asyncio
import json
from collections.abc import Callable, Mapping
from http import HTTPStatus
from typing import NamedTuple, Protocol, cast
from urllib.parse import urlsplit

from dccex_usb.firmware import RELEASES, Fetch, Refusal, Wrote, fetch
from dccex_usb.station import HOST, to_stderr

PORT = 8080
"""The port the face is served on unless a box says otherwise. Not the
mirror's: 2560 is the station's own conversation, and what the door reaches is
this one."""

PATIENCE_S = 10.0
"""How long a caller is given to say what it is asking, and to take what it
asked for. The loop this is on is the mirror's, so a caller that says nothing,
or that stops reading half way through its answer, is let go rather than
waited on for as long as the railroad runs.

It does not bound the answering. A flash is minutes of esptool with a timeout
of its own (firmware.py), and the caller that asked for one is waited on for
the whole of it: what it asked is whether the station runs that build now."""

MAX_BODY_BYTES = 1 << 16
"""How much body the face reads. What a page asks this app is a tag and a
gesture; anything larger is not a question this answers, and reading it would
be a buffer somebody else decides the size of (ADR-0042)."""

CRLF = "\r\n"
HEAD_END = b"\r\n\r\n"
LENGTH = "content-length"
ORIGIN = "origin"
"""What a browser names the origin of the page that asked in. A caller that is
not a browser names none, and is not a page from another origin."""

ADDRESSED = "host"
"""What a request names the origin it was sent to in, which the door passes on
as the label it answered for. A page on the face's own origin named the same
one."""

JSON = "application/json"
REASON = "reason"
"""What an answer the caller cannot use carries its sentence in."""

RELEASES_PATH = "/releases"
"""What the releases the source carries are asked for at, with the door's
prefix already off it (ADR-0004). The answer is their tags, because a tag is
the only thing a caller ever names (CONTEXT.md)."""

TAG = "tag_name"
"""What the release API calls a release's tag."""

FLASH_PATH = "/flash"
"""What a build is asked to be written at, with the door's prefix already off
it (ADR-0004). Asked for and not read: there is nothing at this path to see,
and a page that reloaded one would write the station twice."""

ASKED_TAG = "tag"
"""What the body of a flash names the release to write. A tag and nothing
else — the source is this app's configuration and no request can reach it
(ADR-0042), so a body that named one is written out of the configured source
just the same, because nothing here looks for one."""

FLASHED = "flashed"
"""What an answer says a build was written under. The tag goes back with it,
so the page can say which one it was rather than which one it asked for."""

STATUS: Mapping[Refusal, HTTPStatus] = {
    # The caller's own to fix, and the two that are: `latest` is not a name
    # for a build (CONTEXT.md), and a body that names no tag asks nothing.
    Refusal.LATEST: HTTPStatus.BAD_REQUEST,
    # Somebody is writing the station already. What to do about it is to ask
    # again when it is over, which is what this says and 400 does not.
    Refusal.IN_FLIGHT: HTTPStatus.CONFLICT,
    # Nothing is wrong with the request: the cable is out or the station is
    # off, and it is fixed at the hardware (ADR-0050).
    Refusal.NO_STATION: HTTPStatus.SERVICE_UNAVAILABLE,
    # The source carries no release by that name. The tags it does carry are
    # one GET away, which is what the other route is for.
    Refusal.NO_RELEASE: HTTPStatus.NOT_FOUND,
    # Three statements about what somebody else's service published — a
    # release with no firmware on it, with no digest for it, or with bytes
    # that are not what it says they are. The same status the releases get
    # when that service cannot be read, and for the same reason: the mirror
    # reports what the source is doing rather than falling over with it.
    Refusal.NO_ASSET: HTTPStatus.BAD_GATEWAY,
    Refusal.NO_DIGEST: HTTPStatus.BAD_GATEWAY,
    Refusal.NOT_PUBLISHED: HTTPStatus.BAD_GATEWAY,
    # esptool ran, so the station may be half written. Not the caller's doing
    # and the one kind of answer that is worth a line on the box as well,
    # which is what a status of 500 or more gets it (`Server`).
    Refusal.TOOL_FAILED: HTTPStatus.INTERNAL_SERVER_ERROR,
    Refusal.TOOL_KILLED: HTTPStatus.GATEWAY_TIMEOUT,
    Refusal.RAISED: HTTPStatus.INTERNAL_SERVER_ERROR,
}
"""What each way of refusing a flash is answered with.

Every `Refusal` is here and a test holds that shut, because a refusal with no
status of its own would fall to a 500 and tell a page the mirror had broken
when what happened is that somebody typed a tag that does not exist.
"""


class Writes(Protocol):
    """What the face needs of the thing that writes a release onto the
    command station: a tag asked for, and what became of it.

    `Flasher` satisfies it by having the member. Narrow on purpose — the face
    is routing, and the whole of what it may do to the railroad's one live
    port is ask for a named release to be written on it, so a test stands in
    for all of that with an object that answers one call.
    """

    async def wanted(self, tag: str) -> Wrote: ...


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


def named(body: bytes) -> str | None:
    """The tag a flash is asked for in `body`, or None where it names none.

    Read the way a document from somewhere else is read — one field, and every
    shape it is not is None rather than an exception — because this arrives
    from a LAN with no authentication on it (ADR-0042). One field is also the
    whole of what is read: a body that also named where to fetch from is
    written out of the configured source, because nothing here goes looking.
    """
    try:
        document = json.loads(body)
    except ValueError:
        return None
    if not isinstance(document, dict):
        return None
    tag = cast(dict[str, object], document).get(ASKED_TAG)
    return tag if isinstance(tag, str) and tag else None


def elsewhere(origin: str, host: str) -> bool:
    """Whether the page that asked is on some origin other than the one the
    request was addressed to.

    **The host and nothing else.** The door terminates TLS and the face is
    behind it (ADR-0042, ADR-0004), so a page served over `https` asks a face
    spoken to over plain HTTP: the scheme a browser names is never the scheme
    this is reached on, and a port the door answered on is not the port this
    binds. What the two can be held to is the name they share, which is the
    box's `dccex` label.

    **A request with no origin on it is not a page from another one.** An
    origin is what a browser attaches, and holding a page to what its browser
    says is the whole of what this is: `curl` on the box names none, and
    neither does a browser reading the same origin it is on. What limits the
    rest is the LAN (ADR-0042).
    """
    return bool(origin) and urlsplit(origin).netloc != host


class Face:
    """What the mirror answers, and the configuration it answers out of.

    Constructed with the source of releases the app was started with, with
    what fetches a URL, which the suite substitutes so that nothing in the
    gate reaches the release API, and with what writes a release onto the
    station, which is the app that holds the device.

    The flasher has no default, because there is no sensible one: a face
    served without the thing that holds the cable would answer a page that
    everything was fine and write nothing.
    """

    def __init__(
        self,
        releases: str = RELEASES,
        *,
        fetch: Fetch = fetch,
        flasher: Writes,
    ) -> None:
        self._releases = releases
        self._fetch = fetch
        self._flasher = flasher

    async def answer(
        self,
        method: str,
        path: str,
        body: bytes,
        *,
        origin: str = "",
        host: str = "",
    ) -> Answered:
        """One request answered: the method, the path as it arrived, the bytes
        that came with it, and who it came from — the origin of the page that
        asked, where a browser named one, and the origin it was addressed to.

        The path arrives whole, query string and all, and the query is split
        off and dropped here rather than somewhere a reader has to go and
        check: this is the function that would have to read a source out of a
        request for one to redirect the face, and it does not. The door's
        prefix is already off it: what the face answers is `/releases` and
        `/flash`, and a prefix that arrived is a path this does not answer
        (ADR-0004).

        **A page from another origin is refused before anything is routed**,
        because what it asked for does not matter: a face is private to its
        app and is not somewhere else to get at the command station.

        The body is read by one route, which is the flash: it names the tag to
        write and nothing else (#13).
        """
        if elsewhere(origin, host):
            return refused(
                HTTPStatus.FORBIDDEN,
                f"the mirror's face is the page's at {host},"
                f" and {origin} is somewhere else",
            )
        asked = urlsplit(path).path
        if asked == RELEASES_PATH:
            if method != "GET":
                return refused(
                    HTTPStatus.METHOD_NOT_ALLOWED,
                    f"{asked} is read with GET, and this was {method}",
                )
            return await self._carried()
        if asked == FLASH_PATH:
            if method != "POST":
                return refused(
                    HTTPStatus.METHOD_NOT_ALLOWED,
                    f"{asked} is asked for with POST, and this was {method}",
                )
            return await self._writes(body)
        return refused(
            HTTPStatus.NOT_FOUND, f"the mirror's face does not answer {asked}"
        )

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

    async def _writes(self, body: bytes) -> Answered:
        """A named release written onto the command station, and the caller
        told what happened.

        **This waits for the flash**, which is minutes of esptool with a
        timeout of its own: what a caller asked is whether the station now
        runs that build, and esptool exiting non-zero is not knowable before
        esptool has run. The mirror goes on mirroring throughout — the flash
        is a task on this loop and the fan-out is another — and what the
        clients on 2560 see is the device being away, which is what they
        already get when the cable is out (station.py).

        **Nothing here guards the railroad.** This face cannot read the run
        state or the track row; whether it is safe to reset the station under
        a moving train is the operator's, by way of the page that sequences
        it (ADR-0006). The mirror checks nothing, as it never has.
        """
        tag = named(body)
        if tag is None:
            return refused(
                HTTPStatus.BAD_REQUEST,
                f'a flash names the release to write as {{"{ASKED_TAG}": "…"}},'
                " and this named none",
            )
        wrote = await self._flasher.wanted(tag)
        if wrote.refusal is None:
            return Answered(HTTPStatus.OK, {FLASHED: tag})
        return refused(STATUS[wrote.refusal], wrote.said)


def refused(status: HTTPStatus, reason: str) -> Answered:
    """A status and the sentence that goes with it.

    One field and one sentence: what is on the other end is a page, and a
    caller that cannot say what went wrong makes a person go and read a log on
    a box (ADR-0050).
    """
    return Answered(status, {REASON: reason})


class Asked(NamedTuple):
    """What a request says before its body: the method, the path it names as
    it was written, how many bytes of body it says are coming, the origin of
    the page that asked where a browser named one, and the origin it was
    addressed to."""

    method: str
    path: str
    length: int
    origin: str = ""
    host: str = ""


def requested(head: bytes) -> Asked | None:
    """What a request head asks for, or None where it is not a request.

    The head is read and nothing else of HTTP is: the method, the target, the
    length of the body, and the two fields that say who asked and where they
    asked it — the origin a browser attaches to a page's request, and the
    origin the request was addressed to, which the door passes on as the label
    it answered for (ADR-0004). This is a face on a private origin behind the
    door, spoken to by one page (ADR-0002), so the parts of the protocol a
    general server owes the world — negotiation, encodings, a connection kept
    open for the next request — are parts this would carry without ever being
    asked for them.
    """
    lines = head.decode("latin-1").split(CRLF)
    asked = lines[0].split(" ")
    if len(asked) != 3 or not asked[2].startswith("HTTP/"):
        return None
    said: dict[str, str] = {}
    for line in lines[1:]:
        name, found, value = line.partition(":")
        if not found:
            continue
        field = name.strip().lower()
        if field == LENGTH and field in said:
            # Two lengths are two answers to how much body is coming, and a
            # reader that took one of them would be choosing which of them it
            # and whatever passed the request on agree about. It is not a
            # request this face reads.
            return None
        said[field] = value.strip()
    length = 0
    if LENGTH in said:
        try:
            length = int(said[LENGTH])
        except ValueError:
            return None
        if length < 0:
            return None
    return Asked(
        asked[0], asked[1], length, said.get(ORIGIN, ""), said.get(ADDRESSED, "")
    )


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
        #
        # The one handler an abort does not end is one waiting out a flash it
        # asked for, which is waiting on the station and not on the socket.
        # That wait is the one the app makes next anyway — it does not end in
        # the middle of a flash (`__main__.mirroring`) — and the port is given
        # back above it either way.
        for writer in tuple(self._asking):
            writer.transport.abort()
        if server is not None:
            await server.wait_closed()

    async def _asked(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """One request answered, and the connection ended either way.

        **What `patience_s` bounds is the caller and not the answer.** A
        caller that opened a connection and said nothing, or that is not
        taking what it asked for, is not something the process that holds the
        command station waits on for ever. How long the answering itself takes
        is a different question with a different bound: a flash is minutes of
        esptool with a timeout of its own (firmware.py), and a face that timed
        its own answer out would leave the page that asked with a closed
        socket and a station that was written anyway.
        """
        self._asking.add(writer)
        try:
            await self._exchange(reader, writer)
        except (TimeoutError, OSError, asyncio.IncompleteReadError):
            writer.transport.abort()
        finally:
            self._asking.discard(writer)
            writer.close()

    async def _exchange(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        answered = await self._answered(reader)
        if answered.status >= HTTPStatus.INTERNAL_SERVER_ERROR:
            # The one answer worth a line on the box, and the reason it is:
            # what went wrong is not the caller's doing, and the caller is a
            # page that may be nobody's at the moment. What the face refuses a
            # caller for is the caller's own to read (ADR-0050).
            self._log(f"face: {answered.body.get(REASON, answered.status.phrase)}")
        await asyncio.wait_for(self._taken(writer, answered), self._patience_s)

    async def _taken(self, writer: asyncio.StreamWriter, answered: Answered) -> None:
        """The answer written and the connection ended, for as long as the
        caller's patience allows: one that has stopped reading is let go of
        rather than waited on."""
        writer.write(response(answered))
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    async def _answered(self, reader: asyncio.StreamReader) -> Answered:
        """The request read off the connection, and routing's answer to it.

        The reading is what the caller is given `patience_s` for; the routing
        that follows it is given as long as it takes, because what it may be
        doing is writing the command station.

        What a request is not is a status too: a head longer than this reads,
        a first line that is not a request, and a body larger than a face
        asked questions by a page has any use for.
        """
        try:
            head = await asyncio.wait_for(reader.readuntil(HEAD_END), self._patience_s)
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
        body = (
            await asyncio.wait_for(reader.readexactly(asked.length), self._patience_s)
            if asked.length
            else b""
        )
        return await self._face.answer(
            asked.method, asked.path, body, origin=asked.origin, host=asked.host
        )

    def _serving(self) -> asyncio.Server:
        if self._server is None:
            raise RuntimeError("the face is not served")
        return self._server
