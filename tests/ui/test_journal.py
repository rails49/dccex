"""What the page makes of the **journal**.

Journals, written out here as the translator would have written them, and the
**incident**s and the counts the page reads out of them (ADR-0022 d.5). Being
an incident is a reading of the file and not something in it (d.3), so what is
held here is that reading: which lines are one thing a person should look at,
which are the railroad working, and what the counts beside them come to.

**The function is run rather than read**, as the decoder is and for the same
reason (`tests/ui/test_decoder.py`, ADR-0009 d.3): a rule that decides what an
operator is shown is worth nothing asserted against the source that would
produce it. The journals go through the real function under `node`, by way of
`tests/ui/journal.mjs`, and these checks carry the `node` marker — the gate
does not collect them and the workflow runs them in a job a pull request
requires (`scripts/check.sh`, #101).

**The numbers the flip rules are written with are the page's.** The station
prints no flip count and no peak current, and the right window is not known
before the record exists (ADR-0022, context), so they are named constants and
they are asserted as the numbers they are: a rule that changes is run over the
whole journal again under itself.
"""

from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

import pytest

from tests.ui.node import ran
from tests.ui.test_look import UI

#: The pure function, and the module it is the whole of.
JOURNAL = UI / "src" / "journal.js"

#: What puts the journals through it.
RUNNER = Path(__file__).resolve().parent / "journal.mjs"

#: One line of the journal, as the translator wrote it (ADR-0022 d.2).
Line = dict[str, Any]

#: The railroad every line below was written under. It is on the line so a
#: file read a week later needs nothing beside it, and nothing here reads it.
RAILROAD = "gleis49"

#: What the station said it was running, and the one it was written with
#: before (`TWO_BUILDS`).
BUILD = "v5.6.4-rails49.6"
BEFORE = "v5.6.4-rails49.1"

#: When the journals below start. A fixed instant, because what the rules read
#: is the distance between two stamps and never the hour on either.
OPENED = datetime(2026, 10, 12, 18, 0, 0, tzinfo=UTC)


def at(ms: int) -> str:
    """A stamp `ms` milliseconds into the journal, as a line carries it: ISO
    8601 in UTC, to the millisecond (`src/dccex/journal.py`)."""
    return (OPENED + timedelta(milliseconds=ms)).isoformat(timespec="milliseconds")


def said(
    ms: int,
    message: str,
    *,
    district: str = "",
    mode: str | None = None,
    limit: int | None = None,
    build: str = BUILD,
) -> Line:
    """A line about something the station said: the message whole and
    verbatim, and where it names a district, that district's **mode** and
    **limit** as the station had last reported them.

    Both are `null` where it had not reported yet, which is an ordinary state
    of the first second of a link, and the field is there rather than left out:
    a number somebody could count must not be missing (ADR-0022 d.2).
    """
    line: Line = {
        "at": at(ms),
        "railroad": RAILROAD,
        "build": build,
        "said": message,
    }
    if district:
        line |= {"district": district, "mode": mode, "limit": limit}
    return line


def down(ms: int) -> Line:
    """The station stopped answering. The **build** goes with the link, so the
    line carries none (CONTEXT.md, **build**)."""
    return {"at": at(ms), "railroad": RAILROAD, "build": "", "link": "down"}


def up(ms: int, *, build: str = BUILD) -> Line:
    """The station is answering again."""
    return {"at": at(ms), "railroad": RAILROAD, "build": build, "link": "up"}


def restarted(ms: int, *, build: str = BUILD) -> Line:
    """The station restarted under a railroad that was running (ADR-0021). The
    line is written before the link's readings are forgotten, so it carries
    the build last reported."""
    return {"at": at(ms), "railroad": RAILROAD, "build": build, "restart": True}


def overload(district: str, milliamps: int = 3120) -> str:
    """A district the station cut on an overload, as `MotorDriver.cpp` prints
    it at fork tag `v5.6.4-rails49.6-ocp-test`."""
    return (
        f"<* TRACK {district} POWER OVERLOAD {milliamps}mA (max 3000mA) "
        "detected after    2ms. Pause   40ms *>"
    )


def guarded(district: str, milliamps: int = 4210) -> str:
    """The cut the Guard makes, which comes with no `ALERT` before it (#251,
    ADR-0016 d.3 as amended)."""
    return f"<* TRACK {district} FAST OVERLOAD {milliamps}mA. Pause 100ms *>"


def restore(district: str) -> str:
    """The station retrying a district it cut."""
    return f"<* TRACK {district} POWER RESTORE (after   40ms) *>"


def normal(district: str, milliamps: int = 180) -> str:
    """The district is itself again."""
    return f"<* TRACK {district} NORMAL (after 20ms/40ms) {milliamps}mA *>"


def alert(district: str, milliamps: int = 2900) -> str:
    """The current on a district is over its limit (ADR-0016 d.4)."""
    return f"<* TRACK {district} ALERT  {milliamps}mA *>"


def invert(district: str, *, fast: bool = True) -> str:
    """A reverser flipping a district. `(fast)` is the flip the station made
    in time; without it the station took the long way round."""
    return f"<* TRACK {district} INVERT{' (fast)' if fast else ''} *>"


#: A reverser doing its job: one flip on a district in `MAIN_AUTO`, nothing
#: before it and nothing after it.
A_CLEAN_FLIP: list[Line] = [
    said(0, "<p1 C>", district="C", mode="MAIN_AUTO", limit=3000),
    said(1_000, invert("C"), district="C", mode="MAIN_AUTO", limit=3000),
    said(60_000, "<p0 C>", district="C", mode="MAIN_AUTO", limit=3000),
]

#: The same flip, and the short it did not clear 100 ms later.
A_FLIP_THE_SHORT_OUTLIVED: list[Line] = [
    said(0, "<p1 C>", district="C", mode="MAIN_AUTO", limit=3000),
    said(1_000, invert("C"), district="C", mode="MAIN_AUTO", limit=3000),
    said(1_100, guarded("C"), district="C", mode="MAIN_AUTO", limit=3000),
    said(1_200, restore("C"), district="C", mode="MAIN_AUTO", limit=3000),
    said(1_300, normal("C"), district="C", mode="MAIN_AUTO", limit=3000),
]

#: A reverser that cannot settle: three flips inside 900 ms, and no short at
#: all.
THREE_FLIPS: list[Line] = [
    said(0, "<p1 C>", district="C", mode="MAIN_AUTO", limit=3000),
    said(1_000, invert("C"), district="C", mode="MAIN_AUTO", limit=3000),
    said(1_400, invert("C"), district="C", mode="MAIN_AUTO", limit=3000),
    said(1_900, invert("C"), district="C", mode="MAIN_AUTO", limit=3000),
    said(5_000, "<p0 C>", district="C", mode="MAIN_AUTO", limit=3000),
]

#: One short, and the station retrying it four times before the district is
#: itself again. The retry doubles its wait, which is what the gaps are.
FOUR_RETRIES: list[Line] = [
    said(0, "<p1 B>", district="B", mode="MAIN", limit=3000),
    said(1_000, overload("B"), district="B", mode="MAIN", limit=3000),
    said(1_040, restore("B"), district="B", mode="MAIN", limit=3000),
    said(1_100, overload("B", 3400), district="B", mode="MAIN", limit=3000),
    said(1_180, restore("B"), district="B", mode="MAIN", limit=3000),
    said(1_240, overload("B", 3900), district="B", mode="MAIN", limit=3000),
    said(1_400, restore("B"), district="B", mode="MAIN", limit=3000),
    said(1_500, overload("B", 3200), district="B", mode="MAIN", limit=3000),
    said(1_900, restore("B"), district="B", mode="MAIN", limit=3000),
    said(2_000, normal("B"), district="B", mode="MAIN", limit=3000),
]

#: The same two lines on two districts: a current over the limit that came
#: back by itself, on a main track and on the programming track.
AN_ALERT_ON_EACH: list[Line] = [
    said(0, "<p1 A>", district="A", mode="MAIN", limit=3000),
    said(10, "<p1 B>", district="B", mode="PROG", limit=250),
    said(1_000, alert("A"), district="A", mode="MAIN", limit=3000),
    said(1_200, normal("A"), district="A", mode="MAIN", limit=3000),
    said(2_000, alert("B", 250), district="B", mode="PROG", limit=250),
    said(2_200, normal("B", 20), district="B", mode="PROG", limit=250),
]

#: An alert in the first second of a link, before the station has said what
#: the district is set to.
AN_ALERT_BEFORE_A_MODE: list[Line] = [
    said(0, "<p1 A>", district="A"),
    said(500, alert("A"), district="A"),
    said(700, normal("A"), district="A"),
]

#: A district the station cut, and the link going while it was still cut.
A_TRIP_AND_A_LINK_LOSS: list[Line] = [
    said(0, "<p1 C>", district="C", mode="MAIN", limit=3000),
    said(1_000, overload("C"), district="C", mode="MAIN", limit=3000),
    down(3_000),
    up(5_000),
]

#: Half an hour of power in three quarters of an hour of journal: on, cut a
#: quarter of an hour in, itself again five minutes later, off at the end.
POWERED: list[Line] = [
    said(0, "<p1 A>", district="A", mode="MAIN", limit=3000),
    said(900_000, overload("A"), district="A", mode="MAIN", limit=3000),
    said(1_200_000, normal("A"), district="A", mode="MAIN", limit=3000),
    said(2_100_000, "<p0 A>", district="A", mode="MAIN", limit=3000),
]

#: One file across a flash: a short on the build the station was running, a
#: restart, and another short on the build it came back as.
TWO_BUILDS: list[Line] = [
    said(0, "<p1 A>", district="A", mode="MAIN", limit=3000, build=BEFORE),
    said(1_000, overload("A"), district="A", mode="MAIN", limit=3000, build=BEFORE),
    said(2_000, normal("A"), district="A", mode="MAIN", limit=3000, build=BEFORE),
    restarted(3_000, build=BEFORE),
    said(4_000, "<p1 A>", district="A", mode="MAIN", limit=3000),
    said(5_000, overload("A", 3400), district="A", mode="MAIN", limit=3000),
    said(6_000, normal("A"), district="A", mode="MAIN", limit=3000),
]

#: What the station rode out: a current it watched and a fault pin it did not
#: cut on. Neither is a cut and neither is read.
RODE_OUT: list[Line] = [
    said(0, "<p1 A>", district="A", mode="MAIN", limit=3000),
    said(
        1_000,
        "<* TRACK A CURRENT 2900mA (100ms ignore) *>",
        district="A",
        mode="MAIN",
        limit=3000,
    ),
    said(
        2_000,
        "<* TRACK A FAULT PIN (100ms ignore) *>",
        district="A",
        mode="MAIN",
        limit=3000,
    ),
]

#: A flip the station did not call fast, on a district the file never says
#: the power of: the journal was cleared while the railroad was running.
A_SLOW_FLIP: list[Line] = [
    said(0, invert("D", fast=False), district="D", mode="MAIN_AUTO", limit=3000),
    said(2_000, "<p0 D>", district="D", mode="MAIN_AUTO", limit=3000),
]

#: A journal from before the translator stopped keeping them (#269): the
#: station's answers to `<s>` are still in it, so the bare `<p0>` and `<p1>`
#: and the ones naming a mode group sit among the lines that name a district.
#: A district is cut and comes back while they go by, and another is named by
#: a flip and by no `<p…>` of its own.
LINES_NAMING_NO_DISTRICT: list[Line] = [
    said(0, "<p1 A>", district="A", mode="MAIN", limit=3000),
    said(100, invert("B", fast=False), district="B", mode="MAIN_AUTO", limit=3000),
    said(1_000, overload("A"), district="A", mode="MAIN", limit=3000),
    said(1_040, "<p0 PROG>"),
    said(1_100, "<p0>"),
    said(1_200, "<p1 MAIN>"),
    said(1_300, "<p1>"),
    said(2_000, normal("A"), district="A", mode="MAIN", limit=3000),
    said(3_601_000, "<p0 A>", district="A", mode="MAIN", limit=3000),
]

#: Every journal above, read over the period it is read over. A name, a
#: journal and a period, so that one file read two ways is two of these.
ASKS: dict[str, dict[str, Any]] = {
    "a clean flip": {"journal": A_CLEAN_FLIP},
    "a flip the short outlived": {"journal": A_FLIP_THE_SHORT_OUTLIVED},
    "three flips": {"journal": THREE_FLIPS},
    "four retries": {"journal": FOUR_RETRIES},
    "an alert on each": {"journal": AN_ALERT_ON_EACH},
    "an alert before a mode": {"journal": AN_ALERT_BEFORE_A_MODE},
    "a trip and a link loss": {"journal": A_TRIP_AND_A_LINK_LOSS},
    "powered": {"journal": POWERED},
    "two builds": {"journal": TWO_BUILDS},
    "the build it came back as": {
        "journal": TWO_BUILDS,
        "period": {"build": BUILD},
    },
    "after the restart": {
        "journal": TWO_BUILDS,
        "period": {"start": at(3_500), "end": at(6_500)},
    },
    "what the station rode out": {"journal": RODE_OUT},
    "a slow flip": {"journal": A_SLOW_FLIP},
    "lines naming no district": {"journal": LINES_NAMING_NO_DISTRICT},
    "nothing at all": {"journal": []},
}


def run(asks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """What the function answers for `asks`, in one running of it."""
    answered: list[dict[str, Any]] = ran(RUNNER, asks, "the journal")
    return answered


@lru_cache(maxsize=1)
def readings() -> dict[str, dict[str, Any]]:
    """Every journal the suite has, read once."""
    return dict(zip(ASKS, run([ASKS[name] for name in ASKS]), strict=True))


def incidents(name: str) -> list[dict[str, Any]]:
    """What a person should look at in that journal, in the order it opened."""
    read: list[dict[str, Any]] = readings()[name]["incidents"]
    return read


def district(name: str, letter: str) -> dict[str, Any]:
    """One district's counts over that journal."""
    counts: dict[str, Any] = readings()[name]["districts"][letter]
    return counts


@pytest.mark.node
def test_a_flip_a_reverser_cleared_is_the_railroad_working() -> None:
    """Counted and not an incident.

    Shorts should not happen on this railroad except where a reverser flips a
    district, so the flips that cleared are the ones a count says something
    about and the ones that did not are read below (ADR-0022, context).
    """
    assert incidents("a clean flip") == []
    assert district("a clean flip", "C")["flips"] == 1


@pytest.mark.node
def test_a_flip_and_a_cut_within_the_window_are_one_reversal() -> None:
    """One incident and not two, and it reads as the reversal rather than as
    the trip: what the district did is why it cut."""
    (one,) = incidents("a flip the short outlived")
    assert one["kind"] == "reversal"
    assert one["district"] == "C"
    assert one["trips"] == 1
    assert one["milliamps"] == 4210
    assert one["start"] == at(1_100)
    assert one["end"] == at(1_300)


@pytest.mark.node
def test_the_flip_a_cut_followed_is_not_counted_as_a_clean_one() -> None:
    """It is in the incident, and a count of the reverser doing its job that
    held it would say the job was done."""
    assert district("a flip the short outlived", "C")["flips"] == 0


@pytest.mark.node
def test_three_flips_inside_the_second_are_a_reverser_that_cannot_settle() -> None:
    """A third flip on one district inside `REPEATED_MS`, with no short at all:
    nothing the station says is a trip, and it is still the thing to look at.
    """
    (one,) = incidents("three flips")
    assert one["kind"] == "repeated reversal"
    assert one["district"] == "C"
    assert one["trips"] == 0
    assert one["milliamps"] is None


@pytest.mark.node
def test_the_flips_the_third_counted_are_part_of_what_it_says() -> None:
    """A burst of three is one reading and not an incident with two good flips
    beside it."""
    assert district("three flips", "C")["flips"] == 0


@pytest.mark.node
def test_a_short_the_station_retried_is_one_incident_with_its_retries() -> None:
    """However many times the station cut it in between (CONTEXT.md,
    **incident**). The peak is the highest current printed in it, and the
    limit beside each is the setting rather than a reading."""
    (one,) = incidents("four retries")
    assert one["kind"] == "trip"
    assert one["trips"] == 4
    assert one["milliamps"] == 3900
    assert one["start"] == at(1_000)
    assert one["end"] == at(2_000)


@pytest.mark.node
def test_the_time_cut_is_each_cut_until_the_station_restored_it() -> None:
    """Trip to the next `POWER RESTORE`, four times over, and the retry's wait
    doubling is what the sum is made of."""
    (one,) = incidents("four retries")
    assert one["cut"] == 40 + 80 + 160 + 400
    assert district("four retries", "B")["cut"] == one["cut"]
    assert district("four retries", "B")["trips"] == 4


@pytest.mark.node
def test_a_current_over_the_limit_that_came_back_is_a_spike() -> None:
    """An alert that ended in normal with nothing cut. A current over the
    district's limit is what the station prints one for, and a spike under it
    is not seen at all (ADR-0022 d.6)."""
    (one,) = incidents("an alert on each")
    assert one["kind"] == "spike"
    assert one["district"] == "A"
    assert one["trips"] == 0
    assert one["milliamps"] == 2900


@pytest.mark.node
def test_the_same_two_lines_on_the_programming_track_are_the_track_working() -> None:
    """A decoder acknowledging draws the current the programming track is
    watching for, and an alert there that ended in normal is what the page is
    told not to call an incident (CONTEXT.md, **incident**)."""
    counts = district("an alert on each", "B")
    assert counts["incidents"]["spike"] == 0
    assert sum(counts["incidents"].values()) == 0


@pytest.mark.node
def test_an_alert_before_the_station_said_a_mode_is_read_all_the_same() -> None:
    """`mode` is `null` through the first second of a link, and a line the
    page cannot place on a programming track is not a line it passes over."""
    (one,) = incidents("an alert before a mode")
    assert one["kind"] == "spike"


@pytest.mark.node
def test_a_trip_the_link_ended_closes_where_the_link_went() -> None:
    """What cannot be read is not what was last read: the district may have
    come back while nobody could hear it, so the incident ends at the line
    that says the station stopped answering."""
    cut, outage = incidents("a trip and a link loss")
    assert cut["kind"] == "trip"
    assert cut["end"] == at(3_000)
    assert cut["cut"] == 2_000
    assert outage["kind"] == "link"
    assert outage["district"] is None
    assert outage["start"] == at(3_000)
    assert outage["end"] == at(5_000)


@pytest.mark.node
def test_an_incident_names_the_journal_lines_it_is_made_of() -> None:
    """By their place in the journal it was read out of.

    Which lines are an incident's is this module's reading and not the view's
    (ADR-0022 d.3): the flip a short outlived is one of them and it is before
    the line the reading opened at, and the line that closed it is one of them
    too. A view reading a window off the start and the end would get both
    wrong, so the reading says which lines it took (#266,
    `tests/ui/test_incidents.py`).
    """
    (one,) = incidents("a flip the short outlived")
    assert one["taken"] == [1, 2, 3, 4], "the flip, the cut, the retry, the normal"
    (burst,) = incidents("three flips")
    assert burst["taken"] == [1, 2, 3, 4], "three flips and the power going off"
    cut, _ = incidents("a trip and a link loss")
    assert cut["taken"] == [1, 2], "the cut, and the link going while it was cut"
    (slow,) = incidents("a slow flip")
    assert slow["taken"] == [0, 1], "the flip, and the power going off"


@pytest.mark.node
def test_the_stations_own_incident_takes_the_lines_that_name_no_district() -> None:
    """A restart is the one line it is written on, and an outage is the line
    the link went on and the line it came back on. A district's words inside
    the same seconds are that district's, which is why they are separate
    readings."""
    (rode,) = [line for line in incidents("two builds") if line["kind"] == "restart"]
    assert rode["taken"] == [3]
    _, outage = incidents("a trip and a link loss")
    assert outage["taken"] == [2, 3]


@pytest.mark.node
def test_the_link_losses_and_the_restarts_are_the_stations_own() -> None:
    """They are about no district, so they are counted where the journal says
    them: of the station."""
    assert readings()["a trip and a link loss"]["station"] == {
        "links": 1,
        "restarts": 0,
    }
    assert readings()["two builds"]["station"] == {"links": 0, "restarts": 1}


@pytest.mark.node
def test_powered_is_on_until_the_district_is_cut_and_on_again_from_normal() -> None:
    """A quarter of an hour, then the station cuts it, then a quarter of an
    hour from the line that says it is itself again: half an hour powered out
    of thirty-five minutes of journal, and the incident read against that
    half hour rather than against the wall clock."""
    counts = district("powered", "A")
    assert counts["hours"] == 0.5
    assert counts["cut"] == 300_000
    assert counts["rate"] == 2.0


@pytest.mark.node
def test_a_flip_the_station_did_not_call_fast_is_a_slow_reversal() -> None:
    """`INVERT` without the station's `(fast)`: the reverser got there and
    took the long way round, which is the thing to look at before it does not
    get there at all."""
    (one,) = incidents("a slow flip")
    assert one["kind"] == "slow reversal"
    assert one["district"] == "D"
    assert district("a slow flip", "D")["flips"] == 0


@pytest.mark.node
def test_a_district_the_file_never_says_the_power_of_has_no_rate() -> None:
    """A rate over no time is a number nobody can read, and a zero there is
    one somebody would count (ADR-0009 d.2). The hours are zero, which is a
    number: the file says the district was powered for none of itself."""
    counts = district("a slow flip", "D")
    assert counts["hours"] == 0
    assert counts["rate"] is None


@pytest.mark.node
def test_a_power_line_naming_no_district_is_passed_over() -> None:
    """The bare `<p0>` and `<p1>`, and the ones naming `MAIN`, `PROG` or
    `JOIN`: the station prints them after a `<pN X>` line for each district,
    so they say nothing those do not, and the page reads them as the
    translator does (`replies.kept`, ADR-0022 d.2 as amended). The trip ends
    on the `NORMAL` rather than on the `<p0 PROG>` 40 ms after the cut, and
    neither line is part of what either incident is made of.
    """
    cut, slow = incidents("lines naming no district")
    assert cut["kind"] == "trip"
    assert cut["district"] == "A"
    assert cut["end"] == at(2_000)
    assert cut["cut"] == 1_000
    assert cut["taken"] == [2, 7], "the cut and the normal"
    assert slow["kind"] == "slow reversal"
    assert slow["end"] == at(3_601_000)
    assert slow["taken"] == [1], "the flip"


@pytest.mark.node
def test_a_power_line_naming_no_district_powers_no_district() -> None:
    """A district the file says no `<pN X>` about was powered for none of the
    journal, whatever the lines naming none of them said. The one the file
    does say it about is powered across them."""
    assert district("lines naming no district", "B")["hours"] == 0
    assert district("lines naming no district", "B")["rate"] is None
    assert district("lines naming no district", "A")["hours"] == 1.0
    assert district("lines naming no district", "A")["rate"] == 1.0


@pytest.mark.node
def test_a_period_by_build_counts_only_that_builds_lines() -> None:
    """What happened while the station was running this, which is how the
    question is asked. The restart is on the line before the flash and is not
    in it."""
    assert len(incidents("two builds")) == 3
    (one,) = incidents("the build it came back as")
    assert one["start"] == at(5_000)
    assert one["milliamps"] == 3400
    assert district("the build it came back as", "A")["trips"] == 1
    assert readings()["the build it came back as"]["station"] == {
        "links": 0,
        "restarts": 0,
    }


@pytest.mark.node
def test_a_period_by_a_start_and_an_end_reads_the_lines_between_them() -> None:
    """The other way a period is given, over the same file."""
    (one,) = incidents("after the restart")
    assert one["start"] == at(5_000)
    assert one["end"] == at(6_000)


@pytest.mark.node
def test_a_line_the_station_rode_out_is_not_an_incident() -> None:
    """A current it watched and a fault pin it did not cut on. The words it
    cuts a district with are `POWER OVERLOAD`, `FAST OVERLOAD` and `FAULT PIN
    detected`, and the page reads no further than them (ADR-0016 d.3)."""
    assert incidents("what the station rode out") == []
    assert district("what the station rode out", "A")["trips"] == 0


@pytest.mark.node
def test_a_journal_with_nothing_in_it_reads_as_nothing() -> None:
    """A box where the translator has only just come up, and the page that
    draws it has nothing to say rather than nothing to draw."""
    assert readings()["nothing at all"] == {
        "incidents": [],
        "districts": {},
        "station": {"links": 0, "restarts": 0},
    }


@pytest.mark.node
def test_every_kind_is_a_number_on_every_district() -> None:
    """Zero where nothing of that kind happened, rather than a kind that is
    not there: a reader counting down a column reads a number in every row
    (ADR-0009 d.2)."""
    counts = district("four retries", "B")["incidents"]
    assert counts == {
        "repeated reversal": 0,
        "reversal": 0,
        "slow reversal": 0,
        "trip": 1,
        "spike": 0,
    }


@pytest.mark.node
def test_the_windows_a_flip_is_read_against_are_named() -> None:
    """The station prints no flip count and the right numbers were not known
    before the record existed (ADR-0022, context), so they are the page's own
    and they are here to be changed under the whole journal again."""
    (own,) = run([{"own": True}])
    assert own["flipped"] == 250
    assert own["repeats"] == 3
    assert own["repeated"] == 1000
    assert own["kinds"] == [
        "repeated reversal",
        "reversal",
        "slow reversal",
        "trip",
        "spike",
    ]


@pytest.mark.node
def test_the_same_journal_reads_the_same_whatever_was_read_before_it() -> None:
    """No state between readings, so a page that read one period does not read
    the next one differently (ADR-0022 d.5)."""
    asks = [ASKS[name] for name in ASKS]
    assert run(asks) == run(asks[::-1])[::-1]


def test_the_journal_is_read_with_no_clock_and_no_socket() -> None:
    """A pure function of the lines and the period (ADR-0022 d.5).

    Held against the source because those are the reaches that would end it: a
    module that read the clock itself could not be asked what a file from last
    week comes to, and the whole of what is asserted above is a file and a
    reading of it.

    `Date.parse` is not one of them and is how a stamp becomes a distance. It
    is the clock the journal carries rather than the one the machine is set
    to, which is the distinction `monitor.js` is held to in the same words
    (`tests/ui/test_monitor.py`).

    The one `import` is the **decoder**: a `<p…>` is the station's syntax and
    is known in one place (ADR-0009 d.3). The `<* TRACK X … *>` lines are read
    here, being the ones the decoder has no gloss for.
    """
    source = JOURNAL.read_text()
    assert 'from "./decoder.js"' in source, "the journal reads a line itself"
    for held in (
        "new Date(",
        "Date.now",
        "Math.random",
        "setTimeout",
        "setInterval",
        "window",
        "document",
        "querySelector",
        "fetch",
        "WebSocket",
    ):
        assert held not in source, f"the journal reaches {held}"
