"""The store's routes the face reaches: the railroads there are, and one
railroad's **script** read and written.

A script is a railroad's document in `control`'s store, one per railroad, and
the page edits it through this app's face (ADR-0015 d.1, d.5,
rails49/control#586). In its own container this app cannot import the store, so
it reads and writes it over HTTP the way the translator reads it
(`dccex.store`), and a test here runs against a fake of the routes rather than
a copy of them — the routes are `control`'s and documented there (ADR-0014,
consequences).

**Three asks, because the page does three things.** The railroads there are
(`GET /drawings`), one railroad's text (`GET /scripts/<railroad>`, `404` for a
railroad with none), and a text put there (`PUT /scripts/<railroad>`). No
retry and no backoff: one ask is one ask, and a store that did not answer is a
sentence the page is given rather than a request the mirror sits on — the
person editing is watching, and the mirror is holding a cable while it waits
(`face.py`).

**Nothing is read that is not needed.** The list is names and the document is
its text; what else the store keeps about a railroad is `control`'s and is not
passed on. A payload is read one field at a time and never trusted, as one off
the bus is.

Standard library only, as everything here is, and blocking work is done off
the loop's thread: the mirror's fan-out happens while a store is being asked,
and a throttle whose bytes waited on somebody else's HTTP request would be a
throttle this app stopped mirroring for (`firmware.py`'s `fetch`).
"""

import asyncio
import http.client
import json
import urllib.error
import urllib.request
from typing import Any, cast
from urllib.parse import quote

DRAWINGS_PATH = "drawings"
"""What the railroads there are are listed at. A railroad's drawing is what
`control` keeps under its name, so the list of drawings is the list of
railroads — the store's own word, and the one route that answers it
(rails49/control#586)."""

DRAWINGS = "drawings"
"""What the store's list comes back under."""

SCRIPTS_PATH = "scripts"
"""The scripts route, one level above the railroad's name. A box has one
DCC-EX station, so the key is the railroad alone (ADR-0015 d.1)."""

SCRIPT = "script"
"""What a script document names its railroad under."""

TEXT = "text"
"""What a script document carries its text under."""

TIMEOUT_S = 5.0
"""How long one ask waits for the store before it counts as unanswered. A
store that has accepted the connection and then gone quiet is the same outage
as one that never accepted it, and this treats them as one — the same number
the translator's reader gives it (`dccex.store`)."""

JSON = "application/json"


class Away(Exception):
    """The store did not answer this ask — it is not up, or it could not, or
    what came back is no document of this shape.

    One exception for all of them, because there is one thing the face does
    about it: say so, with the store's own words where it gave any. A `404`
    from the scripts route is not this: a railroad with no script is an
    answer, and it is the answer the page opens the sample under.
    """


class _Missing(Away):
    """The route answered `404`: the store holds no document under that name.

    Private, and a kind of `Away` so that a caller that has nothing to say
    about a missing document is told the same thing it would be told about a
    store that is down. The scripts route is the one caller that does have
    something to say, and it is the one that catches this.
    """


class Store:
    """`control`'s store, off `base_url`, as the face reaches it.

    Every method is awaited on this loop and does its waiting on a thread of
    its own, so the mirror goes on mirroring while the store is being asked.
    """

    def __init__(self, base_url: str, *, timeout_s: float = TIMEOUT_S) -> None:
        self._base = base_url.rstrip("/")
        self._timeout_s = timeout_s

    @property
    def where(self) -> str:
        """The store's address, as the face names it in a refusal: what a
        person reading the page has to go and look at."""
        return self._base

    async def railroads(self) -> list[str]:
        """The railroads the store holds, in the order it lists them.

        The order is the store's and is passed on as it came, as the releases
        are: which railroad a person wants is a question about the names, and
        the page that draws them is what asks it.

        An entry that is not a name is dropped and the rest stand: what the
        store carries is what the page is shown, and one odd entry is not a
        reason to show a person no railroads at all.
        """
        where = f"{self._base}/{DRAWINGS_PATH}"
        listed = (await self._got(where)).get(DRAWINGS)
        if not isinstance(listed, list):
            raise Away(f"{where}: answered with no railroads")
        return [
            name for name in cast(list[Any], listed) if isinstance(name, str) and name
        ]

    async def text(self, railroad: str) -> str | None:
        """The railroad's script as its text, or None where the store has none
        for it.

        The name is escaped as one level of the route: a railroad called `a/b`
        is a name the store does not have rather than a route of its own.
        """
        where = self._scripts(railroad)
        try:
            said = (await self._got(where)).get(TEXT)
        except _Missing:
            return None
        if not isinstance(said, str):
            raise Away(f"{where}: answered with no script text")
        return said

    async def puts(self, railroad: str, text: str) -> None:
        """The railroad's script put there, as the document the store's route
        takes: the railroad it is for and the text of it.

        It answers nothing. What the store says about a document it saved is
        the store's own and is not passed on: what the page asked is whether
        the text is now the railroad's script, which is this returning.
        """
        where = self._scripts(railroad)
        body = json.dumps({SCRIPT: railroad, TEXT: text}).encode()
        await asyncio.to_thread(self._put, where, body)

    def _scripts(self, railroad: str) -> str:
        return f"{self._base}/{SCRIPTS_PATH}/{quote(railroad, safe='')}"

    async def _got(self, where: str) -> dict[str, Any]:
        """One document off the store, read off the loop's thread."""
        return await asyncio.to_thread(self._read, where)

    def _read(self, where: str) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(where, timeout=self._timeout_s) as answer:
                body = json.load(answer)
        except urllib.error.HTTPError as answered:
            said = f"{where}: {_reason(answered)}"
            raise (_Missing(said) if answered.code == 404 else Away(said)) from None
        except (OSError, ValueError, http.client.HTTPException) as away:
            # `URLError` is an `OSError`, a reply that is not JSON is a
            # `ValueError`, and a connection dropped mid-reply is an
            # `HTTPException` (`IncompleteRead`): every one of them is a store
            # that has not answered this ask.
            raise Away(f"{where}: {away}") from None
        if not isinstance(body, dict):
            raise Away(f"{where}: answered with {type(body).__name__}, not a document")
        return cast(dict[str, Any], body)

    def _put(self, where: str, body: bytes) -> None:
        request = urllib.request.Request(
            where, data=body, method="PUT", headers={"Content-Type": JSON}
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_s) as answer:
                answer.read()
        except urllib.error.HTTPError as answered:
            raise Away(f"{where}: {_reason(answered)}") from None
        except (OSError, ValueError, http.client.HTTPException) as away:
            raise Away(f"{where}: {away}") from None


def _reason(answered: urllib.error.HTTPError) -> str:
    """The store's own words, which every refusal it makes carries in
    `error`. A body that is not one of ours leaves the status to speak."""
    try:
        body = json.load(answered)
    except (OSError, ValueError, http.client.HTTPException):
        return f"{answered.code} {answered.reason}"
    said = cast(dict[str, Any], body).get("error") if isinstance(body, dict) else None
    return said if isinstance(said, str) else f"{answered.code} {answered.reason}"
