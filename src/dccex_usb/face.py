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

import json
from http import HTTPStatus
from typing import NamedTuple, cast
from urllib.parse import urlsplit

from dccex_usb.firmware import RELEASES, Fetch, fetch

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
