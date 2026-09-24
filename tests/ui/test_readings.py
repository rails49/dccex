"""What the **band** and the **tile**s read, given the facts a page hands them.

Scenarios: the station said these lines at these moments, the face last
answered with this many **client**s, and it is now — so the band reads this and
the tiles read that. Every reading on the page is made of what the station
said, decoded on the page (ADR-0008 d.2), so a scenario is a conversation and
nothing else, and the readings are a pure function of it.

**They are run rather than read**, as the decoder's pairs and the box's are
(`tests/ui/test_decoder.py`, `tests/ui/test_message.py`), and for the reason
this issue's criterion names: what a page shows an operator is worth nothing
asserted against the source that would produce it. The scenarios go through the
real functions under `node`, by way of `tests/ui/readings.mjs`.

What cannot be run here is Lit. The gate is Python with a bare node in it and
no packages, so nothing in it can mount a component and read the DOM back:
`control`'s band test renders, and this renders the readings the band draws and
holds the drawing itself against the component's source
(`tests/ui/test_band.py`, `tests/ui/test_tiles.py`). The words an operator sees
are asserted here; that those words reach the screen is the part a Python gate
cannot reach, which is the cost `tests/ui/test_look.py` already names.
"""

import json
import re
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any

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
    node = shutil.which("node")
    assert node is not None, "no node on this machine to run the readings with"
    ran = subprocess.run(
        [node, str(RUNNER)],
        input=json.dumps(list(scenarios)),
        capture_output=True,
        text=True,
        check=False,
    )
    assert ran.returncode == 0, f"the readings did not run: {ran.stderr.strip()}"
    drawn: list[dict[str, Any]] = json.loads(ran.stdout)
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
CURRENT = "<c CurrentMAIN 123 C Milli 0 0 4000 1000>"

#: A station that has just said everything it has to say about itself.
TALKING: tuple[tuple[str, int], ...] = (
    (BANNER, NOW - 30),
    ("<p1>", NOW - 20),
    (CURRENT, NOW - 10),
)


@lru_cache(maxsize=1)
def live() -> dict[str, Any]:
    """The page a moment after the station answered a poll."""
    return drawn(said=list(TALKING), clients=2, now=NOW)


def test_the_band_carries_two_readings_and_the_tiles_four() -> None:
    """The band is the link and whether the rails are hot, and nothing else
    (CONTEXT.md, **band**); the tiles are the station's four particulars.

    A reading added to either without a scenario beside it is a reading an
    operator can be shown that nobody ever read (ADR-0009 d.3).
    """
    assert [shown["of"] for shown in live()["band"]] == ["link", "rails"]
    assert [shown["of"] for shown in live()["tiles"]] == [
        "build",
        "current",
        "clients",
        "last heard",
    ]


def test_the_band_reads_the_link_and_the_rails() -> None:
    """Both of the band's readings, off a station that is saying them."""
    assert band(said=list(TALKING), now=NOW) == {
        "link": "answering",
        "rails": "hot",
    }


def test_the_rails_are_cold_when_the_station_says_the_power_is_off() -> None:
    assert band(said=[("<p0>", NOW - 10)], now=NOW)["rails"] == "cold"


def test_a_track_named_on_the_line_is_still_the_rails() -> None:
    """`<p1 MAIN>` is the station saying power is on. This page has no track
    row to hang a name on — it is about a command station and not a railroad
    (ADR-0008) — so what it reads is that the rails are hot."""
    assert band(said=[("<p1 MAIN>", NOW - 10)], now=NOW)["rails"] == "hot"


def test_the_tiles_read_the_station_s_particulars() -> None:
    """The four of them, off a station that has said its piece and a face that
    has answered how many clients are on the port (ADR-0008 d.2, d.4)."""
    assert tiles(said=list(TALKING), clients=2, now=NOW) == {
        "build": "9db6d10",
        "current": "123 mA",
        "clients": "2",
        "last heard": "just now",
    }


def test_the_last_heard_tile_counts_from_the_last_thing_said() -> None:
    """Anything the station said, not only a line the decoder knows: what the
    tile reads is whether the conversation is alive."""
    said = [(BANNER, NOW - 9000), ("<l 3 0 128 0>", NOW - 4000)]
    assert tiles(said=said, now=NOW)["last heard"] == "4s ago"


def test_a_line_the_decoder_does_not_know_is_still_the_station_speaking() -> None:
    """This fork answers a subset of DCC-EX's vocabulary and upstream adds to
    it (ADR-0009 d.5). A line the page cannot gloss is a station that is
    plainly answering, and a **link** that went down under one would be the
    page calling a talking station dead."""
    assert band(said=[("<l 3 0 128 0>", NOW - 10)], now=NOW)["link"] == "answering"


def test_a_station_that_says_nothing_is_a_link_that_is_down() -> None:
    """Before anything has arrived, and with no socket anywhere in it: the
    **link** is the station answering rather than a socket being open
    (ADR-0008, control ADR-0066)."""
    assert band(now=NOW) == {"link": "not answering", "rails": "unknown"}
    assert tiles(now=NOW) == {
        "build": "",
        "current": "",
        "clients": "",
        "last heard": "",
    }


def test_a_station_that_stops_answering_takes_the_band_and_three_tiles() -> None:
    """The station said all of it and then went quiet past the silence.

    The band says so rather than leaving the page looking merely idle, and the
    three tiles that are the station talking blank together — which is the
    correct reading rather than a gap, because the station is not talking
    (ADR-0008 d.3).
    """
    gone: dict[str, Any] = {
        "said": list(TALKING),
        "clients": 2,
        "now": NOW + silent_ms(),
    }

    assert band(**gone) == {"link": "not answering", "rails": "unknown"}
    assert tiles(**gone) == {
        "build": "",
        "current": "",
        "clients": "2",
        "last heard": "",
    }


def test_the_link_holds_for_as_long_as_the_silence_is_allowed() -> None:
    """The boundary itself, both sides of it, so the rule is the number the
    module exports rather than whatever a scenario happened to use."""
    said = [("<p1>", NOW)]
    inside = band(said=said, now=NOW + silent_ms())
    outside = band(said=said, now=NOW + silent_ms() + 1)

    assert inside["link"] == "answering"
    assert outside["link"] == "not answering"


def test_the_build_blanks_with_the_link_and_fills_again_by_itself() -> None:
    """A stale pre-flash build is never reported as the one on the board, and
    nothing has to be reloaded to get the new one: the station's banner arrives
    on its own when it comes back up (ADR-0008 d.3, ADR-0010 d.4)."""
    flashing = [(BANNER, NOW)]
    back = [*flashing, (BANNER.replace("9db6d10", "0ff1ce5"), NOW + 90_000)]

    assert tiles(said=flashing, now=NOW + 60_000)["build"] == ""
    assert tiles(said=back, now=NOW + 90_010)["build"] == "0ff1ce5"


def test_the_clients_tile_is_the_face_s_and_does_not_blank_with_the_link() -> None:
    """The one reading that is not the station talking (ADR-0008 d.4). A
    station that has gone quiet says nothing about who is on the mirror's
    port, and the mirror is still answering for itself."""
    assert tiles(clients=3, now=NOW)["clients"] == "3"


def test_nobody_on_the_port_is_a_reading_and_not_a_blank() -> None:
    """Zero is what the face said; blank is the face not having answered. A
    page that drew them the same would hide an app that had stopped talking."""
    assert tiles(clients=0, now=NOW)["clients"] == "0"
    assert tiles(now=NOW)["clients"] == ""


def test_a_face_that_did_not_answer_blanks_the_tile_rather_than_reading_zero() -> None:
    """A face that is away, or that answered with something that is not a
    count, says nothing: drawing `0` for an app the page could not ask would
    be reporting an empty port nobody saw (ADR-0009 d.2, `face.ts`)."""
    assert tiles(clients=None, now=NOW)["clients"] == ""


def test_what_the_station_last_said_is_what_the_readings_read() -> None:
    """Power off after power on is cold, and the second current is the one
    drawn: a reading is the station's latest word and not its first."""
    said = [
        ("<p1>", NOW - 40),
        (CURRENT, NOW - 30),
        ("<p0>", NOW - 20),
        ("<c CurrentMAIN 0 C Milli 0 0 4000 1000>", NOW - 10),
    ]

    assert band(said=said, now=NOW)["rails"] == "cold"
    assert tiles(said=said, now=NOW)["current"] == "0 mA"


def test_a_reading_the_station_has_not_given_is_blank_and_not_a_zero() -> None:
    """A station that came up and said nothing else has a build and no
    current. Drawing `0 mA` there would be a reading nobody took (ADR-0009
    d.2)."""
    drawn_now = tiles(said=[(BANNER, NOW)], now=NOW)

    assert drawn_now["build"] == "9db6d10"
    assert drawn_now["current"] == ""


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


def test_the_same_facts_read_the_same_whatever_was_asked_before() -> None:
    """Given the same conversation they draw the same page for ever, so what
    the band says cannot depend on what some other page asked a moment ago."""
    scenarios: tuple[dict[str, Any], ...] = (
        {"said": list(TALKING), "clients": 2, "now": NOW},
        {"now": NOW},
        {"said": [("<p0>", NOW)], "now": NOW},
    )
    assert run(scenarios) == tuple(reversed(run(tuple(reversed(scenarios)))))
