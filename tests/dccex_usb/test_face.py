"""Tests at the face seam, with no socket and no release API.

The face is two things and they are tested as two. **Routing** is a function
of a method, a path and a body, and what it answers is a status and a body —
so every question about what the face says is asked of `Face.answer` directly,
with what fetches a URL injected, and none of those tests opens a socket or
reaches a network. **The server** is the port that carries it, and what is
asserted of it is that it is handed back unstarted, that a request on it gets
the answer routing gave, and that serving it leaves the mirror's own port and
the device alone.

Nothing in the gate reaches the release API (docs/dccex_usb/README.md), so the
source here is a fake that answers from a dict, and the URLs are on a TLD that
resolves nowhere in case that ever stops being true.
"""

import asyncio
import json
import os
from collections.abc import Sequence
from http import HTTPStatus

import pytest

from dccex_usb.face import Face, Server
from tests.dccex_usb.test_station import Log, Pty, arriving, connect, send, station

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


def test_a_request_to_the_face_answers_the_tags_the_source_carries() -> None:
    """The whole of what the face is for here: a client asks what releases
    the configured source carries and gets the tags back, so nobody has to
    type one from memory."""
    face = Face(RELEASES, fetch=Source())

    answered = asyncio.run(face.answer("GET", "/releases", b""))

    assert answered.status == HTTPStatus.OK
    assert answered.body == {"tags": TAGS}


def test_the_releases_are_read_from_the_source_the_face_was_configured_with() -> None:
    source = Source()

    asyncio.run(Face(ELSEWHERE, fetch=source).answer("GET", "/releases", b""))

    assert source.asked == [ELSEWHERE]


def test_no_request_can_redirect_the_source() -> None:
    """The one thing the LAN's lack of authentication makes dangerous. A
    request that names a source — in the query, in the body, or both — is
    answered out of the configured one, because nothing reads either
    (ADR-0042, firmware.py)."""
    source = Source()

    answered = asyncio.run(
        Face(RELEASES, fetch=source).answer(
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
    face = Face(RELEASES, fetch=Source(OSError("no route to host")))

    answered = asyncio.run(face.answer("GET", "/releases", b""))

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
    face = Face(RELEASES, fetch=Source(said))

    answered = asyncio.run(face.answer("GET", "/releases", b""))

    assert answered.status == HTTPStatus.BAD_GATEWAY
    assert RELEASES in str(answered.body["reason"])


def test_a_source_that_carries_no_releases_yet_is_an_empty_answer() -> None:
    """Not a refusal: the source answered, and what it said is that nothing
    has been published there. A page that said the API was unreachable would
    send somebody looking at the network."""
    face = Face(RELEASES, fetch=Source(listing([])))

    answered = asyncio.run(face.answer("GET", "/releases", b""))

    assert answered.status == HTTPStatus.OK
    assert answered.body == {"tags": []}


def test_a_path_the_face_does_not_answer_is_a_refusal() -> None:
    """A face is private to its app and is not somewhere else to get at the
    railroad (CONTEXT.md): what it does not answer, it says it does not."""
    source = Source()

    answered = asyncio.run(Face(RELEASES, fetch=source).answer("GET", "/layout", b""))

    assert answered.status == HTTPStatus.NOT_FOUND
    assert source.asked == []


def test_the_releases_are_read_and_not_written() -> None:
    """A tag is chosen among what is published, and publishing is not this
    app's business. What writes one onto the station is #13, and it is not
    this path however it is asked for."""
    source = Source()

    answered = asyncio.run(
        Face(RELEASES, fetch=source).answer("POST", "/releases", b"")
    )

    assert answered.status == HTTPStatus.METHOD_NOT_ALLOWED
    assert source.asked == []


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
    face = Face(RELEASES, fetch=Source())

    answered = asyncio.run(
        face.answer("GET", "/releases", b"", origin=PAGE, host=LABEL)
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
        Face(RELEASES, fetch=source).answer(
            "GET", "/releases", b"", origin=origin, host=LABEL
        )
    )

    assert answered.status == HTTPStatus.FORBIDDEN
    assert LABEL in str(answered.body["reason"])
    assert source.asked == []


def test_a_caller_that_names_no_origin_is_not_a_page_from_another_one() -> None:
    """`curl` on the box, and a page's own browser on a same-origin read: an
    origin is what a browser attaches, and holding a page to one is the whole
    of what this check is. What limits the rest is the LAN (ADR-0042)."""
    face = Face(RELEASES, fetch=Source())

    answered = asyncio.run(face.answer("GET", "/releases", b"", host=LABEL))

    assert answered.status == HTTPStatus.OK


def test_the_prefix_is_stripped_before_the_face_sees_it() -> None:
    """The face's address is a path prefix on the page's origin, and the door
    takes it off on the way through (ADR-0004). So the face answers
    `/releases` and not the address a browser types: a prefix arriving here
    is a door that did not strip it, which is a path this does not answer."""
    source = Source()

    answered = asyncio.run(
        Face(RELEASES, fetch=source).answer("GET", "/dccex-usb/releases", b"")
    )

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


def test_the_server_is_handed_back_unstarted() -> None:
    """Constructing one binds nothing: a test starts it, asks it the port the
    OS chose, and stops it, which is the split `Station` is driven by."""

    async def started_and_stopped() -> None:
        server = Server(Face(RELEASES, fetch=Source()), 0)
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
        server = Server(Face(RELEASES, fetch=Source()), 0)
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
        server = Server(Face(RELEASES, fetch=Source()), 0)
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
        server = Server(Face(RELEASES, fetch=Source()), 0)
        await server.start()
        try:
            return await ask(server.port, request(origin=PAGE))
        finally:
            await server.close()

    status, body = asyncio.run(asyncio.wait_for(asked(), TIMEOUT_S))

    assert status == HTTPStatus.OK
    assert body == {"tags": TAGS}


def test_a_source_that_cannot_be_reached_is_said_on_the_box_as_well() -> None:
    """The caller is told, and so is whoever is reading the app's log: a
    release API that is away is not the caller's doing, and the page that
    asked may be nobody's at the moment (ADR-0050). What the face refuses a
    caller for stays the caller's own to read."""
    said: list[str] = []

    async def asked() -> tuple[int, object]:
        server = Server(
            Face(RELEASES, fetch=Source(OSError("no route to host"))),
            0,
            log=said.append,
        )
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
        server = Server(Face(RELEASES, fetch=Source()), 0, log=said.append)
        await server.start()
        try:
            return await ask(server.port, request(target="/layout"))
        finally:
            await server.close()

    status, _ = asyncio.run(asyncio.wait_for(asked(), TIMEOUT_S))

    assert status == HTTPStatus.NOT_FOUND
    assert said == []


# -- the wiring --------------------------------------------------------------


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
        served = Server(Face(RELEASES, fetch=Source()), 0)
        await mirror.start()
        await served.start()
        try:
            await log.wait_for("serial open")
            assert served.port != mirror.port

            status, body = await ask(served.port)
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
            await served.close()
            await mirror.close()
            cable.close()

    asyncio.run(asyncio.wait_for(scenario(), TIMEOUT_S))
