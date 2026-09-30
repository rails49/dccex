"""What the **band** and the **tile**s read, given the facts a page hands them.

Scenarios: the station said these lines at these moments, and it is now — so
the band reads this and the tiles read that. Every reading on the page is made of what the station
said, decoded on the page (ADR-0008 d.2), so a scenario is a conversation and
nothing else, and the readings are a pure function of it.

**They are run rather than read**, as the decoder's pairs and the box's are
(`tests/ui/test_decoder.py`, `tests/ui/test_message.py`), and for the reason
this issue's criterion names: what a page shows an operator is worth nothing
asserted against the source that would produce it. The scenarios go through the
real functions under `node`, by way of `tests/ui/readings.mjs`.

What cannot be run here is Lit. The gate is Python and the node beside it is a
bare one with no packages, so nothing in either can mount a component and read
the DOM back:
`control`'s band test renders, and this renders the readings the band draws and
holds the drawing itself against the component's source
(`tests/ui/test_band.py`, `tests/ui/test_tiles.py`). The words an operator sees
are asserted here; that those words reach the screen is the part a Python gate
cannot reach, which is the cost `tests/ui/test_look.py` already names.
"""

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import pytest

from tests.ui.node import HELD, ran
from tests.ui.test_look import UI
from tests.ui.test_stream import code

#: The readings, and the module they are the whole of.
READINGS = UI / "src" / "readings.js"

#: What puts a scenario through them.
RUNNER = Path(__file__).resolve().parent / "readings.mjs"

#: A moment on the page's clock. The scenarios are written around it so that
#: nothing in them reads as an offset from zero by accident.
NOW = 1_000_000


def silent_ms() -> int:
    """`SILENT_MS`, read out of the module that exports it: how long the
    station may say nothing before the **link** is down."""
    match = re.search(r"SILENT_MS\s*=\s*(\d+)", READINGS.read_text())
    assert match is not None, "the readings say nothing about when the link is down"
    return int(match.group(1))


def run(scenarios: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    """What a page would be drawing for each of `scenarios`, in one running."""
    drawn: list[dict[str, Any]] = ran(RUNNER, list(scenarios), "the readings")
    return tuple(drawn)


def drawn(**scenario: Any) -> dict[str, Any]:
    """What a page would be drawing, for one scenario."""
    return run((scenario,))[0]


def band(**scenario: Any) -> dict[str, Any]:
    """What the band carries: the **build**, the **link** and the power
    button."""
    carried: dict[str, Any] = drawn(**scenario)["band"]
    return carried


def power(**scenario: Any) -> dict[str, Any]:
    """What the band's power button is, says and sends."""
    pressed: dict[str, Any] = band(**scenario)["power"]
    return pressed


def tiles(**scenario: Any) -> dict[str, dict[str, Any]]:
    """One **tile** per track in use, by the letter of each.

    Keyed by the letter rather than listed, because what a tile reads is four
    readings and a failure that named the track is the one worth reading. The
    order is asserted on its own below, off the same answer.
    """
    return {tile["track"]: tile for tile in drawn(**scenario)["tiles"]}


BANNER = "<iDCC-EX V-5.0.7 / MEGA / STANDARD_MOTOR G-9db6d10>"

#: One poll's answer from the station on the layout (5.6.4, EX-CSB1), trimmed
#: to what the readings are made of: power on A and B, off on C, every track
#: MAIN, the current on each and the most each may draw.
POLLED = (
    "<p1 A>",
    "<p1 B>",
    "<p0 C>",
    "<p1>",
    "<jI 120 2 0 0>",
    "<jG 1233 1233 250 250>",
    "<= A MAIN>",
    "<= B MAIN>",
    "<= C MAIN>",
    "<= D NONE>",
)

#: A station that has just said everything it has to say about itself.
TALKING: tuple[tuple[str, int], ...] = (
    (BANNER, NOW - 30),
    *((line, NOW - 20) for line in POLLED),
)


@lru_cache(maxsize=1)
def live() -> dict[str, Any]:
    """The page a moment after the station answered a poll."""
    return drawn(said=list(TALKING), now=NOW)


@pytest.mark.node
def test_the_band_carries_the_build_the_link_and_the_power_button() -> None:
    """The band is the **build**, the **link** and one control, and nothing
    else (CONTEXT.md **band**, ADR-0011). A reading added without a scenario
    beside it is a reading an operator can be shown that nobody ever read
    (ADR-0009 d.3)."""
    assert sorted(live()["band"]) == ["answering", "build", "power", "says"]


@pytest.mark.node
def test_the_band_reads_the_build_the_link_and_the_power_off_a_station() -> None:
    """The whole of it, off a station that is answering with its rails hot.

    The words are what a reader who cannot see the dot is given, and the band
    draws them beside it only while the link is down (`ui/test/band.test.ts`).
    The button is named for what a press will do, which is cut the power.
    """
    assert band(said=list(TALKING), now=NOW) == {
        "build": "9db6d10",
        "answering": True,
        "says": "answering",
        "power": {"hot": True, "does": "power off", "sends": "<0>"},
    }


@pytest.mark.node
def test_the_power_button_turns_power_on_where_the_station_says_it_is_off() -> None:
    """Red, and a press sends `<1>` (ADR-0011 d.1)."""
    assert power(said=[("<p0>", NOW - 10)], now=NOW) == {
        "hot": False,
        "does": "power on",
        "sends": "<1>",
    }


@pytest.mark.node
def test_a_track_named_on_the_line_is_still_the_power_as_a_whole() -> None:
    """`<p1 MAIN>` is the station saying power is on for every MAIN track,
    which is a rail somebody can be shocked by and a button that cuts it."""
    assert power(said=[("<p1 MAIN>", NOW - 10)], now=NOW)["sends"] == "<0>"


@pytest.mark.node
def test_any_track_on_is_a_button_that_cuts_the_power() -> None:
    """`<p0 C>` is track C's power and the rest of them are still hot, so the
    press to offer is the one that cuts (ADR-0011 d.1). The track's own tile
    says C is off."""
    said = [("<p1>", NOW - 20), ("<p0 C>", NOW - 10)]
    assert power(said=said, now=NOW) == {
        "hot": True,
        "does": "power off",
        "sends": "<0>",
    }
    assert tiles(said=said, now=NOW)["C"]["hot"] is False


@pytest.mark.node
def test_a_track_on_with_the_power_as_a_whole_off_still_cuts() -> None:
    """The station's word on power as a whole and its word on one track are
    both readings of it, and either one saying `on` is a rail somebody can be
    shocked by."""
    said = [("<p0>", NOW - 20), ("<p1 A>", NOW - 10)]
    assert power(said=said, now=NOW)["sends"] == "<0>"


@pytest.mark.node
def test_there_is_a_tile_per_track_in_use_in_letter_order() -> None:
    """One per track whose mode is not NONE, in letter order (CONTEXT.md
    **tile**, issue 170). D is set to NONE, which is a track not in use.

    The **link** and the **build** are not among them: the **band** carries
    both.
    """
    assert [tile["track"] for tile in live()["tiles"]] == ["A", "B", "C"]


@pytest.mark.node
def test_a_tile_reads_a_track_s_power_mode_current_and_limit() -> None:
    """The readings a tile is, and nothing else. A reading added without a
    scenario beside it is one an operator can be shown that nobody ever read
    (ADR-0009 d.3).

    The power is there twice and is one reading: the colour the symbol takes,
    and the same thing in words for a reader who cannot see it (issue 168).
    C's power is off and its current is still what the station last measured on
    it — the symbol says the power and the number says the current, which are
    two readings and not one.
    """
    assert tiles(said=list(TALKING), now=NOW) == {
        "A": {
            "track": "A",
            "hot": True,
            "says": "track A power is on",
            "mode": "MAIN",
            "draws": "120 mA",
            "most": "1233 mA",
        },
        "B": {
            "track": "B",
            "hot": True,
            "says": "track B power is on",
            "mode": "MAIN",
            "draws": "2 mA",
            "most": "1233 mA",
        },
        "C": {
            "track": "C",
            "hot": False,
            "says": "track C power is off",
            "mode": "MAIN",
            "draws": "0 mA",
            "most": "250 mA",
        },
    }


@pytest.mark.node
def test_a_track_whose_mode_is_not_known_yet_is_still_drawn() -> None:
    """A current arrives before the mode has: the track has a tile and its mode
    is blank until the station says what it is set to."""
    assert tiles(said=[("<jI 40>", NOW)], now=NOW) == {
        "A": {
            "track": "A",
            "hot": None,
            "says": "track A power is unknown",
            "mode": "",
            "draws": "40 mA",
            "most": "",
        },
    }


@pytest.mark.node
def current(*milliamps: int) -> str:
    """What track A's tile reads as its current after these readings, one a
    second."""
    said = [(f"<jI {ma}>", NOW - 10 + i) for i, ma in enumerate(milliamps)]
    draws: str = tiles(said=said, now=NOW)["A"]["draws"]
    return draws


def test_the_current_is_the_mean_of_the_last_eight_readings() -> None:
    """The station's samples scatter around the real current; their mean is
    the reading. These are the first eight track A gave on 2026-09-25 with a
    loco running at constant speed."""
    assert current(120, 11, 64, 97, 64, 100, 62, 13) == "66 mA"


def test_only_the_last_eight_readings_count() -> None:
    """An old reading falls out of the mean, so a step is fully shown two
    seconds after it happened."""
    assert current(900, *[100] * 8) == "100 mA"
    assert current(*[100] * 4, *[300] * 4) == "200 mA"


def test_the_first_readings_are_averaged_as_they_come() -> None:
    """Before there are eight, the mean is of what there is: a blank tile for
    the first two seconds would be a reading withheld."""
    assert current(40) == "40 mA"
    assert current(40, 60) == "50 mA"


@pytest.mark.node
def test_a_line_the_decoder_does_not_know_is_still_the_station_speaking() -> None:
    """This fork answers a subset of DCC-EX's vocabulary and upstream adds to
    it (ADR-0009 d.5). A line the page cannot gloss is a station that is
    plainly answering, and a **link** that went down under one would be the
    page calling a talking station dead."""
    assert band(said=[("<l 3 0 128 0>", NOW - 10)], now=NOW)["answering"] is True


@pytest.mark.node
def test_a_station_that_says_nothing_is_a_link_that_is_down() -> None:
    """Before anything has arrived, and with no socket anywhere in it: the
    **link** is the station answering rather than a socket being open
    (ADR-0008, control ADR-0066)."""
    assert band(now=NOW) == {
        "build": "",
        "answering": False,
        "says": "dcc-ex offline",
        "power": {"hot": None, "does": "power", "sends": None},
    }
    assert tiles(now=NOW) == {}


@pytest.mark.node
def test_a_link_that_is_down_says_so_in_words() -> None:
    """The dot is the reading for a reader looking at it and the words are the
    same reading for one who is not, which is why there are words in both
    states; a station that is not answering is a fault and is owed them beside
    the dot as well (#138, issue 168, `ui/test/band.test.ts`)."""
    assert band(now=NOW)["says"] == "dcc-ex offline"
    assert band(said=list(TALKING), now=NOW + silent_ms())["says"] == "dcc-ex offline"
    assert band(said=list(TALKING), now=NOW)["says"] == "answering"


@pytest.mark.node
def test_the_power_button_presses_nothing_while_the_link_is_down() -> None:
    """Power is then unknown and a press would reach a station that is not
    answering (ADR-0011 d.2). It says what it is rather than what a press
    would do, because there is no press.

    A station that is answering and has said nothing about power yet is the
    same case: what nothing has confirmed is not a colour to draw or a message
    to send (ADR-0009 d.2).
    """
    unknown = {"hot": None, "does": "power", "sends": None}

    assert power(now=NOW) == unknown
    assert power(said=list(TALKING), now=NOW + silent_ms()) == unknown
    assert power(said=[("<jI 40>", NOW - 10)], now=NOW) == unknown


@pytest.mark.node
def test_a_station_that_stops_answering_takes_the_band_and_the_tiles() -> None:
    """The station said all of it and then went quiet past the silence.

    The band says so rather than leaving the page looking merely idle, and the
    tiles go with it — the whole row, because a tile is one track and the
    station has stopped saying there is one. That is the correct reading rather
    than a gap: the station is not talking (ADR-0008 d.3).
    """
    gone: dict[str, Any] = {"said": list(TALKING), "now": NOW + silent_ms()}

    assert band(**gone) == {
        "build": "",
        "answering": False,
        "says": "dcc-ex offline",
        "power": {"hot": None, "does": "power", "sends": None},
    }
    assert tiles(**gone) == {}


@pytest.mark.node
def test_the_link_holds_for_as_long_as_the_silence_is_allowed() -> None:
    """The boundary itself, both sides of it, so the rule is the number the
    module exports rather than whatever a scenario happened to use."""
    said = [("<p1>", NOW)]
    inside = band(said=said, now=NOW + silent_ms())
    outside = band(said=said, now=NOW + silent_ms() + 1)

    assert inside["answering"] is True
    assert outside["answering"] is False


@pytest.mark.node
def test_the_build_blanks_with_the_link_and_fills_again_by_itself() -> None:
    """A stale pre-flash build is never reported as the one on the board, and
    nothing has to be reloaded to get the new one: the station's banner arrives
    on its own when it comes back up (ADR-0008 d.3, ADR-0010 d.4)."""
    flashing = [(BANNER, NOW)]
    back = [*flashing, (BANNER.replace("9db6d10", "0ff1ce5"), NOW + 90_000)]

    assert band(said=flashing, now=NOW + 60_000)["build"] == ""
    assert band(said=back, now=NOW + 90_010)["build"] == "0ff1ce5"


@pytest.mark.node
def test_what_the_station_last_said_is_what_the_readings_read() -> None:
    """Power off after power on offers the press that turns it on, a track
    switched back on after that offers the one that cuts, and the track reads
    its current again: a reading is the station's latest word and not its
    first."""
    said = [
        ("<p1>", NOW - 40),
        ("<p0>", NOW - 30),
        ("<jI 50>", NOW - 25),
        ("<p0 A>", NOW - 20),
        ("<p1 A>", NOW - 10),
    ]

    assert power(said=said[:2], now=NOW)["sends"] == "<1>"
    assert power(said=said, now=NOW)["sends"] == "<0>"
    assert tiles(said=said, now=NOW)["A"]["draws"] == "50 mA"


@pytest.mark.node
def test_a_reading_the_station_has_not_given_is_blank_and_not_a_zero() -> None:
    """A track the station has named but not measured has no current.
    Drawing `0 mA` there would be a reading nobody took (ADR-0009 d.2)."""
    assert tiles(said=[("<= A MAIN>", NOW)], now=NOW)["A"]["draws"] == ""


def test_the_readings_hold_no_clock_and_no_socket() -> None:
    """A pure function of what was said and of the moment it is asked for.

    Held against the source because those are the reaches that would end it:
    a module that read the clock itself could not be asked what the page shows
    fifteen seconds from now, which is the whole of what is asserted above.

    The whole of `HELD` rather than the five names this module was written
    with. A DOM and a `fetch` would spoil it exactly as a clock would, and a
    list that named only some of them held this module to less than its
    siblings for no reason anybody wrote down (#122).

    The one `import` is the **decoder**, and it is the point: a reading is the
    conversation decoded on the page (ADR-0008 d.2), so the module that folds
    the lines in is the module that asks what they mean.
    """
    source = code(READINGS.read_text())
    assert 'from "./decoder.js"' in source, "the readings read a line themselves"
    for held in HELD:
        assert held not in source, f"the readings reach {held}"


@pytest.mark.node
def test_the_same_facts_read_the_same_whatever_was_asked_before() -> None:
    """Given the same conversation they draw the same page for ever, so what
    the band says cannot depend on what some other page asked a moment ago."""
    scenarios: tuple[dict[str, Any], ...] = (
        {"said": list(TALKING), "now": NOW},
        {"now": NOW},
        {"said": [("<p0>", NOW)], "now": NOW},
    )
    assert run(scenarios) == tuple(reversed(run(tuple(reversed(scenarios)))))
