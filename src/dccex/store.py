"""The store's scripts route, read from the translator's own process.

A script is a railroad's document in `control`'s store, one per railroad:
`GET /scripts/<railroad>`, answering `{"script": "<railroad>", "text": "..."}`
(ADR-0015 d.1, rails49/control#586). In its own container this app cannot
import the store to read one, so it reads it over the same face the page edits
it through — the store's routes are `control`'s, documented there, and a test
here runs against a fake of them rather than a copy (ADR-0014, consequences).

**Not `lib.documents.Documents`.** That one retries until the store answers,
which is right for a layout an app has nothing to do without and wrong here:
the translator comes up without a script, carries out OFF, STOP and speeds,
refuses power ON and keeps asking (ADR-0015 d.4). So one ask is one ask, and
whether to ask again is the translator's (`translator.following`).

Three readings and no more, because the translator does three different things
about them: the text, no script at all (`404`), and a store that did not
answer this request. Everything that is not a document carrying a text is the
third — nothing listening, a connection dropped, a reply that is not JSON, a
`5xx`, a document with no text in it — and a payload is read and never
trusted, as one off the bus is (BUS.md, rule 4).

Standard library only, as the library's own reader is: the whole of it is one
`GET`.
"""

import json
import urllib.error
import urllib.request
from typing import Any, cast
from urllib.parse import quote

SCRIPTS = "scripts"
"""The route, one level above the railroad's name. A box has one DCC-EX
station, so the key is the railroad alone (ADR-0015 d.1)."""

TIMEOUT_S = 5.0
"""How long one ask waits for the store before it counts as unanswered. A
store that has accepted the connection and then gone quiet is the same outage
as one that never accepted it, and this treats them as one — the same number
`lib/documents.py` gives the documents beside it."""


class Unanswered(Exception):
    """The store did not answer this ask — it is not up yet, or it could not,
    or what came back is no document of this shape. What the translator keeps
    asking about, where a `404` is an answer it acts on."""


class Scripts:
    """The scripts the store serves, off `base_url`.

    Blocking, on the caller's own thread: the first ask is made before the
    link to the station is opened, and the ones after it are made on a thread
    of their own so that the loop that drives the railroad is never waiting
    on a store (`translator.following`).
    """

    def __init__(self, base_url: str, *, timeout_s: float = TIMEOUT_S) -> None:
        self._base = base_url.rstrip("/")
        self._timeout_s = timeout_s

    def text(self, railroad: str) -> str | None:
        """The railroad's script as its text, or None where the store has
        none for it. Raises `Unanswered` where the store did not answer.

        The name is escaped as one level of the route, as the library's
        reader escapes a layout's: a railroad called `a/b` is a name the
        store does not have rather than a route of its own.
        """
        where = f"{self._base}/{SCRIPTS}/{quote(railroad, safe='')}"
        try:
            with urllib.request.urlopen(where, timeout=self._timeout_s) as answer:
                body = json.load(answer)
        except urllib.error.HTTPError as answered:
            if answered.code == 404:
                return None
            raise Unanswered(f"{where}: {_reason(answered)}") from None
        except (OSError, ValueError) as away:
            # `URLError` is an `OSError`, which is also what a connection
            # dropped mid-reply raises, and a reply that is not JSON is a
            # `ValueError`: every one of them is a store that has not
            # answered this ask.
            raise Unanswered(f"{where}: {away}") from None
        said = (
            cast(dict[str, Any], body).get("text") if isinstance(body, dict) else None
        )
        if not isinstance(said, str):
            raise Unanswered(f"{where}: answered with no script text")
        return said


def _reason(answered: urllib.error.HTTPError) -> str:
    """The store's own words, which every refusal it makes carries in
    `error`. A body that is not one of ours leaves the status to speak."""
    try:
        body = json.load(answered)
    except ValueError:
        return f"{answered.code} {answered.reason}"
    said = cast(dict[str, Any], body).get("error") if isinstance(body, dict) else None
    return said if isinstance(said, str) else f"{answered.code} {answered.reason}"
