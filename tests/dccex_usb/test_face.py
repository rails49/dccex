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
from collections.abc import Sequence
from http import HTTPStatus

import pytest

from dccex_usb.face import Face

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
