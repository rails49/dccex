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

from tests.ui.node import ran
from tests.ui.test_look import UI

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


def band(**scenario: Any) -> dict[str, str]:
    """What the band reads, by the name of each reading on it."""
    return {shown["of"]: shown["reads"] for shown in drawn(**scenario)["band"]}


def tiles(**scenario: Any) -> dict[str, str]:
    """What the tiles read, by the name of each."""
    return {shown["of"]: shown["reads"] for shown in drawn(**scenario)["tiles"]}


BANNER = "<iDCC-EX V-5.0.7 / MEGA / STANDARD_MOTOR G-9db6d10>"

#: One poll's answer from the station on the layout (5.6.4, EX-CSB1), trimmed
#: to what the readings are made of: power on A and B, off on C, every track
#: MAIN, and the current on each.
POLLED = (
    "<p1 A>",
    "<p1 B>",
    "<p0 C>",
    "<p1>",
    "<jI 120 2 0 0>",
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


def light(**scenario: Any) -> bool:
    """Whether the link light is on."""
    lit: bool = drawn(**scenario)["tiles"][0]["lit"]
    return lit


@lru_cache(maxsize=1)
def live() -> dict[str, Any]:
    """The page a moment after the station answered a poll."""
    return drawn(said=list(TALKING), now=NOW)


@pytest.mark.node
def test_the_band_carries_two_readings() -> None:
    """The band is the link and whether the rails are hot, and nothing else
    (CONTEXT.md, **band**). A reading added without a scenario beside it is a
    reading an operator can be shown that nobody ever read (ADR-0009 d.3)."""
    assert [shown["of"] for shown in live()["band"]] == ["link", "rails"]


@pytest.mark.node
def test_the_band_reads_the_link_and_the_rails() -> None:
    """Both of the band's readings, off a station that is saying them."""
    assert band(said=list(TALKING), now=NOW) == {
        "link": "answering",
        "rails": "hot",
    }


@pytest.mark.node
def test_the_rails_are_cold_when_the_station_says_the_power_is_off() -> None:
    assert band(said=[("<p0>", NOW - 10)], now=NOW)["rails"] == "cold"


@pytest.mark.node
def test_a_track_named_on_the_line_is_still_the_rails() -> None:
    """`<p1 MAIN>` is the station saying power is on for every MAIN track,
    which is what the band's rails reading is about."""
    assert band(said=[("<p1 MAIN>", NOW - 10)], now=NOW)["rails"] == "hot"


@pytest.mark.node
def test_one_track_going_off_is_its_tile_and_not_the_rails() -> None:
    """`<p0 C>` is track C's power. The band's rails reading is the station's
    word on power as a whole, and the track's own tile says C is off."""
    said = [("<p1>", NOW - 20), ("<p0 C>", NOW - 10)]
    assert band(said=said, now=NOW)["rails"] == "hot"
    assert tiles(said=said, now=NOW)["track C"] == "off"


@pytest.mark.node
def test_the_tiles_are_the_light_the_build_and_a_tile_per_track() -> None:
    """In order: the link light, the build, then each track the station uses
    by its letter. D is set to NONE, which is a track not in use."""
    assert [shown["of"] for shown in live()["tiles"]] == [
        "link",
        "build",
        "track A · MAIN",
        "track B · MAIN",
        "track C · MAIN",
    ]


@pytest.mark.node
def test_the_tiles_read_the_station_s_particulars() -> None:
    """A track that is on reads its current; one that is off reads `off`,
    not the current last measured on it."""
    assert tiles(said=list(TALKING), now=NOW) == {
        "link": "",
        "build": "9db6d10",
        "track A · MAIN": "120 mA",
        "track B · MAIN": "2 mA",
        "track C · MAIN": "off",
    }
    assert light(said=list(TALKING), now=NOW) is True


@pytest.mark.node
def test_a_track_whose_mode_is_not_known_yet_is_still_drawn() -> None:
    """A current arrives before the mode has: the track is drawn by its letter
    alone until the station says what it is set to."""
    assert tiles(said=[("<jI 40>", NOW)], now=NOW) == {
        "link": "",
        "build": "",
        "track A": "40 mA",
    }


@pytest.mark.node
def test_the_current_is_smoothed_across_polls() -> None:
    """Each reading moves the one shown half the way towards it, so a single
    spike is halved and a steady draw settles in a few polls."""
    said = [("<jI 100>", NOW - 20), ("<jI 300>", NOW - 10)]
    assert tiles(said=said, now=NOW)["track A"] == "200 mA"
    twice = [("<jI 100>", NOW - 9), ("<jI 100>", NOW - 8)]
    assert tiles(said=[*said, *twice], now=NOW)["track A"] == "125 mA"
    steady = [("<jI 100>", NOW - 8 + i) for i in range(8)]
    assert tiles(said=[*said, *steady], now=NOW)["track A"] == "100 mA"


@pytest.mark.node
def test_a_line_the_decoder_does_not_know_is_still_the_station_speaking() -> None:
    """This fork answers a subset of DCC-EX's vocabulary and upstream adds to
    it (ADR-0009 d.5). A line the page cannot gloss is a station that is
    plainly answering, and a **link** that went down under one would be the
    page calling a talking station dead."""
    assert band(said=[("<l 3 0 128 0>", NOW - 10)], now=NOW)["link"] == "answering"
    assert light(said=[("<l 3 0 128 0>", NOW - 10)], now=NOW) is True


@pytest.mark.node
def test_a_station_that_says_nothing_is_a_link_that_is_down() -> None:
    """Before anything has arrived, and with no socket anywhere in it: the
    **link** is the station answering rather than a socket being open
    (ADR-0008, control ADR-0066)."""
    assert band(now=NOW) == {"link": "not answering", "rails": "unknown"}
    assert tiles(now=NOW) == {"link": "", "build": ""}
    assert light(now=NOW) is False


@pytest.mark.node
def test_a_station_that_stops_answering_takes_the_band_and_the_tiles() -> None:
    """The station said all of it and then went quiet past the silence.

    The band says so rather than leaving the page looking merely idle, the
    light goes red, and the tiles that are the station talking go with it —
    which is the correct reading rather than a gap, because the station is not
    talking (ADR-0008 d.3).
    """
    gone: dict[str, Any] = {"said": list(TALKING), "now": NOW + silent_ms()}

    assert band(**gone) == {"link": "not answering", "rails": "unknown"}
    assert tiles(**gone) == {"link": "", "build": ""}
    assert light(**gone) is False


@pytest.mark.node
def test_the_link_holds_for_as_long_as_the_silence_is_allowed() -> None:
    """The boundary itself, both sides of it, so the rule is the number the
    module exports rather than whatever a scenario happened to use."""
    said = [("<p1>", NOW)]
    inside = band(said=said, now=NOW + silent_ms())
    outside = band(said=said, now=NOW + silent_ms() + 1)

    assert inside["link"] == "answering"
    assert outside["link"] == "not answering"


@pytest.mark.node
def test_the_build_blanks_with_the_link_and_fills_again_by_itself() -> None:
    """A stale pre-flash build is never reported as the one on the board, and
    nothing has to be reloaded to get the new one: the station's banner arrives
    on its own when it comes back up (ADR-0008 d.3, ADR-0010 d.4)."""
    flashing = [(BANNER, NOW)]
    back = [*flashing, (BANNER.replace("9db6d10", "0ff1ce5"), NOW + 90_000)]

    assert tiles(said=flashing, now=NOW + 60_000)["build"] == ""
    assert tiles(said=back, now=NOW + 90_010)["build"] == "0ff1ce5"


@pytest.mark.node
def test_what_the_station_last_said_is_what_the_readings_read() -> None:
    """Power off after power on is cold, and a track switched back on reads
    its current again: a reading is the station's latest word and not its
    first."""
    said = [
        ("<p1>", NOW - 40),
        ("<p0>", NOW - 30),
        ("<jI 50>", NOW - 25),
        ("<p0 A>", NOW - 20),
        ("<p1 A>", NOW - 10),
    ]

    assert band(said=said, now=NOW)["rails"] == "cold"
    assert tiles(said=said, now=NOW)["track A"] == "50 mA"


@pytest.mark.node
def test_a_reading_the_station_has_not_given_is_blank_and_not_a_zero() -> None:
    """A track the station has named but not measured has no current.
    Drawing `0 mA` there would be a reading nobody took (ADR-0009 d.2)."""
    assert tiles(said=[("<= A MAIN>", NOW)], now=NOW)["track A · MAIN"] == ""


def test_the_readings_hold_no_clock_and_no_socket() -> None:
    """A pure function of what was said and of the moment it is asked for.

    Held against the source because those are the reaches that would end it:
    a module that read the clock itself could not be asked what the page shows
    fifteen seconds from now, which is the whole of what is asserted above.
    """
    source = READINGS.read_text()
    assert 'from "./decoder.js"' in source, "the readings read a line themselves"
    for held in ("Date", "setTimeout", "setInterval", "window", "WebSocket"):
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
