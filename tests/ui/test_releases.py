"""What the page lists the **release**s as, given what the **face** answered.

Scenarios: the face said the source carries these releases and the station
says it is running this **build**, so the page lists them in this order, with
these dates, and marks that one. The listing is a pure function of the two —
no socket, no clock and no DOM — which is what lets the whole of it be
asserted on a machine with nothing plugged in.

**Listing reaches no network here and none in a browser either.** The
scenarios are the face's answer already: the release API is read by the app
from its configured source and the page is handed what it carries
(ADR-0002, `face.py`), so there is nothing for this suite to reach and nothing
for a browser to. What holds that on the page's side is
`test_the_page_asks_its_own_face_and_no_release_api` below, and on the app's
side `tests/dccex_usb/test_face.py`.

**The rows are run rather than read**, as the decoder's pairs and the band's
readings are (`tests/ui/test_decoder.py`, `tests/ui/test_readings.py`): a list
an operator reads is worth nothing asserted against the source that would
produce it. The scenarios go through the real function under `node`, by way of
`tests/ui/releases.mjs`.

What the page draws these rows as is not here: the row under the tiles is its
own step, and what can be held of a Lit component in a Python gate is held
against its source when it lands.
"""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from tests.ui.test_look import UI

#: The listing, and the module it is the whole of.
RELEASES = UI / "src" / "releases.js"

#: What puts a scenario through it.
RUNNER = Path(__file__).resolve().parent / "releases.mjs"

NEWEST = {
    "tag": "v5.6.4-rails49.1",
    "published": "2025-09-14T10:32:07Z",
    "flashable": True,
}
MIDDLE = {
    "tag": "v5.6.3-rails49.2",
    "published": "2025-08-02T18:05:44Z",
    "flashable": True,
}
OLDEST = {
    "tag": "v5.6.2-rails49.1",
    "published": "2025-06-21T07:11:00Z",
    "flashable": True,
}

#: What the source carries, in an order that is not the one the page draws.
CARRIED = [MIDDLE, OLDEST, NEWEST]


def run(scenarios: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    """What a page would be drawing for each of `scenarios`, in one running."""
    node = shutil.which("node")
    assert node is not None, "no node on this machine to run the listing with"
    ran = subprocess.run(
        [node, str(RUNNER)],
        input=json.dumps(list(scenarios)),
        capture_output=True,
        text=True,
        check=False,
    )
    assert ran.returncode == 0, f"the listing did not run: {ran.stderr.strip()}"
    drawn: list[dict[str, Any]] = json.loads(ran.stdout)
    return tuple(drawn)


def listed(**scenario: Any) -> dict[str, Any]:
    """The listing a page would be drawing, for one scenario."""
    return run((scenario,))[0]["listing"]


def rows(**scenario: Any) -> list[dict[str, Any]]:
    """The release rows a page would be drawing, newest first."""
    listing: list[dict[str, Any]] = listed(**scenario)["rows"]
    return listing


def says() -> dict[str, str]:
    """The four sentences the page can say about a release or about the list,
    as the module exports them."""
    said: dict[str, str] = run(({},))[0]["says"]
    return said


# -- what the page lists ------------------------------------------------------


def test_the_releases_are_listed_newest_first_each_with_its_date() -> None:
    """The whole of what the row is for: every release the box is configured
    to read, in the order that puts the one to flash at the top, each with the
    day it was published (#8).

    The order is the page's own. The face passes the source's list on as it
    came, because which one is newest is a question about the dates.
    """
    listing = rows(carried=CARRIED)

    assert [row["tag"] for row in listing] == [
        NEWEST["tag"],
        MIDDLE["tag"],
        OLDEST["tag"],
    ]
    assert [row["published"] for row in listing] == [
        "2025-09-14",
        "2025-08-02",
        "2025-06-21",
    ]


def test_two_releases_published_on_one_day_keep_the_order_they_were() -> None:
    """The stamps are compared whole and not by the day the row shows, so a
    second release on one afternoon does not draw above the one that followed
    it."""
    morning = {**MIDDLE, "tag": "morning", "published": "2025-08-02T09:00:00Z"}
    evening = {**MIDDLE, "tag": "evening", "published": "2025-08-02T21:00:00Z"}

    listing = rows(carried=[morning, evening])

    assert [row["tag"] for row in listing] == ["evening", "morning"]
    assert [row["published"] for row in listing] == ["2025-08-02", "2025-08-02"]


def test_a_release_the_source_dated_none_is_listed_last_and_dated_none() -> None:
    """A guess standing where a reading goes is an observation the page did
    not make (ADR-0009 d.2), so a release the source stamped no moment on gets
    no day — and goes under the ones that can be ordered, because there is
    nothing to order it by."""
    undated = {"tag": "v5.6.5-rails49.1", "published": "", "flashable": True}

    listing = rows(carried=[undated, MIDDLE])

    assert [row["tag"] for row in listing] == [MIDDLE["tag"], undated["tag"]]
    assert listing[-1]["published"] == ""


def test_the_release_on_the_station_is_the_one_whose_tag_is_the_build() -> None:
    """Being up to date is a thing to see rather than to work out by reading a
    build and a tag against each other (docs/ui/README.md). The build is what
    the station said it is running, off the `G-` field of its banner (ADR-0008
    d.3)."""
    listing = rows(carried=CARRIED, build=MIDDLE["tag"])

    assert [row["onStation"] for row in listing] == [False, True, False]


def test_with_no_build_no_release_is_marked() -> None:
    """The build goes with the **link**: a station that is not answering has
    no build, and a row claiming to be what is on a board the page cannot see
    would be the page reporting what it never read (ADR-0008 d.3)."""
    assert [row["onStation"] for row in rows(carried=CARRIED)] == [False] * 3


def test_a_build_the_source_does_not_carry_marks_nothing() -> None:
    """A station running something the source has never published is a true
    thing to show and not an error: the list says nothing is on the station,
    which is what it knows."""
    listing = rows(carried=CARRIED, build="G-9db6d10")

    assert not any(row["onStation"] for row in listing)


def test_a_release_with_no_firmware_on_it_is_distinguishable() -> None:
    """A release exists whether or not anything can be written from it
    (CONTEXT.md), and a row that looked like the others would send an operator
    to a tag the mirror would refuse (#8, `face.py`)."""
    bare = {**NEWEST, "tag": "v5.6.5-rails49.1", "flashable": False}

    listing = rows(carried=[bare, MIDDLE])

    assert [row["flashable"] for row in listing] == [False, True]
    assert says()["NO_FIRMWARE"] == "no firmware to write"


def test_a_face_that_did_not_answer_says_so_rather_than_nothing() -> None:
    """Nothing said is not nothing published. An empty list drawn for a face
    that could not be asked would be this page reporting a source it never
    read (ADR-0009 d.2), and it would send somebody to a release API that is
    perfectly well."""
    listing = listed(carried=None)

    assert listing["rows"] == []
    assert listing["says"] == says()["UNREADABLE"] == "the releases could not be read"


def test_a_source_that_has_published_nothing_says_that_instead() -> None:
    """The other way of having no rows, and it is an answer rather than an
    outage: the source was asked and carries nothing (`face.py`)."""
    listing = listed(carried=[])

    assert listing["rows"] == []
    assert listing["says"] == says()["NONE"]
    assert "published" in listing["says"], "an empty source reads as an outage"


def test_a_list_with_releases_on_it_says_nothing_instead() -> None:
    """The sentence is what stands in for the rows and not a caption over
    them."""
    assert listed(carried=CARRIED)["says"] == ""
