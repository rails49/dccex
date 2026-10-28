"""What the **journal** view draws, given a journal and a period.

The reading is held next door — which lines are an **incident** and what the
counts come to (`tests/ui/test_journal.py`, ADR-0022 d.5) — and what is held
here is what a person reads: the rows newest first, the lines under each one,
the routine lines a toggle brings in, the counts as words, the periods the file
offers, and every sentence the controls are pressed with.

**The journals are the reading suite's own.** The lines are written with its
helpers, so a line in this file is the line the translator writes and there is
one spelling of it for both halves (#266, ADR-0022 d.2).

**It is run rather than read**, as the decoder's pairs and the band's readings
are (`tests/ui/test_decoder.py`): a sentence an operator reads is worth
nothing asserted against the source that would produce it. The scenarios go
through the real module under `node`, by way of `tests/ui/incidents.mjs`, and
these checks carry the `node` marker — the gate does not collect them and the
workflow runs them in a job a pull request requires (`scripts/check.sh`, #101).

**And the drawing is mounted rather than read** (#126). That the words land on
the row they are about is asserted by mounting the three components in
happy-dom (`ui/test/counts.test.ts`, `ui/test/incidents.test.ts`,
`ui/test/controls.test.ts`, `ui/test/journal.test.ts`). What is read off the
sources below is what a DOM does not answer: that the components write none of
these sentences out again, and that the pane holds no counterparty of its own.
"""

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import pytest

from tests.ui.node import HELD, ran
from tests.ui.paths import UI
from tests.ui.test_journal import (
    A_BURST_ON_ANOTHER_DISTRICT,
    A_CLEAN_FLIP,
    A_FLIP_ON_ANOTHER_DISTRICT,
    A_FLIP_THE_SHORT_OUTLIVED,
    A_SLOW_FLIP,
    A_TRIP_AND_A_LINK_LOSS,
    AN_ALERT_ON_EACH,
    BEFORE,
    BUILD,
    FLIPS_ON_TWO_DISTRICTS,
    POWERED,
    THREE_FLIPS,
    TWO_BUILDS,
    at,
    down,
    guarded,
    invert,
    normal,
    restore,
    up,
)
from tests.ui.test_stream import code, quoted

#: What the view draws, and the module it is the whole of.
INCIDENTS = UI / "src" / "incidents.js"

#: What puts a journal through it.
RUNNER = Path(__file__).resolve().parent / "incidents.mjs"

#: The view, and the three components it hands what is read down to.
VIEW = UI / "src" / "ui" / "dccex-journal.ts"
TABLE = UI / "src" / "ui" / "dccex-counts.ts"
LIST = UI / "src" / "ui" / "dccex-incidents.ts"
CONTROLS = UI / "src" / "ui" / "dccex-controls.ts"

#: When the journals are read: the moment after the last line of them, so that
#: a span counted back from it holds every line. The module takes the clock as
#: an argument and keeps none (ADR-0009 d.1), which is what makes this a value
#: here rather than a machine's.
NOW = at(3_600_000)

#: A stamp drawn as a reader reads it: the day and the time on their own clock,
#: to the millisecond.
DRAWN = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}$")

#: One instant, and what a machine in each of two zones draws it as. Zones
#: with no summer time in them, as `tests/ui/test_monitor.py` picks them, so
#: the pair holds in January and in July alike.
ZONED: dict[str, str] = {
    "UTC": "2026-10-12 18:00:01.100",
    "Pacific/Honolulu": "2026-10-12 08:00:01.100",
}


def run(asks: list[dict[str, Any]], zone: str = "UTC") -> list[Any]:
    """What the module answers for `asks`, in one running of it.

    In a zone of this module's choosing, because one of the asks is about the
    machine's own: a stamp is the reader's clock rather than UTC, and a check
    that ran in whatever zone the machine happened to be set to could not tell
    those two apart on a box in London.
    """
    answered: list[Any] = ran(RUNNER, asks, "the journal view", zone=zone)
    return answered


@lru_cache(maxsize=1)
def own() -> dict[str, Any]:
    """The module's own words and columns."""
    (words,) = run([{"own": True}])
    return dict(words)


def drew(
    journal: list[dict[str, Any]],
    period: dict[str, Any] | None = None,
    *,
    routine: bool = False,
) -> dict[str, Any]:
    """What a page would be drawing for one journal over one period."""
    (shown,) = run([{"journal": journal, "period": period or {}, "routine": routine}])
    return dict(shown)


def cells(shown: dict[str, Any], district: str) -> dict[str, str]:
    """One district's row, by the column each cell is under."""
    (row,) = [row for row in shown["districts"] if row["district"] == district]
    return dict(zip(own()["headings"][1:], row["cells"], strict=True))


def lines(journal: list[dict[str, Any]]) -> str:
    """One journal as the face serves it: one JSON object per line.

    Written out here rather than read off a file, because what the page is
    handed is bytes and what this suite holds is lines (ADR-0022 d.1).
    """
    return "".join(f"{json.dumps(line)}\n" for line in journal)


@pytest.mark.node
def test_an_incident_carries_the_journal_lines_it_is_made_of() -> None:
    """The flip, the cut, the retry and the district being itself again: a row
    opens on the lines a person would otherwise be reading the file for.

    Which lines those are is the reading module's own (ADR-0022 d.3). The flip
    is one of them and it is *before* the incident's start — the reading opens
    at the line that cut — so a window read off the start and the end would
    leave the cause of the reversal out of the thing it caused.
    """
    (one,) = drew(A_FLIP_THE_SHORT_OUTLIVED)["entries"]
    assert one["kind"] == "reversal"
    assert one["district"] == "C"
    assert [line["said"] for line in one["lines"]] == [
        invert("C"),
        guarded("C"),
        restore("C"),
        normal("C"),
    ]


@pytest.mark.node
def test_the_flips_a_burst_took_are_under_the_burst() -> None:
    """Three flips inside a second are one row, and all three are in it: the
    two before the one that said so are part of what it says.

    The line that closed it is in it too — here the power going off, which is
    where the reading of a district that never came back by itself ends.
    """
    (one,) = drew(THREE_FLIPS)["entries"]
    assert one["kind"] == "repeated reversal"
    assert [line["said"] for line in one["lines"]] == [*[invert("C")] * 3, "<p0 C>"]


@pytest.mark.node
def test_a_reversal_row_names_the_district_that_flipped() -> None:
    """A reversal is filed under the district that was cut, so where another
    district flipped the kind names it (#368). Where the flip was the
    district's own the kind reads as it is."""
    (one,) = drew(A_FLIP_ON_ANOTHER_DISTRICT)["entries"]
    assert (one["district"], one["kind"]) == ("A", "reversal (C)")
    (own,) = drew(A_FLIP_THE_SHORT_OUTLIVED)["entries"]
    assert (own["district"], own["kind"]) == ("C", "reversal")


@pytest.mark.node
def test_a_repeated_reversal_row_names_the_district_that_flipped() -> None:
    """The burst on D is D's row and reads as it is; the cut it caused on A
    names D."""
    rows = drew(A_BURST_ON_ANOTHER_DISTRICT)["entries"]
    assert sorted((row["district"], row["kind"]) for row in rows) == [
        ("A", "repeated reversal (D)"),
        ("D", "repeated reversal"),
    ]


@pytest.mark.node
def test_a_reversal_that_took_flips_on_two_districts_names_both() -> None:
    """A first, as the districts are."""
    (one,) = drew(FLIPS_ON_TWO_DISTRICTS)["entries"]
    assert (one["district"], one["kind"]) == ("A", "reversal (C, D)")


@pytest.mark.node
def test_a_row_says_the_time_the_district_the_kind_and_the_numbers() -> None:
    """What the list shows before it is opened, in the words it shows them in:
    a number is drawn and a reading nobody took is blank (ADR-0009 d.2)."""
    (one,) = drew(A_FLIP_THE_SHORT_OUTLIVED)["entries"]
    assert one["when"] == "2026-10-12 18:00:01.100"
    assert one["trips"] == "1"
    assert one["milliamps"] == "4210 mA"
    assert one["cut"] == "100 ms"
    assert one["says"] == ""
    assert one["routine"] is False
    (spike,) = drew(AN_ALERT_ON_EACH)["entries"]
    assert spike["kind"] == "spike"
    assert spike["cut"] == "0 ms", "a district nothing cut is cut for no time"


@pytest.mark.node
def test_the_lines_no_incident_took_are_rows_only_where_they_are_asked_for() -> None:
    """A flip nothing came of and the power going on and off are the railroad
    working, so the list is the incidents until a reader says otherwise
    (docs/ui/README.md).

    A routine row carries the station's own words and none of the numbers:
    there is nothing to count about a flip that cleared.
    """
    assert drew(A_CLEAN_FLIP)["entries"] == []
    rows = drew(A_CLEAN_FLIP, routine=True)["entries"]
    assert [row["says"] for row in rows] == ["<p0 C>", invert("C"), "<p1 C>"]
    for row in rows:
        assert row["routine"] is True
        assert (row["kind"], row["trips"], row["milliamps"], row["cut"]) == (
            "",
            "",
            "",
            "",
        )


@pytest.mark.node
def test_the_rows_are_newest_first() -> None:
    """What a person opens the view with is what happened last.

    Where a routine line and an incident carry the same stamp the incident is
    first: it is the thing to look at.
    """
    rows = drew(A_TRIP_AND_A_LINK_LOSS, routine=True)["entries"]
    assert [row["at"] for row in rows] == sorted(
        (row["at"] for row in rows), reverse=True
    )
    assert [(row["kind"], row["district"]) for row in rows][:2] == [
        ("link", "station"),
        ("trip", "C"),
    ]


@pytest.mark.node
def test_the_link_line_is_under_both_the_outage_and_the_trip_it_ended() -> None:
    """One line, two rows, and neither is a reading the other made: the trip
    ends where the station stopped answering, and the outage starts there."""
    outage, cut = drew(A_TRIP_AND_A_LINK_LOSS)["entries"]
    assert [line["said"] for line in outage["lines"]] == ["link down", "link up"]
    assert [line["said"] for line in cut["lines"]][-1] == "link down"


@pytest.mark.node
@pytest.mark.parametrize("why", ["stopped", "closed", "silent"])
def test_the_link_line_says_why_the_link_went_down(why: str) -> None:
    """The reason the translator wrote is drawn after `link down` (#367)."""
    (outage,) = drew([down(3_000, why=why), up(5_000)])["entries"]
    assert [line["said"] for line in outage["lines"]] == [
        f"link down: {why}",
        "link up",
    ]


@pytest.mark.node
def test_a_link_line_written_before_the_reason_reads_as_it_did() -> None:
    """A `down` line with no `why` is one written before #367."""
    (outage,) = drew([down(3_000), up(5_000)])["entries"]
    assert [line["said"] for line in outage["lines"]] == ["link down", "link up"]


@pytest.mark.node
def test_the_station_s_own_row_is_the_link_losses_and_the_restarts() -> None:
    """The two things in the journal that are about no district, counted of the
    station and headed by its word (GLOSSARY.md, **station**)."""
    assert drew(A_TRIP_AND_A_LINK_LOSS)["station"] == {
        "district": "station",
        "says": ["1 link loss", "0 restarts"],
    }
    assert drew(TWO_BUILDS)["station"]["says"] == ["0 link losses", "1 restart"]


@pytest.mark.node
def test_a_district_s_row_is_its_counts_in_the_words_they_are_drawn_in() -> None:
    """One cell per column, in the order the columns are, so the component is
    handed a row of words rather than deciding which number goes where."""
    drawn = cells(drew(POWERED), "A")
    assert drawn == {
        "repeated reversal": "0",
        "reversal": "0",
        "slow reversal": "0",
        "trip": "1",
        "spike": "0",
        "trips": "1",
        "peak mA": "3120 mA",
        "cut": "5 m 00 s",
        "flips": "0",
        "hours": "0.50 h",
        "per hour": "2.00",
    }


@pytest.mark.node
def test_a_reading_nobody_took_is_blank_and_every_count_is_a_number() -> None:
    """A district that was never powered has no rate, and one the station
    printed no current about has no peak: a zero somebody could count there
    would be a measurement nobody made (ADR-0009 d.2). The hours are a number,
    because the file does say the district was powered for none of itself."""
    drawn = cells(drew(A_SLOW_FLIP), "D")
    assert drawn["per hour"] == ""
    assert drawn["peak mA"] == ""
    assert drawn["hours"] == "0.00 h"
    assert drawn["slow reversal"] == "1"


@pytest.mark.node
def test_the_columns_are_the_district_the_kinds_and_the_counts() -> None:
    """The kinds are the reading module's, so a kind that arrives there is a
    column here and not a column somebody has to add."""
    assert own()["headings"] == [
        "district",
        "repeated reversal",
        "reversal",
        "slow reversal",
        "trip",
        "spike",
        "trips",
        "peak mA",
        "cut",
        "flips",
        "hours",
        "per hour",
    ]


@pytest.mark.node
def test_the_list_is_headed_by_its_own_columns() -> None:
    """The list is headed once, and its numbers are named as the table names
    them."""
    assert own()["columns"] == ["when", "district", "kind", "trips", "peak mA", "cut"]


@pytest.mark.node
def test_the_periods_are_the_three_spans_and_the_builds_in_the_file() -> None:
    """Newest build first, because the last one in the file is what the station
    is running now. The empty build is not one of them: it is the station not
    answering rather than something it was running (GLOSSARY.md, **build**)."""
    (served,) = run([{"served": lines(TWO_BUILDS)}])
    assert served["choices"] == ["all", "last day", "last 7 days", BUILD, BEFORE]
    assert served["builds"] == [BUILD, BEFORE]


@pytest.mark.node
def test_the_two_spans_are_counted_back_from_when_the_journal_was_read() -> None:
    """The page hands its clock in, so nothing in the module keeps one: the
    same file and the same instant read the same way for ever."""
    day, week, whole, build = run(
        [
            {"choice": "last day", "now": NOW},
            {"choice": "last 7 days", "now": NOW},
            {"choice": "all", "now": NOW},
            {"choice": BUILD, "now": NOW},
        ]
    )
    assert day == {"start": "2026-10-11T19:00:00.000Z"}
    assert week == {"start": "2026-10-05T19:00:00.000Z"}
    assert whole == {}, "the whole file is no bounds at all"
    assert build == {"build": BUILD}, "anything else is a build"


@pytest.mark.node
def test_a_build_chosen_draws_only_what_the_station_said_on_it() -> None:
    """What happened while the station was running this, which is how the
    question is asked (ADR-0022 d.2)."""
    rows = drew(TWO_BUILDS, {"build": BUILD}, routine=True)["entries"]
    assert [row["kind"] for row in rows if not row["routine"]] == ["trip"]
    for row in rows:
        assert row["when"] >= "2026-10-12 18:00:04"


@pytest.mark.node
def test_a_line_the_translator_had_not_finished_writing_is_dropped() -> None:
    """The mirror serves the file while the translator appends to it (ADR-0022
    d.4), so the last line can be half written. The rest of the file is read,
    and a line with no stamp is dropped the same way: everything the view says
    is of when something happened."""
    (served,) = run([{"served": lines(A_CLEAN_FLIP) + '{"at": "2026-10-12T18:00:0'}])
    assert len(served["lines"]) == len(A_CLEAN_FLIP)
    (nothing,) = run([{"served": '{"railroad": "gleis49"}\n[]\n7\n'}])
    assert nothing["lines"] == []


@pytest.mark.node
def test_a_journal_with_nothing_in_it_draws_no_rows_at_all() -> None:
    """A box where the translator has only just come up. What stands in its
    place is the page's own sentence, which is drawn by the view."""
    assert drew([], routine=True) == {
        "districts": [],
        "station": {"district": "station", "says": ["0 link losses", "0 restarts"]},
        "entries": [],
    }
    assert own()["says"]["EMPTY"] != own()["says"]["UNREADABLE"]


@pytest.mark.node
def test_the_file_s_size_is_drawn_in_the_unit_it_is_spelt_in() -> None:
    """`kB` is a thousand bytes, which is what a reader comparing it against a
    disk reads it as. One byte is one byte and not one bytes."""
    drawn = run([{"bytes": size} for size in (0, 1, 999, 1_500, 2_500_000)])
    assert [said["size"] for said in drawn] == [
        "0 bytes",
        "1 byte",
        "999 bytes",
        "1.5 kB",
        "2.5 MB",
    ]


@pytest.mark.node
def test_a_duration_is_drawn_in_the_unit_a_reader_can_hold() -> None:
    """Milliseconds under a second, because the station cuts a district and
    retries it inside one (ADR-0016); seconds under a minute; minutes and
    seconds above that."""
    drawn = (0, 40, 999, 1_000, 1_100, 59_900, 70_000, 119_900, 300_000)
    assert run([{"ms": ms} for ms in drawn]) == [
        "0 ms",
        "40 ms",
        "999 ms",
        "1.0 s",
        "1.1 s",
        "59.9 s",
        "1 m 10 s",
        "2 m 00 s",
        "5 m 00 s",
    ]


@pytest.mark.node
def test_a_stamp_carries_the_day_and_is_the_clock_of_the_machine_reading_it() -> None:
    """The day, because the journal is read a week later and a time alone says
    which minute without saying which evening. Local, because the person
    reading is at the layout correlating what they saw with what the station
    said — the rule the **monitor** stamps a line by, and the same function
    (`monitor.js`).

    The instant itself is not lost to it: it rides on the row's `datetime`
    (`dccex-incidents.ts`).
    """
    for zone, drawn in ZONED.items():
        (stamp,) = run([{"at": at(1_100)}], zone)
        assert stamp == drawn, f"a clock in {zone} draws it otherwise"
        assert DRAWN.match(stamp) is not None


@pytest.mark.node
def test_the_words_the_controls_are_pressed_with_are_the_module_s() -> None:
    """Every sentence an operator reads on this view, asserted as the words
    they are rather than against the template that would show them."""
    says = own()["says"]
    assert says["ALL"] == "all"
    assert says["DAY"] == "last day"
    assert says["WEEK"] == "last 7 days"
    assert says["STATION"] == "station"
    assert says["RELOADS"] == "reload"
    assert says["DOWNLOADS"] == "download"
    assert says["ROUTINE"] == "show routine lines"
    assert own()["spans"] == ["all", "last day", "last 7 days"]


@pytest.mark.node
def test_the_same_journal_draws_the_same_whatever_was_drawn_before_it() -> None:
    """No state between readings, so a view that read one period does not draw
    the next one differently (ADR-0022 d.5)."""
    asks: list[dict[str, Any]] = [
        {"journal": POWERED},
        {"journal": TWO_BUILDS, "routine": True},
        {"journal": A_CLEAN_FLIP, "period": {"build": BUILD}},
    ]
    assert run(asks) == run(asks[::-1])[::-1]


def test_the_view_s_reading_holds_no_clock_and_no_socket() -> None:
    """A pure function of the lines, the period and the instant it is handed
    (ADR-0022 d.5), so that a file from last week draws the same way twice.

    `Date` is not one of the reaches: a stamp on a line becomes a distance and
    an instant becomes a bound through it, which is the clock the journal
    carries rather than the one the machine is set to. The clock the machine is
    set to arrives as an argument, and `Date.now` is what a module that reached
    for one itself would say (`tests/ui/test_journal.py`, `monitor.js`).
    """
    source = code(INCIDENTS.read_text())
    assert 'from "./journal.js"' in source, "the view reads the journal itself"
    assert 'from "./monitor.js"' in source, "the view stamps a line its own way"
    for held in HELD:
        if held == "Date":
            continue
        assert held not in source, f"the view's reading reaches {held}"
    assert "Date.now" not in source, "the view's reading reaches for a clock"


def test_the_components_write_none_of_the_module_s_sentences_out_again() -> None:
    """A word drawn in a template is a word two places can disagree about, and
    the one that is run is the module's (`tests/ui/test_releases.py`).

    Held against the literals rather than the file, because the prose says
    these words to explain what is drawn and saying a word is not drawing it.
    The sentences rather than every word: a one-word label is the class on the
    element it is drawn in as well, and a check reading literals cannot tell
    `station` the word from `station` the selector.
    """
    says = [said for said in own()["says"].values() if " " in said]
    for component in (VIEW, TABLE, LIST, CONTROLS):
        written = quoted(component.read_text())
        for word in says:
            assert word not in written, f"{component.name} writes {word!r} out again"


def test_the_pane_holds_no_counterparty_of_its_own() -> None:
    """The page asks the **face** and hands the answers down, as it does with
    the releases and the **script** (the organisation's ADR-0002,
    `dccex-app.ts`).

    The view is handed what reads the journal; the three
    components under it are handed words and rows. A pane that fetched would be
    a second answer to what the page talks to.
    """
    for component in (VIEW, TABLE, LIST, CONTROLS):
        drawn = code(component.read_text())
        for reached in ("fetch(", "new WebSocket", "new Bus("):
            assert reached not in drawn, f"{component.name} reaches {reached}"
    view = code(VIEW.read_text())
    assert "this.reads()" in view, "the view asks nobody for the journal"


def test_the_view_asks_on_opening_and_on_the_reload_and_on_no_schedule() -> None:
    """A record read afterwards is not a reading that moves under the eye, and
    the page takes the pane away when another **view** is showing — so coming
    to the journal is what asks for it (ADR-0010, `dccex-app.ts`).

    What a press does is asserted by mounting the pane
    (`ui/test/journal.test.ts`); what is held here is that there is no timer to
    find.
    """
    drawn = code(VIEW.read_text())
    assert "connectedCallback" in drawn, "the view never asks"
    for held in ("setInterval", "setTimeout"):
        assert held not in drawn, f"the view polls the journal with {held}"
