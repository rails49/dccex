"""Tests at the face seam, with no socket and no release API.

The face is two things and they are tested as two. **Routing** is a function
of a method, a path and a body, and what it answers is a status and a body —
so every question about what the face says is asked of `Face.answer` directly,
with what fetches a URL injected, and none of those tests opens a socket or
reaches a network. **The server** is the port that carries it, and what is
asserted of it is that it is handed back unstarted, that a request on it gets
the answer routing gave, that serving it leaves the mirror's own port and the
device alone, and — for the one route whose answer is not the end of the
connection — that the station's bytes ride it both ways (#14).

Nothing in the gate reaches the release API (docs/dccex_usb/README.md), so the
source here is a fake that answers from a dict, and the URLs are on a TLD that
resolves nowhere in case that ever stops being true. Nothing in it writes a
command station either: what a flash does to a device is `test_firmware.py`'s,
so the flasher here is usually a stand-in that says what became of a gesture
and never touches a cable. The one test that wires the real one up gives it a
pty and a fake esptool, as that file does.
"""

import asyncio
import contextlib
import json
import os
import socket
import time
from collections.abc import Callable, Sequence
from http import HTTPStatus
from pathlib import Path

import pytest

from dccex_usb.face import (
    CRLF,
    HEAD_END,
    STATUS,
    Answered,
    Ends,
    Face,
    Joins,
    Loopback,
    Server,
    Writes,
    response,
)
from dccex_usb.firmware import Flasher, Ran, Refusal, Wrote
from dccex_usb.framing import MAX_MESSAGE
from dccex_usb.station import READ_SIZE, to_stderr
from dccex_usb.stream import CLOSE, GOING_AWAY, accepted
from tests.dccex_usb.test_firmware import FakeFetch
from tests.dccex_usb.test_station import (
    SHUTDOWN_S,
    Log,
    Pty,
    arriving,
    connect,
    send,
    station,
    wedge,
)
from tests.dccex_usb.test_stream import masked

RELEASES = "https://api.example.invalid/repos/rails49/CommandStation-EX/releases"
ELSEWHERE = "https://api.example.invalid/repos/someone-else/CommandStation-EX/releases"

TAGS = ["v5.6.4-rails49.1", "v5.6.3-rails49.2"]
"""What the source carries, newest first, as the release API lists them."""


def listing(tags: Sequence[str] = TAGS) -> bytes:
    """A releases document, as the API answers the source with one.

    Carrying more than the face reads, because the API does: what is asserted
    is the tags, and a reader that took the whole entry would be taken down by
    whatever the service returned the day it returned something else.
    """
    return json.dumps(
        [
            {
                "tag_name": tag,
                "name": f"CommandStation-EX {tag}",
                "assets": [{"name": "firmware.bin", "digest": "sha256:…"}],
            }
            for tag in tags
        ]
    ).encode()


class Source:
    """The release API, faked: what it answers, and what was asked of it."""

    def __init__(self, answer: bytes | Exception | None = None) -> None:
        self._answer: bytes | Exception = listing() if answer is None else answer
        self.asked: list[str] = []

    async def __call__(self, url: str) -> bytes:
        self.asked.append(url)
        if isinstance(self._answer, Exception):
            raise self._answer
        return self._answer


TAG = TAGS[0]
"""The tag a caller names when it asks for a build to be written."""


class Writing:
    """The flasher, faked: the tags it was asked to write, and what it says
    became of them.

    It is the whole of what the face needs of the thing that holds the device
    (`Writes`), which is why a test can stand in for it: what a flash does to
    a station is `test_firmware.py`'s, and what a caller is told about it is
    this file's.
    """

    def __init__(self, wrote: Wrote | None = None) -> None:
        self._wrote = wrote
        self.asked: list[str] = []

    async def wanted(self, tag: str) -> Wrote:
        self.asked.append(tag)
        if self._wrote is not None:
            return self._wrote
        return Wrote(None, f"flashed '{tag}'")


def asking(tag: str = TAG) -> bytes:
    """A flash asked for, as the page's body says it: a tag and nothing else,
    because a tag is the only thing a caller names (CONTEXT.md)."""
    return json.dumps({"tag": tag}).encode()


def face(
    fetch: Source | None = None,
    releases: str = RELEASES,
    flasher: Writes | None = None,
) -> Face:
    """The face a test asks something of, built in one place.

    What it is configured with is the source of releases, what fetches a URL —
    a fake, because nothing in the gate reaches the release API — and what
    writes a release onto the station, which is a fake for the same reason:
    the gate has no command station and runs no esptool.
    """
    return Face(
        releases,
        fetch=fetch if fetch is not None else Source(),
        flasher=flasher if flasher is not None else Writing(),
    )


def test_a_request_to_the_face_answers_the_tags_the_source_carries() -> None:
    """The whole of what the face is for here: a client asks what releases
    the configured source carries and gets the tags back, so nobody has to
    type one from memory."""
    answered = asyncio.run(face().answer("GET", "/releases", b""))

    assert answered.status == HTTPStatus.OK
    assert answered.body == {"tags": TAGS}


def test_the_releases_are_read_from_the_source_the_face_was_configured_with() -> None:
    source = Source()

    asyncio.run(face(source, ELSEWHERE).answer("GET", "/releases", b""))

    assert source.asked == [ELSEWHERE]


def test_no_request_can_redirect_the_source() -> None:
    """The one thing the LAN's lack of authentication makes dangerous. A
    request that names a source — in the query, in the body, or both — is
    answered out of the configured one, because nothing reads either
    (ADR-0042, firmware.py)."""
    source = Source()

    answered = asyncio.run(
        face(source).answer(
            "GET",
            f"/releases?releases={ELSEWHERE}&source={ELSEWHERE}",
            json.dumps({"releases": ELSEWHERE}).encode(),
        )
    )

    assert source.asked == [RELEASES]
    assert answered.status == HTTPStatus.OK
    assert answered.body == {"tags": TAGS}


def test_a_source_that_cannot_be_reached_is_a_status_and_a_reason() -> None:
    """The release API is somebody else's service: the mirror mirrors what it
    is doing rather than falling over with it."""
    asked = face(Source(OSError("no route to host")))

    answered = asyncio.run(asked.answer("GET", "/releases", b""))

    assert answered.status == HTTPStatus.BAD_GATEWAY
    assert "no route to host" in str(answered.body["reason"])
    assert RELEASES in str(answered.body["reason"])


@pytest.mark.parametrize(
    "said",
    [
        pytest.param(b"<html>not json at all</html>", id="not json"),
        pytest.param(b'{"message": "Not Found"}', id="not a list"),
        pytest.param(
            b'[{"message": "Not Found"}]', id="a list of what is not a release"
        ),
    ],
)
def test_a_source_that_answers_with_nothing_usable_is_a_status_and_a_reason(
    said: bytes,
) -> None:
    asked = face(Source(said))

    answered = asyncio.run(asked.answer("GET", "/releases", b""))

    assert answered.status == HTTPStatus.BAD_GATEWAY
    assert RELEASES in str(answered.body["reason"])


def test_a_source_that_carries_no_releases_yet_is_an_empty_answer() -> None:
    """Not a refusal: the source answered, and what it said is that nothing
    has been published there. A page that said the API was unreachable would
    send somebody looking at the network."""
    asked = face(Source(listing([])))

    answered = asyncio.run(asked.answer("GET", "/releases", b""))

    assert answered.status == HTTPStatus.OK
    assert answered.body == {"tags": []}


def test_a_path_the_face_does_not_answer_is_a_refusal() -> None:
    """A face is private to its app and is not somewhere else to get at the
    railroad (CONTEXT.md): what it does not answer, it says it does not."""
    source = Source()

    answered = asyncio.run(face(source).answer("GET", "/layout", b""))

    assert answered.status == HTTPStatus.NOT_FOUND
    assert source.asked == []


def test_the_releases_are_read_and_not_written() -> None:
    """A tag is chosen among what is published, and publishing is not this
    app's business. What writes one onto the station is #13, and it is not
    this path however it is asked for."""
    source = Source()

    answered = asyncio.run(face(source).answer("POST", "/releases", b""))

    assert answered.status == HTTPStatus.METHOD_NOT_ALLOWED
    assert source.asked == []


# -- the flash ---------------------------------------------------------------


def test_a_named_tag_is_written_onto_the_station_and_the_caller_is_answered() -> None:
    """The gesture the face was written for (#13): the page names a release,
    the app that holds the device writes it, and whoever asked is told what
    happened rather than sent to read a log on the box (ADR-0050)."""
    writing = Writing()

    answered = asyncio.run(face(flasher=writing).answer("POST", "/flash", asking()))

    assert writing.asked == [TAG]
    assert answered.status == HTTPStatus.OK
    assert answered.body == {"flashed": TAG}


def test_every_way_a_flash_is_refused_reaches_the_caller() -> None:
    """Nothing the flasher can turn a gesture down for is missing a status of
    its own: a refusal that fell through to one would tell a page the mirror
    had broken when what happened is that a tag names no release."""
    assert set(STATUS) == set(Refusal)


@pytest.mark.parametrize(
    "refusal, status",
    [
        pytest.param(Refusal.LATEST, HTTPStatus.BAD_REQUEST, id="latest"),
        pytest.param(Refusal.IN_FLIGHT, HTTPStatus.CONFLICT, id="one in flight"),
        pytest.param(
            Refusal.NO_STATION, HTTPStatus.SERVICE_UNAVAILABLE, id="no station"
        ),
        pytest.param(Refusal.NO_RELEASE, HTTPStatus.NOT_FOUND, id="no such release"),
        pytest.param(Refusal.NO_ASSET, HTTPStatus.BAD_GATEWAY, id="no firmware"),
        pytest.param(Refusal.NO_DIGEST, HTTPStatus.BAD_GATEWAY, id="no digest"),
        pytest.param(
            Refusal.NOT_PUBLISHED, HTTPStatus.BAD_GATEWAY, id="not what was published"
        ),
        pytest.param(
            Refusal.TOOL_FAILED, HTTPStatus.INTERNAL_SERVER_ERROR, id="esptool failed"
        ),
        pytest.param(
            Refusal.TOOL_KILLED, HTTPStatus.GATEWAY_TIMEOUT, id="esptool was killed"
        ),
        pytest.param(
            Refusal.RAISED, HTTPStatus.INTERNAL_SERVER_ERROR, id="something raised"
        ),
    ],
)
def test_what_a_flash_was_refused_for_is_a_status_and_a_reason(
    refusal: Refusal, status: HTTPStatus
) -> None:
    """Each of them a status the caller can act on: what it may ask again
    (409), what is the station's doing (503), what is the source's (502), and
    what is a page's own (400). The sentence is the flasher's, whole."""
    said = "the flasher's own sentence"

    answered = asyncio.run(
        face(flasher=Writing(Wrote(refusal, said))).answer("POST", "/flash", asking())
    )

    assert answered.status == status
    assert answered.body == {"reason": said}


@pytest.mark.parametrize(
    "body",
    [
        pytest.param(b"", id="nothing"),
        pytest.param(b"v5.6.4-rails49.1", id="not json"),
        pytest.param(b'["v5.6.4-rails49.1"]', id="not an object"),
        pytest.param(b'{"release": "v5.6.4-rails49.1"}', id="names no tag"),
        pytest.param(b'{"tag": ""}', id="an empty tag"),
        pytest.param(b'{"tag": 5}', id="a tag that is not a name"),
    ],
)
def test_a_body_that_names_no_tag_is_refused_before_the_device(body: bytes) -> None:
    """A tag is the one thing a flash is asked with, and it is read the way a
    payload is read — one field, and every shape it is not is a refusal —
    because it arrives from a LAN with no authentication on it (ADR-0042)."""
    writing = Writing()

    answered = asyncio.run(face(flasher=writing).answer("POST", "/flash", body))

    assert answered.status == HTTPStatus.BAD_REQUEST
    assert answered.body["reason"]
    assert writing.asked == []


def test_a_flash_is_asked_for_and_not_read() -> None:
    """The station is written by asking, so `GET /flash` is not a way to see
    what is being written: there is nothing to read here, and a page that
    reloaded one would write the station again."""
    writing = Writing()

    answered = asyncio.run(face(flasher=writing).answer("GET", "/flash", asking()))

    assert answered.status == HTTPStatus.METHOD_NOT_ALLOWED
    assert writing.asked == []


def test_no_request_can_redirect_the_source_a_flash_is_written_from() -> None:
    """The same rule as the releases, on the path where it costs the most: a
    body that names a source is written out of the configured one, because
    nothing reads one. A source on the wire would let anyone on the wifi have
    the station run an arbitrary binary (ADR-0042, firmware.py)."""
    writing = Writing()

    answered = asyncio.run(
        face(flasher=writing).answer(
            "POST",
            f"/flash?releases={ELSEWHERE}",
            json.dumps({"tag": TAG, "releases": ELSEWHERE}).encode(),
        )
    )

    assert writing.asked == [TAG]
    assert answered.status == HTTPStatus.OK


# -- the stream --------------------------------------------------------------

KEY = "dGhlIHNhbXBsZSBub25jZQ=="
"""What a browser names when it opens a stream. RFC 6455's own example, so the
token that answers it is the standard's and not this suite's."""


def test_a_page_opening_the_stream_is_answered_with_the_token_it_asked_for() -> None:
    """The gesture #14 adds: the page asks for the station's conversation and
    the face says it may have it. What rides on it afterwards is not routing's
    — this answer is the last thing about the connection that is a request."""
    answered = asyncio.run(face().answer("GET", "/stream", b"", key=KEY))

    assert answered.status == HTTPStatus.SWITCHING_PROTOCOLS
    assert answered.upgrade == accepted(KEY)


def test_the_stream_is_opened_by_upgrading_and_fetched_no_other_way() -> None:
    """There is nothing at this path to read: what it carries is what the
    station is saying now, and a caller that asked for it as a page asked for
    a thing that does not exist."""
    answered = asyncio.run(face().answer("GET", "/stream", b""))

    assert answered.status == HTTPStatus.BAD_REQUEST
    assert answered.body["reason"]
    assert not answered.upgrade


@pytest.mark.parametrize(
    "method", [pytest.param("POST", id="posted"), pytest.param("PUT", id="put")]
)
def test_the_stream_is_opened_and_not_written_to(method: str) -> None:
    """What a page types reaches the station on the stream it already has, and
    not as a request: the mirror's port is what a message is written to, and a
    request that carried one would be a second way in (ADR-0007)."""
    answered = asyncio.run(face().answer(method, "/stream", b"<t 3 50 1>", key=KEY))

    assert answered.status == HTTPStatus.METHOD_NOT_ALLOWED
    assert not answered.upgrade


def test_an_answer_that_is_not_an_upgrade_says_so_on_the_wire() -> None:
    """The two shapes an answer has: a status with a JSON body, or the upgrade
    that hands the connection over. A caller reading one as the other is a page
    holding a socket nobody is going to talk on."""
    fetched = response(Answered(HTTPStatus.OK, {"tags": TAGS}))
    opened = response(Answered(HTTPStatus.SWITCHING_PROTOCOLS, {}, accepted(KEY)))

    assert b"Content-Type: application/json" in fetched
    assert b"Connection: close" in fetched
    assert b"101 Switching Protocols" in opened
    assert accepted(KEY).encode() in opened
    assert b"Content-Length" not in opened


# -- the door's side ---------------------------------------------------------

LABEL = "dccex.example.invalid"
"""The box's `dccex` label: the one origin the page and the face share."""

PAGE = f"https://{LABEL}"
"""What a browser sends as the origin of a page served at that label. It is
`https` where the face is spoken to over plain HTTP, because the door
terminates TLS and the face is behind it (ADR-0004)."""

ELSEWHERE_ORIGIN = "https://somebody-else.example.invalid"


def test_a_page_on_the_face_s_own_origin_is_answered() -> None:
    """The page the face exists for: it is served at the label, it asks under
    the prefix, and its browser says so."""
    answered = asyncio.run(
        face().answer("GET", "/releases", b"", origin=PAGE, host=LABEL)
    )

    assert answered.status == HTTPStatus.OK
    assert answered.body == {"tags": TAGS}


@pytest.mark.parametrize(
    "origin",
    [
        pytest.param(ELSEWHERE_ORIGIN, id="another label"),
        pytest.param("http://" + LABEL + ".example.invalid", id="a longer name"),
        pytest.param("null", id="no origin a browser will name"),
    ],
)
def test_a_page_from_another_origin_is_refused(origin: str) -> None:
    """A face is private to its app and is on the page's origin (ADR-0004).
    A page somewhere else asking this app about the command station is
    refused before it is routed, so what it asks for does not matter."""
    source = Source()

    answered = asyncio.run(
        face(source).answer("GET", "/releases", b"", origin=origin, host=LABEL)
    )

    assert answered.status == HTTPStatus.FORBIDDEN
    assert LABEL in str(answered.body["reason"])
    assert source.asked == []


def test_a_page_from_another_origin_may_not_open_the_stream() -> None:
    """The route the origin check matters most on. A browser does not ask
    before opening a stream — there is no preflight on one — so the origin it
    names is the whole of what keeps a page somewhere else off the command
    station's conversation (ADR-0004 d.4)."""
    answered = asyncio.run(
        face().answer(
            "GET", "/stream", b"", origin=ELSEWHERE_ORIGIN, host=LABEL, key=KEY
        )
    )

    assert answered.status == HTTPStatus.FORBIDDEN
    assert not answered.upgrade


def test_a_caller_that_names_no_origin_is_not_a_page_from_another_one() -> None:
    """`curl` on the box, and a page's own browser on a same-origin read: an
    origin is what a browser attaches, and holding a page to one is the whole
    of what this check is. What limits the rest is the LAN (ADR-0042)."""
    answered = asyncio.run(face().answer("GET", "/releases", b"", host=LABEL))

    assert answered.status == HTTPStatus.OK


UNREADABLE = "//[v"
"""A request target that `urlsplit` cannot read: a host that opens an IPv6
literal and never closes it. A browser does not send this; something pointed
at the port by hand does."""


@pytest.mark.parametrize(
    "asked",
    [
        pytest.param(UNREADABLE, id="an unclosed IPv6 literal"),
        pytest.param("http://[::1", id="a whole URL with one"),
    ],
)
def test_a_target_that_cannot_be_read_is_refused_rather_than_dropped(
    asked: str,
) -> None:
    """A malformed target is a bad request and is answered as one. Reading it
    is `urlsplit`'s, which raises on a host it cannot parse rather than
    returning something; left to escape, that ends the connection with no
    answer on it at all and a traceback on the box."""
    source = Source()

    answered = asyncio.run(face(source).answer("GET", asked, b""))

    assert answered.status == HTTPStatus.BAD_REQUEST
    assert source.asked == []


def test_an_origin_that_cannot_be_read_is_somewhere_else() -> None:
    """An origin is held to the host it names, so one that cannot be read
    names no host and is not this one. It is refused like any other page from
    somewhere else — the direction that is safe when the check cannot be
    made — rather than raising out of the routing."""
    source = Source()

    answered = asyncio.run(
        face(source).answer("GET", "/releases", b"", origin="http://[::1", host=LABEL)
    )

    assert answered.status == HTTPStatus.FORBIDDEN
    assert source.asked == []


def test_the_prefix_is_stripped_before_the_face_sees_it() -> None:
    """The face's address is a path prefix on the page's origin, and the door
    takes it off on the way through (ADR-0004). So the face answers
    `/releases` and not the address a browser types: a prefix arriving here
    is a door that did not strip it, which is a path this does not answer."""
    source = Source()

    answered = asyncio.run(face(source).answer("GET", "/dccex-usb/releases", b""))

    assert answered.status == HTTPStatus.NOT_FOUND
    assert source.asked == []


PATIENCE_S = 2.0
TIMEOUT_S = 5.0


def request(
    method: str = "GET",
    target: str = "/releases",
    body: bytes = b"",
    origin: str = "",
) -> bytes:
    """One HTTP request, as the UI's page makes it and as the door passes it
    on: the label it was addressed to, and the origin of the page that asked
    where a browser attached one."""
    head = (
        f"{method} {target} HTTP/1.1\r\n"
        f"Host: {LABEL}\r\n"
        + (f"Origin: {origin}\r\n" if origin else "")
        + f"Content-Length: {len(body)}\r\n"
        "\r\n"
    )
    return head.encode() + body


async def ask(port: int, asked: bytes = request()) -> tuple[int, object]:
    """Ask the face over TCP and read the whole answer back.

    Read to end-of-file rather than by the length it reports: what is asserted
    is what the face said, and a reader that trusted the header could not
    notice a body that disagreed with it.
    """
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    try:
        writer.write(asked)
        await writer.drain()
        answered = await reader.read()
    finally:
        writer.close()
        await writer.wait_closed()
    head, _, body = answered.partition(b"\r\n\r\n")
    status = int(head.split(b" ")[1])
    return status, json.loads(body)


class Unjoined:
    """What joins the mirror's port here, and never does. A test that wants a
    stream says how the mirror is reached, and every other one is about a face
    that is asked a question and answers it."""

    async def __call__(self) -> Ends:
        raise AssertionError("the mirror's port was joined")


def served(
    asked: Face | None = None,
    *,
    joins: Joins | None = None,
    log: Callable[[str], None] = to_stderr,
    patience_s: float = PATIENCE_S,
) -> Server:
    """The face on a port the OS chooses, built in one place.

    What a test names is what it is about — a face configured its own way, how
    the mirror is joined for a monitor, the log it reads, the patience it runs
    out of — and everything else is what the app is served with. The port is
    always the OS's: a suite that bound the face's own would pass or fail on
    what else the machine is running.
    """
    return Server(
        asked if asked is not None else face(),
        0,
        joins=joins if joins is not None else Unjoined(),
        log=log,
        patience_s=patience_s,
    )


def test_the_server_is_handed_back_unstarted() -> None:
    """Constructing one binds nothing: a test starts it, asks it the port the
    OS chose, and stops it, which is the split `Station` is driven by."""

    async def started_and_stopped() -> None:
        server = served()
        with pytest.raises(RuntimeError):
            assert server.port

        await server.start()
        port = server.port
        assert port > 0
        status, _ = await ask(port)
        assert status == HTTPStatus.OK

        await server.close()
        with pytest.raises(OSError):
            await asyncio.open_connection("127.0.0.1", port)

    asyncio.run(asyncio.wait_for(started_and_stopped(), TIMEOUT_S))


def test_a_request_on_the_port_is_answered_with_what_routing_said() -> None:
    async def asked() -> tuple[int, object]:
        server = served()
        await server.start()
        try:
            return await ask(server.port)
        finally:
            await server.close()

    status, body = asyncio.run(asyncio.wait_for(asked(), TIMEOUT_S))

    assert status == HTTPStatus.OK
    assert body == {"tags": TAGS}


@pytest.mark.parametrize(
    "asked, status",
    [
        pytest.param(
            request(target="/layout"), HTTPStatus.NOT_FOUND, id="no such path"
        ),
        pytest.param(
            request(method="POST", body=b'{"tag": "v5.6.4-rails49.1"}'),
            HTTPStatus.METHOD_NOT_ALLOWED,
            id="a method with a body",
        ),
        pytest.param(b"hello?\r\n\r\n", HTTPStatus.BAD_REQUEST, id="not a request"),
        pytest.param(
            b"GET /releases HTTP/1.1\r\nContent-Length: 0\r\nContent-Length: 7\r\n\r\n",
            HTTPStatus.BAD_REQUEST,
            id="two answers to how much body is coming",
        ),
        pytest.param(
            request(origin=ELSEWHERE_ORIGIN),
            HTTPStatus.FORBIDDEN,
            id="a page from another origin",
        ),
    ],
)
def test_what_the_face_will_not_answer_comes_back_as_a_status_and_a_reason(
    asked: bytes, status: int
) -> None:
    """Including the request with a body: it is read off the connection
    before the answer goes back, so a caller gets its status rather than a
    connection closed under what it was still sending."""

    async def refused() -> tuple[int, object]:
        server = served()
        await server.start()
        try:
            return await ask(server.port, asked)
        finally:
            await server.close()

    got, body = asyncio.run(asyncio.wait_for(refused(), TIMEOUT_S))

    assert got == status
    assert isinstance(body, dict) and body["reason"]


def test_the_page_s_own_origin_arrives_on_the_head_and_is_answered() -> None:
    """The other half of the refusal above: what the door passes on is the
    label it answered on and the origin the browser named, and a page on that
    label is the caller the face is for."""

    async def asked() -> tuple[int, object]:
        server = served()
        await server.start()
        try:
            return await ask(server.port, request(origin=PAGE))
        finally:
            await server.close()

    status, body = asyncio.run(asyncio.wait_for(asked(), TIMEOUT_S))

    assert status == HTTPStatus.OK
    assert body == {"tags": TAGS}


IMPATIENT_S = 0.05
"""A patience small enough that a flash outlasts it here the way a real one
outlasts ten seconds."""

WRITES_S = IMPATIENT_S * 5


class Slow:
    """A flasher that takes longer than the caller's patience, which every
    real one does: esptool is a minute or two."""

    def __init__(self, takes_s: float) -> None:
        self._takes_s = takes_s

    async def wanted(self, tag: str) -> Wrote:
        await asyncio.sleep(self._takes_s)
        return Wrote(None, f"flashed '{tag}'")


def test_a_flash_is_answered_however_long_the_station_takes() -> None:
    """What a request is given is the caller's time and not the station's. A
    flash is minutes of esptool with a timeout of its own (firmware.py), and a
    face that timed its own answer out would leave the page that asked with a
    closed socket and a station that was written anyway — the one outcome
    nobody can say anything about afterwards."""

    async def asked() -> tuple[int, object]:
        server = served(face(flasher=Slow(WRITES_S)), patience_s=IMPATIENT_S)
        await server.start()
        try:
            return await ask(
                server.port, request(method="POST", target="/flash", body=asking())
            )
        finally:
            await server.close()

    status, body = asyncio.run(asyncio.wait_for(asked(), TIMEOUT_S))

    assert status == HTTPStatus.OK
    assert body == {"flashed": TAG}


def test_a_caller_that_says_nothing_is_let_go_of() -> None:
    """The other half of that: what the patience is for is a caller that
    opened a connection and never asked anything, which the process holding
    the command station does not wait on for as long as the railroad runs."""

    async def waited() -> bytes:
        server = served(patience_s=IMPATIENT_S)
        await server.start()
        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", server.port)
            try:
                return await reader.read()
            finally:
                writer.close()
                with contextlib.suppress(ConnectionResetError):
                    await writer.wait_closed()
        finally:
            await server.close()

    assert asyncio.run(asyncio.wait_for(waited(), TIMEOUT_S)) == b""


def test_a_source_that_cannot_be_reached_is_said_on_the_box_as_well() -> None:
    """The caller is told, and so is whoever is reading the app's log: a
    release API that is away is not the caller's doing, and the page that
    asked may be nobody's at the moment (ADR-0050). What the face refuses a
    caller for stays the caller's own to read."""
    said: list[str] = []

    async def asked() -> tuple[int, object]:
        server = served(face(Source(OSError("no route to host"))), log=said.append)
        await server.start()
        try:
            return await ask(server.port)
        finally:
            await server.close()

    status, _ = asyncio.run(asyncio.wait_for(asked(), TIMEOUT_S))

    assert status == HTTPStatus.BAD_GATEWAY
    assert [line for line in said if "no route to host" in line]


def test_what_the_face_refuses_a_caller_for_is_not_said_on_the_box() -> None:
    said: list[str] = []

    async def asked() -> tuple[int, object]:
        server = served(log=said.append)
        await server.start()
        try:
            return await ask(server.port, request(target="/layout"))
        finally:
            await server.close()

    status, _ = asyncio.run(asyncio.wait_for(asked(), TIMEOUT_S))

    assert status == HTTPStatus.NOT_FOUND
    assert said == []


# -- the wiring --------------------------------------------------------------


def test_a_tag_asked_for_on_the_face_is_written_by_the_mirror_that_holds_it() -> None:
    """The whole of it through one socket, with a pty for the command station:
    a page asks the face for a named release, the mirror lets the device go,
    esptool is run on it, the mirror takes it back, and the caller is answered.

    What runs is a fake, because esptool cannot write a pty and nothing in the
    gate may need a command station — and it is what says the device was away
    while it ran, which is the one ordering that can leave the railroad with a
    closed port and no firmware (ADR-0065).
    """

    async def scenario() -> None:
        log = Log()
        cable = Pty()
        mirror = station(cable.path, log)
        held: list[bool] = []

        async def runner(command: Sequence[str], timeout_s: float) -> Ran:
            held.append(mirror.held)
            return Ran(0, "")

        flasher = Flasher(mirror, RELEASES, fetch=FakeFetch(), runner=runner, log=log)
        streamed = served(face(flasher=flasher))
        await mirror.start()
        await streamed.start()
        try:
            await log.wait_for("serial open")

            status, body = await ask(
                streamed.port, request(method="POST", target="/flash", body=asking())
            )

            assert (status, body) == (HTTPStatus.OK, {"flashed": TAG})
            assert held == [False], "esptool ran with the mirror on the port"
            await log.wait_for_count("serial open", 2)
            assert mirror.held, "the mirror did not take the device back"
        finally:
            await streamed.close()
            await mirror.close()
            cable.close()

    asyncio.run(asyncio.wait_for(scenario(), TIMEOUT_S))


def test_serving_the_face_disturbs_neither_the_device_nor_the_mirror_s_port() -> None:
    """The face beside the real mirror, with a pty for the command station.

    A face is one more thing in the process that holds the railroad's one
    serial device, so what is asserted here is everything it does not do: it
    is a port of its own, the station's conversation goes on through the
    mirror's port both ways while the face is answering, and the device is
    still held afterwards.
    """

    async def scenario() -> None:
        log = Log()
        cable = Pty()
        mirror = station(cable.path, log)
        streamed = served()
        await mirror.start()
        await streamed.start()
        try:
            await log.wait_for("serial open")
            assert streamed.port != mirror.port

            status, body = await ask(streamed.port)
            assert (status, body) == (HTTPStatus.OK, {"tags": TAGS})

            reader, writer = await connect(mirror)
            await send(writer, b"<s>")
            assert await arriving(cable.master, len(b"<s>")) == b"<s>"
            os.write(cable.master, b"<iDCC-EX>")
            assert await reader.readexactly(len(b"<iDCC-EX>")) == b"<iDCC-EX>"
            assert mirror.held, "the face took the device from the mirror"

            writer.close()
            await writer.wait_closed()
        finally:
            await streamed.close()
            await mirror.close()
            cable.close()

    asyncio.run(asyncio.wait_for(scenario(), TIMEOUT_S))


# -- the monitor's stream ----------------------------------------------------


def upgrade(origin: str = "", target: str = "/stream", key: str = KEY) -> bytes:
    """What a browser sends to open a stream: a request like any other, with
    the key that says what it is opening and the origin of the page it is
    opening from."""
    head = (
        f"GET {target} HTTP/1.1\r\n"
        f"Host: {LABEL}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        "Sec-WebSocket-Version: 13\r\n"
        f"Sec-WebSocket-Key: {key}\r\n" + (f"Origin: {origin}\r\n" if origin else "")
    ) + CRLF
    return head.encode()


class Browser:
    """The monitor's end of a stream, as a browser speaks it.

    Written out here rather than asking the app to frame for the test: what is
    under test is the wire, and a harness that framed with the code it is
    checking could not notice the two agreeing on something no browser does.
    """

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self._reader = reader
        self._writer = writer
        self.heard = bytearray()
        self.goodbye = b""

    @classmethod
    async def opened(
        cls, port: int, origin: str = PAGE, deaf: bool = False
    ) -> "Browser":
        """A page on the face's own origin, with its stream open.

        A deaf one cannot take much unread, the way `connect_deaf` makes one
        on 2560: what the mirror sees is the same client either way — one that
        stops taking bytes — reached in a fraction of the traffic.
        """
        sock = socket.socket()
        if deaf:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2048)
        sock.setblocking(False)
        await asyncio.get_running_loop().sock_connect(sock, ("127.0.0.1", port))
        reader, writer = await asyncio.open_connection(sock=sock)
        writer.write(upgrade(origin))
        await writer.drain()
        head = await reader.readuntil(HEAD_END)
        assert b"101 Switching Protocols" in head, head
        assert accepted(KEY).encode() in head, head
        return cls(reader, writer)

    async def types(self, message: bytes) -> None:
        """One masked frame, as a page typing at the station sends it."""
        self._writer.write(masked(message))
        await self._writer.drain()

    async def frame(self) -> tuple[int, bytes]:
        """The next frame the face sent, and what kind it is."""
        head = await self._reader.readexactly(2)
        assert not head[1] & 0x80, "the face masked what it sent"
        size = head[1] & 0x7F
        if size == 126:
            size = int.from_bytes(await self._reader.readexactly(2), "big")
        return head[0] & 0x0F, await self._reader.readexactly(size)

    async def run(self) -> None:
        """Keep listening until the stream ends, and remember what was said."""
        while True:
            try:
                opcode, payload = await self.frame()
            except (asyncio.IncompleteReadError, ConnectionError):
                return
            if opcode == CLOSE:
                self.goodbye = payload
                return
            self.heard += payload

    async def hears(self, count: int, timeout: float = TIMEOUT_S) -> None:
        deadline = time.monotonic() + timeout
        while len(self.heard) < count:
            if time.monotonic() > deadline:
                raise AssertionError(f"heard {len(self.heard)} bytes, not {count}")
            await asyncio.sleep(0.005)

    def close(self) -> None:
        self._writer.close()


def test_a_page_on_the_stream_is_one_more_client_of_the_mirror() -> None:
    """The whole of #14 through one port, with a pty for the command station.

    A page opens the stream on the same port the face answers its other
    requests on, and what it gets is a client of 2560: every byte the station
    says, in step with a client that dialled the port itself, and what it
    types reaching the device as a whole `<…>` message by the mirror's own
    framing. The port it dialled goes on behaving exactly as it did, with the
    page on the stream and without it.
    """

    async def scenario() -> None:
        log = Log()
        cable = Pty()
        mirror = station(cable.path, log)
        streamed = served(joins=Loopback(mirror))
        await mirror.start()
        await streamed.start()
        watching = None
        try:
            await log.wait_for("serial open")
            reader, writer = await connect(mirror)
            page = await Browser.opened(streamed.port)
            watching = asyncio.create_task(page.run())
            await log.wait_for_count("client connected", 2)

            os.write(cable.master, b"<iDCC-EX V-5.4.16 G-9db8d0e>")

            said = b"<iDCC-EX V-5.4.16 G-9db8d0e>"
            assert await reader.readexactly(len(said)) == said
            await page.hears(len(said))
            assert bytes(page.heard) == said

            # And what the page types reaches the device whole, across two
            # frames, which is how a browser may split anything it sends.
            await page.types(b"<t 3 ")
            await page.types(b"50 1>")
            assert await arriving(cable.master, len(b"<t 3 50 1>")) == b"<t 3 50 1>"

            # The client that dialled 2560 is unaffected, both ways.
            await send(writer, b"<s>")
            assert await arriving(cable.master, len(b"<s>")) == b"<s>"

            # And the face is still a face: one port carries the upgrade and
            # the requests that are not one (ADR-0004 d.3).
            assert await ask(streamed.port) == (HTTPStatus.OK, {"tags": TAGS})

            page.close()
            writer.close()
        finally:
            if watching is not None:
                watching.cancel()
            await streamed.close()
            await mirror.close()
            cable.close()

    asyncio.run(asyncio.wait_for(scenario(), TIMEOUT_S))


def test_a_stream_asked_for_before_the_mirror_serves_is_refused_with_503() -> None:
    """The window an app has on the way up and on the way down: the face is
    answering and the mirror's port is not there. `Station.port` says so by
    raising, and the caller is told the station is away — an answer it can
    read — rather than having its connection closed on a traceback.

    `mirroring` only notices a station that has stopped within its own period,
    so this window is real on the way down and not only at startup.
    """
    log = Log()

    async def asked() -> tuple[int, object]:
        mirror = station(os.devnull, log)
        # Never started: `port` raises, which is what a stream asked for in
        # the window between the face serving and the mirror doing so meets.
        server = served(joins=Loopback(mirror))
        await server.start()
        try:
            return await ask(server.port, upgrade())
        finally:
            await server.close()

    status, body = asyncio.run(asyncio.wait_for(asked(), TIMEOUT_S))

    assert status == HTTPStatus.SERVICE_UNAVAILABLE
    assert isinstance(body, dict) and body["reason"]


def test_a_page_that_stops_reading_is_cut_off_on_the_mirror_s_own_rule() -> None:
    """A monitor that has stopped reading is a client of 2560 that has stopped
    reading: nothing is buffered for it here, so what lets go of it is the
    mirror's own bound on how far behind a client may fall, and the mirror's
    own line says so (`station.py`, ADR-0007)."""

    async def scenario() -> None:
        log = Log()
        cable = Pty()
        mirror = station(cable.path, log)
        streamed = served(joins=Loopback(mirror))
        await mirror.start()
        await streamed.start()
        try:
            page = await Browser.opened(streamed.port, deaf=True)
            await log.wait_for("serial open")
            await wedge(cable)

            assert "too far behind" in await log.wait_for("client disconnected")
            page.close()
        finally:
            await streamed.close()
            await mirror.close()
            cable.close()

    asyncio.run(asyncio.wait_for(scenario(), TIMEOUT_S))


def test_an_outage_disconnects_a_page_alongside_the_clients_on_2560(
    tmp_path: Path,
) -> None:
    """The grace is the outage's and the stream is in it. A client cannot tell
    an away device from a quiet one, and this stream has no way to tell it
    either: the connection closing is the whole signal, and a page gets it as
    a stream that closed and says why (control ADR-0066)."""

    async def scenario() -> None:
        log = Log()
        mirror = station(str(tmp_path / "dccex"), log)
        streamed = served(joins=Loopback(mirror))
        await mirror.start()
        await streamed.start()
        try:
            dialled, writer = await connect(mirror)
            page = await Browser.opened(streamed.port)
            watching = asyncio.create_task(page.run())

            assert await asyncio.wait_for(dialled.read(READ_SIZE), TIMEOUT_S) == b""
            await asyncio.wait_for(watching, TIMEOUT_S)

            assert page.goodbye[:2] == GOING_AWAY.to_bytes(2, "big")
            assert "disconnecting" in await log.wait_for("device still away")
            page.close()
            writer.close()
        finally:
            await streamed.close()
            await mirror.close()

    asyncio.run(asyncio.wait_for(scenario(), TIMEOUT_S))


def test_what_a_page_types_is_framed_by_the_mirror_s_rule_and_capped_by_it() -> None:
    """The cap on a message is the mirror's and reaches the page through it.

    A frame carries 64 KiB and a message the station answers to is a kilobyte,
    so the two are not the same bound and only one of them is about `<…>`: a
    page that types past `framing.MAX_MESSAGE` without its `>` has that
    message discarded, and the bytes after it dropped until the next `<`,
    exactly as a client on 2560 does. Nothing in the stream knows this rule.
    """

    async def scenario() -> None:
        log = Log()
        cable = Pty()
        mirror = station(cable.path, log)
        streamed = served(joins=Loopback(mirror))
        await mirror.start()
        await streamed.start()
        try:
            await log.wait_for("serial open")
            page = await Browser.opened(streamed.port)

            await page.types(b"<" + b"t" * (MAX_MESSAGE + 1))
            await page.types(b"><a 12 1>")

            assert await arriving(cable.master, len(b"<a 12 1>")) == b"<a 12 1>"
            page.close()
        finally:
            await streamed.close()
            await mirror.close()
            cable.close()

    asyncio.run(asyncio.wait_for(scenario(), TIMEOUT_S))


def test_the_app_going_down_lets_go_of_a_page_on_the_stream() -> None:
    """A stream is open for as long as somebody is watching the railroad, so
    the app ending is what ends it. Closing the face aborts the connection the
    way the mirror aborts a client's, both directions come back, and the
    client this monitor had on the mirror's port goes with them — a shutdown
    that waited on a page would hold the device it is trying to let go of
    (`station.py`, `__main__.mirroring`)."""

    async def scenario() -> None:
        log = Log()
        cable = Pty()
        mirror = station(cable.path, log)
        streamed = served(joins=Loopback(mirror))
        await mirror.start()
        await streamed.start()
        try:
            await log.wait_for("serial open")
            page = await Browser.opened(streamed.port)
            watching = asyncio.create_task(page.run())
            await log.wait_for("client connected")

            await asyncio.wait_for(streamed.close(), SHUTDOWN_S)

            await asyncio.wait_for(watching, TIMEOUT_S)
            # And the client it had on the mirror's port left with it, which
            # the mirror says in the line every client leaves by.
            await log.wait_for("client disconnected")
            page.close()
        finally:
            await streamed.close()
            await mirror.close()
            cable.close()

    asyncio.run(asyncio.wait_for(scenario(), TIMEOUT_S))
