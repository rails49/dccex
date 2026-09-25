"""What the page lists the **release**s as, given what the **face** answered.

Scenarios: the face said the source carries these releases and the station
says it is running this **build**, so the page lists them in this order, with
these dates, and marks that one. The listing is a pure function of the two —
no socket, no clock and no DOM — which is what lets the whole of it be
asserted on a machine with nothing plugged in.

**Listing reaches no network here and none in a browser either.** The
scenarios are the face's answer already: the release API is read by the app
from its configured source and the page is handed what it carries (the
organisation's ADR-0002, `face.py`), so there is nothing for this suite to
reach and nothing for a browser to. What holds that on the page's side is
`test_the_page_asks_its_own_face_and_no_release_api` below, and on the app's
side `tests/dccex_usb/test_face.py`.

**The rows are run rather than read**, as the decoder's pairs and the band's
readings are (`tests/ui/test_decoder.py`, `tests/ui/test_readings.py`): a list
an operator reads is worth nothing asserted against the source that would
produce it. The scenarios go through the real function under `node`, by way of
`tests/ui/releases.mjs`. So is what the page makes of the answer the rows come
out of: a rule about which of two sentences a document gets is worth no more
asserted against the module that would apply it, so the documents go through
the reader the same way (#95).

What cannot be run here is Lit. The gate is Python and the node beside it is a
bare one with no packages, so nothing in either can mount a component and read
the DOM back: the
words are asserted here and the drawing of them is held against the
component's source below, which is the cost `tests/ui/test_look.py` already
names.
"""

import re
from pathlib import Path
from typing import Any

import pytest

from tests.ui.node import HELD, ran
from tests.ui.test_look import HEX, ROOT, UI
from tests.ui.test_monitor import rule
from tests.ui.test_stream import NAMED, code, quoted

#: The listing, and the module it is the whole of.
RELEASES = UI / "src" / "releases.js"

#: What puts a scenario through it.
RUNNER = Path(__file__).resolve().parent / "releases.mjs"

#: The row under the tiles.
LIST = UI / "src" / "ui" / "dccex-releases.ts"

#: What it is drawn with.
STYLES = UI / "src" / "ui" / "dccex-releases.styles.ts"

#: The page that hands it the releases and the build.
APP = UI / "src" / "ui" / "dccex-app.ts"

#: Where the page asks the mirror about the mirror.
FACE = UI / "src" / "face.ts"

#: The app's end of the same reading, where `carried()` draws the line the
#: page's reader mirrors.
APP_FACE = ROOT / "src" / "dccex_usb" / "face.py"

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
    drawn: list[dict[str, Any]] = ran(RUNNER, list(scenarios), "the listing")
    return tuple(drawn)


def listed(**scenario: Any) -> dict[str, Any]:
    """The listing a page would be drawing, for one scenario."""
    return run((scenario,))[0]["listing"]


def rows(**scenario: Any) -> list[dict[str, Any]]:
    """The release rows a page would be drawing, newest first."""
    listing: list[dict[str, Any]] = listed(**scenario)["rows"]
    return listing


def read(document: Any) -> list[dict[str, Any]] | None:
    """What the page's reader makes of one `releases` document."""
    made: list[dict[str, Any]] | None = run(({"document": document},))[0]["read"]
    return made


def says() -> dict[str, str]:
    """The four sentences the page can say about a release or about the list,
    as the module exports them."""
    said: dict[str, str] = run(({},))[0]["says"]
    return said


# -- what the page lists ------------------------------------------------------


@pytest.mark.node
def test_the_releases_are_listed_newest_first_each_with_its_date() -> None:
    """The whole of what the row is for: every release the mirror is
    configured to read, in the order that puts the one to flash at the top,
    each with the day it was published (#8).

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


@pytest.mark.node
def test_two_releases_published_on_one_day_keep_the_order_they_were() -> None:
    """The stamps are compared whole and not by the day the row shows, so a
    second release on one afternoon does not draw above the one that followed
    it."""
    morning = {**MIDDLE, "tag": "morning", "published": "2025-08-02T09:00:00Z"}
    evening = {**MIDDLE, "tag": "evening", "published": "2025-08-02T21:00:00Z"}

    listing = rows(carried=[morning, evening])

    assert [row["tag"] for row in listing] == ["evening", "morning"]
    assert [row["published"] for row in listing] == ["2025-08-02", "2025-08-02"]


@pytest.mark.node
def test_a_release_the_source_dated_none_is_listed_last_and_dated_none() -> None:
    """A guess standing where a reading goes is an observation the page did
    not make (ADR-0009 d.2), so a release the source stamped no moment on gets
    no day — and goes under the ones that can be ordered, because there is
    nothing to order it by."""
    undated = {"tag": "v5.6.5-rails49.1", "published": "", "flashable": True}

    listing = rows(carried=[undated, MIDDLE])

    assert [row["tag"] for row in listing] == [MIDDLE["tag"], undated["tag"]]
    assert listing[-1]["published"] == ""


@pytest.mark.node
def test_the_release_on_the_station_is_the_one_whose_tag_is_the_build() -> None:
    """Being up to date is a thing to see rather than to work out by reading a
    build and a tag against each other (docs/ui/README.md). The build is what
    the station said it is running, off the `G-` field of its banner (ADR-0008
    d.3)."""
    listing = rows(carried=CARRIED, build=MIDDLE["tag"])

    assert [row["onStation"] for row in listing] == [False, True, False]


@pytest.mark.node
def test_with_no_build_no_release_is_marked() -> None:
    """The build goes with the **link**: a station that is not answering has
    no build, and a row claiming to be what is on a board the page cannot see
    would be the page reporting what it never read (ADR-0008 d.3)."""
    assert [row["onStation"] for row in rows(carried=CARRIED)] == [False] * 3


@pytest.mark.node
def test_a_build_the_source_does_not_carry_marks_nothing() -> None:
    """A station running something the source has never published is a true
    thing to show and not an error: the list says nothing is on the station,
    which is what it knows."""
    listing = rows(carried=CARRIED, build="G-9db6d10")

    assert not any(row["onStation"] for row in listing)


@pytest.mark.node
def test_a_release_there_is_nothing_to_write_from_is_distinguishable() -> None:
    """A release exists whether or not anything can be written from it
    (CONTEXT.md), and a row that looked like the others would send an operator
    to a tag the mirror would refuse (#8, `face.py`).

    The sentence says nothing about a firmware, because `flashable` stopped
    being about one: it is false for a release with no `firmware.bin` on it
    and for one whose `firmware.bin` the source reports no digest for, and the
    face sends the one boolean for both (#81, #109, `face.py`'s `FLASHABLE`).
    A row that named the first would be a page telling an operator something
    untrue about the second."""
    bare = {**NEWEST, "tag": "v5.6.5-rails49.1", "flashable": False}

    listing = rows(carried=[bare, MIDDLE])

    assert [row["flashable"] for row in listing] == [False, True]
    assert says()["NO_FIRMWARE"] == "nothing here to write and check"


@pytest.mark.node
def test_a_face_that_did_not_answer_says_so_rather_than_nothing() -> None:
    """Nothing said is not nothing published. An empty list drawn for a face
    that could not be asked would be this page reporting a source it never
    read (ADR-0009 d.2), and it would send somebody to a release API that is
    perfectly well."""
    listing = listed(carried=None)

    assert listing["rows"] == []
    assert listing["says"] == says()["UNREADABLE"] == "the releases could not be read"


@pytest.mark.node
def test_a_source_that_has_published_nothing_says_that_instead() -> None:
    """The other way of having no rows, and it is an answer rather than an
    outage: the source was asked and carries nothing (`face.py`)."""
    listing = listed(carried=[])

    assert listing["rows"] == []
    assert listing["says"] == says()["NONE"]
    assert "published" in listing["says"], "an empty source reads as an outage"


@pytest.mark.node
def test_a_list_with_releases_on_it_says_nothing_instead() -> None:
    """The sentence is what stands in for the rows and not a caption over
    them."""
    assert listed(carried=CARRIED)["says"] == ""


def test_the_listing_holds_nothing() -> None:
    """No socket, no state, no clock and no DOM, as every other module a bare
    node runs is held to (`tests/ui/test_decoder.py`,
    `tests/ui/test_message.py`, `tests/ui/test_flash.py`,
    `tests/ui/test_monitor.py`, `tests/ui/test_stream.py`).

    The module claims it in its own header — that is why reading the face's
    answer sits here rather than beside the `fetch` — and a claim no check
    holds is a claim that lasts until somebody is in a hurry. It is the union
    of the siblings' lists, because this one says what all of them say.

    **Read off the code and not off the file.** The prose here says *document*
    where it means the JSON body the face answers with, so a substring check
    like the decoder's would go red on the sentences rather than on the
    module: `code()` takes the comments off first and what is left is what a
    browser would run (#122). The prose word stays where it is (#120).
    """
    source = code(RELEASES.read_text())
    assert "import " not in source, "the listing imports something"
    for held in HELD:
        assert held not in source, f"the listing reaches {held}"


# -- what the page draws ------------------------------------------------------


def test_the_row_draws_the_listing_the_page_hands_it() -> None:
    """The ordering, the dates and the mark are the module's — a pure function
    of what the face answered and what the station said — and the drawing is
    this component's, as the tiles' is (`tests/ui/test_tiles.py`)."""
    drawn = LIST.read_text()
    assert 'from "../releases.js"' in drawn, "the row works the listing out itself"
    assert "listing(this.carried, this.build)" in drawn
    app = APP.read_text()
    assert "<dccex-releases" in app
    assert ".carried=${this.carried}" in app
    assert ".build=${this.readings.build}" in app


@pytest.mark.node
def test_the_row_says_which_release_is_on_the_station_in_the_module_s_words() -> None:
    """The two sentences a row can carry are the listing module's, so that
    what an operator reads is asserted by running it rather than by reading
    the component (`tests/ui/test_readings.py`)."""
    drawn = code(LIST.read_text())
    assert "ON_STATION" in drawn and "NO_FIRMWARE" in drawn
    for sentence in says().values():
        assert sentence not in drawn, f"the row writes {sentence!r} out a second time"


def test_the_row_is_under_the_tiles_and_over_the_monitor() -> None:
    """Under the **build** it is compared against and over the conversation it
    is not part of (docs/ui/README.md)."""
    app = APP.read_text()
    assert 'import "./dccex-releases.js";' in app
    assert app.index("<dccex-tiles") < app.index("<dccex-releases")
    assert app.index("<dccex-releases") < app.index("<dccex-monitor")
    assert 'customElements.define("dccex-releases"' in LIST.read_text()


def test_the_list_is_collapsed_under_the_tiles() -> None:
    """A row that opens, so that the station's particulars and its
    conversation are what the page is when nobody has asked about firmware
    (docs/ui/README.md)."""
    drawn = LIST.read_text()
    assert "<details" in drawn and "<summary" in drawn


def test_the_row_holds_no_counterparty_of_its_own() -> None:
    """Choosing a release flashes it as of #9, and what it is flashed with is
    handed down: the **stream** the stop and the cut go up and the **face**
    that is asked to write are the page's (the organisation's ADR-0002,
    `dccex-app.ts`).

    What the gesture does is held where the sequence is run
    (`tests/ui/test_flash.py`); what is held here is that this pane reaches for
    neither of them.
    """
    drawn = code(LIST.read_text())
    assert '"../face.js"' not in drawn, "the row holds the face"
    assert '"../stream.js"' not in drawn, "the row holds the stream"
    assert "fetch(" not in drawn, "the row asks somebody itself"


def test_the_row_works_no_reading_out_of_its_own() -> None:
    """No clock, no socket and no protocol in a component that has a DOM in
    reach: what it shows is a pure function of what the page knows, which is
    what lets every row of it be asserted as a pair (ADR-0009 d.1)."""
    drawn = code(LIST.read_text())
    for held in ("Date", "setInterval", "fetch(", "WebSocket", "decoder.js"):
        assert held not in drawn, f"the row reaches {held}"


def test_the_rows_wrap_at_the_width_of_a_phone() -> None:
    """The phone at the layout is where this is read, and a tag is long: the
    date and what is said of a release go under the tag rather than off the
    side of the screen (docs/ui/README.md)."""
    release = rule(STYLES.read_text(), ".release")
    assert "flex-wrap: wrap;" in release, "a release row runs off the side"


def test_the_row_is_the_work_pane_s_and_not_the_chrome_s() -> None:
    """The chrome's four values say *this is the same project* across rails49's
    UIs and stay on the chrome; a pane follows the system's theme, which is
    Shoelace's tokens (LOOK.md).

    The one look value it may ask for is `--rail-button`, and it is a size
    rather than a colour: it is the rules' minimum for a thumb, and the control
    that writes a release is pressed on a phone held at the layout, as the
    command box's send is (`tests/ui/test_monitor.py`, #9).
    """
    styles = STYLES.read_text()
    assert not HEX.findall(styles), "the row writes a colour out"
    asked = set(re.findall(r"var\((--[a-z0-9-]+)\)", styles))
    borrowed = {token for token in asked if not token.startswith("--sl-")}
    assert borrowed == {"--rail-button"}, f"the row takes the chrome's {borrowed}"


# -- what the browser asks ----------------------------------------------------


def test_the_page_asks_its_own_face_and_no_release_api() -> None:
    """A UI talks to the bus, the store and its own app's face, and nothing
    else (the organisation's ADR-0002). The releases are read by the app from
    its configured source and handed on; the browser reaches the release API on
    no path (#8)."""
    asking = FACE.read_text()
    assert "RELEASES_PATH = `${FACE}/releases`" in asking
    assert "releases()" in APP.read_text(), "the page never asks the face"
    for name, module in {
        RELEASES.name: RELEASES.read_text(),
        FACE.name: asking,
        LIST.name: LIST.read_text(),
    }.items():
        for literal in quoted(module):
            assert not NAMED.search(literal), f"{name} names {literal}"


def test_the_source_cannot_be_named_by_the_page() -> None:
    """Where releases are read from is a flag on the app (ADR-0042,
    `firmware.py`). The page asks one path with nothing on it: a query the
    face would drop is still a page that thought it could choose, and this
    holds that nothing here ever grows one."""
    asking = FACE.read_text()
    fetching = code(asking)[code(asking).index("export async function releases(") :]
    assert "fetch(RELEASES_PATH)" in fetching, "the page builds the address it asks"
    for literal in quoted(asking):
        assert "?" not in literal, f"the page asks with a query: {literal}"
    for named in ("source", "repo", "github"):
        assert named not in code(asking).lower(), f"the page names a {named}"


def test_a_face_that_did_not_answer_reads_as_nothing_said() -> None:
    """A face that is away, a status that is not a 200, an answer that is not
    a list of releases: `null`, and the row says the releases could not be
    read rather than that there are none (ADR-0009 d.2)."""
    asking = code(FACE.read_text())
    fetching = asking[asking.index("export async function releases(") :]
    assert "Promise<Carried[] | null>" in asking, "a face that is away raises"
    assert "} catch {" in fetching, "a face that is away takes the page with it"
    assert fetching.count("return null;") >= 2


@pytest.mark.node
def test_a_source_that_lists_nothing_reads_as_a_list_of_no_releases() -> None:
    """The first of the three answers a `releases` document gets out of the
    page's reader: the source was asked and carries nothing, which is an
    answer. It reads as a list of no releases, and the page says the source
    has published none yet rather than that it could not be read."""
    assert read([]) == []
    assert listed(carried=read([]))["says"] == says()["NONE"]


@pytest.mark.node
def test_a_list_that_names_no_release_among_its_entries_reads_as_nothing_said() -> None:
    """The middle one, and the defect this was written for (#95). A list that
    carries entries and yields no release out of any of them is a document the
    page could not read, not a source with nothing on it: it reads as nothing
    said, and the page says the releases could not be read.

    Before this change it read as a list of no releases, which says the source
    has published nothing and sends somebody looking at a release API that is
    perfectly well — the distinction #66 was filed to draw, undrawn at this
    end of the wire (ADR-0009 d.2, `face.py`).
    """
    for document in (
        [{"message": "Not Found"}],
        [{"published": "2025-09-14T10:32:07Z", "flashable": True}],
        [{"tag": ""}],
        ["v5.6.4-rails49.1"],
        [None],
        [{"message": "Not Found"}, {"message": "Not Found"}],
    ):
        assert read(document) is None, f"{document} reads as a source carrying nothing"

    unreadable = read([{"message": "Not Found"}])
    assert listed(carried=unreadable)["says"] == says()["UNREADABLE"]


@pytest.mark.node
def test_a_list_with_releases_on_it_reads_as_the_releases_it_carries() -> None:
    """The third: what the page can read, it keeps. An entry it cannot read is
    dropped and the rest of the list stands — what the source carries is what
    the page is shown, and a list quietly shorter than the source's would be
    this page deciding what a person may see (`face.py`)."""
    assert read([NEWEST, MIDDLE, OLDEST]) == [NEWEST, MIDDLE, OLDEST]
    assert read([NEWEST, {"message": "Not Found"}]) == [NEWEST]
    assert listed(carried=read(CARRIED))["says"] == ""


@pytest.mark.node
def test_an_answer_that_is_not_a_list_at_all_reads_as_nothing_said() -> None:
    """Under `releases`, anything but a list is a document about something
    else — a refusal from a service that is not the face, a field that moved,
    nothing at all — and none of it is a source that has published nothing."""
    for document in ({"message": "Not Found"}, "v5.6.4-rails49.1", 7, None, True):
        assert read(document) is None, f"{document!r} reads as an answer about releases"


@pytest.mark.node
def test_a_release_the_source_left_a_field_off_is_read_with_that_field_empty() -> None:
    """One field at a time, as the app reads the release API: the rest of a
    release is left where it is rather than guessed at. No date reads as no
    date, and no `flashable` reads as nothing to write, which is the direction
    that does not send an operator at a tag the mirror would refuse."""
    assert read([{"tag": "v5.6.5-rails49.1"}]) == [
        {"tag": "v5.6.5-rails49.1", "published": "", "flashable": False}
    ]
    assert read([{**NEWEST, "published": 1757845927}]) == [{**NEWEST, "published": ""}]


def test_the_page_s_reader_names_the_face_s_as_the_rule_it_mirrors() -> None:
    """Two ends of a wire read defensively and the duplication stays; what
    must not differ is the rule (#95).

    What the reader answers is run above. What cannot be run is that the two
    halves are one rule, so it is read: the page's half names whose other half
    it is, the app's still draws the line in the one line it draws it in, and
    the two are written with the same two names in the same order.
    """
    asking = code(FACE.read_text())
    fetching = asking[asking.index("export async function releases(") :]
    assert (
        "carried((said as Record<string, unknown>)[RELEASES])" in fetching
    ), "the page asks for the releases and reads them some other way"
    assert "`face.py`'s `carried()`" in FACE.read_text(), "the page names no other half"
    assert "if listed and not found:" in APP_FACE.read_text(), "the app drew no line"
    assert (
        "if (listed.length > 0 && found.length === 0) {" in RELEASES.read_text()
    ), "the page's half is no longer written as the app's is"


def test_the_releases_are_asked_for_once_and_not_on_the_poll() -> None:
    """The station is polled every few seconds because its readings change
    under the eye; the source is somebody else's service and what it carries
    changes when somebody publishes. A page that asked it on the poll would
    spend a rate limit on an answer that is the same all evening, and what
    does change — which release is on the station — arrives on the banner
    (ADR-0010 d.1, ADR-0008 d.3).
    """
    page = code(APP.read_text())
    asking = page[page.index("#ask(): void {") : page.index("#now(): void {")]
    assert "releases()" not in asking, "the page asks the source on every poll"
    opening = page[
        page.index("override connectedCallback(") : page.index("#ask(): void")
    ]
    assert "#list()" in opening, "the page never asks for the releases"
