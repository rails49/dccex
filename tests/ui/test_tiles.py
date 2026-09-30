"""What the **tile**s draw, and what they blank.

Which words a set of facts produces is asserted by running the real functions
(`tests/ui/test_readings.py`), and that they go together on a page is asserted
by mounting the component and reading the row back (`ui/test/tiles.test.ts`,
#126). What is held here is the rest — that the tiles work no reading out of
their own, where they sit, that a row with nothing in it keeps its shape, and
that they wrap rather than running off the side of a phone.

Read off the sources, because these are claims a mounted component cannot
answer: happy-dom does no layout, so a `min-height` and a `flex-wrap` are not
things to assert there, and a component that worked the reading out again would
draw the same words.
"""

import re

from tests.ui.test_look import HEX, UI
from tests.ui.test_monitor import rule
from tests.ui.test_stream import code

#: One track's readings, one tile each.
TILES = UI / "src" / "ui" / "dccex-tiles.ts"

#: What they are drawn with.
STYLES = UI / "src" / "ui" / "dccex-tiles.styles.ts"

#: The page that hands them the readings.
APP = UI / "src" / "ui" / "dccex-app.ts"


def test_the_reading_is_the_module_s_and_the_page_hands_it_down() -> None:
    """The reading is the readings module's — a pure function of what the
    station said and of the moment it is asked for (ADR-0008 d.2) — and the
    drawing is this component's.

    What the tiles read is asserted by mounting them; where the facts came
    from is not visible there, because tiles that worked them out again would
    draw the same words until the two answers parted.
    """
    drawn = TILES.read_text()
    assert 'from "../readings.js"' in drawn, "the tiles work a reading out themselves"
    assert "<dccex-tiles .readings=${this.readings}>" in APP.read_text()


def test_a_tile_is_one_track_and_the_link_and_the_build_are_the_band_s() -> None:
    """One per track in use and nothing else on the row (CONTEXT.md **tile**,
    issue 170).

    The **link** and the **build** are the **band**'s, which carries both at
    every width either is drawn at (issue 168). A tile that repeated one of
    them would be a second answer to a reading the chrome already gives, in the
    pane the chrome sits over.
    """
    drawn = code(TILES.read_text())
    assert "tiles(this.readings)" in drawn, "the tiles are not one per track"
    for carried in (".build", ".answering", "link"):
        assert carried not in drawn, f"a tile draws the band's {carried}"


def test_the_tiles_are_at_the_top_of_the_work_pane_above_the_monitor() -> None:
    """Everything the page is about goes in the work pane, and the particulars
    go above the conversation they are made of (ADR-0008, docs/ui/README.md)."""
    app = APP.read_text()
    assert 'import "./dccex-tiles.js";' in app
    assert app.index("<dccex-tiles") < app.index(
        "<dccex-monitor"
    ), "the tiles are drawn below the monitor"
    assert 'customElements.define("dccex-tiles"' in TILES.read_text()


def test_the_tiles_work_no_reading_out_of_their_own() -> None:
    """No clock, no socket and no protocol in a component that has a DOM in
    reach: what a tile shows is a pure function of what the page knows, which
    is what lets every one of them be asserted as a pair (ADR-0009 d.1)."""
    drawn = TILES.read_text()
    for held in ("Date", "setInterval", "fetch(", "WebSocket", "decoder.js"):
        assert held not in drawn, f"the tiles reach {held}"


def test_an_empty_row_and_a_blank_reading_keep_their_shape() -> None:
    """The tiles go together when the link goes down (ADR-0008 d.3), and a row
    that collapsed as it happened would move the monitor under the reader's
    thumb at the moment the station went away.

    Each reading's line the same way: a current the station has not measured is
    blank, and a tile that shrank while it waited would move the two readings
    under it.
    """
    assert "min-height:" in rule(STYLES.read_text(), ":host"), "the empty row goes"
    for reading in (".mode", ".most"):
        assert "min-height:" in rule(
            STYLES.read_text(), reading
        ), f"a tile with no {reading} collapses"


def test_the_tiles_wrap_onto_more_rows_rather_than_running_off_the_side() -> None:
    """Four tiles at a phone's width do not fit on one row (issue 170).

    They wrap, and each may shrink below the share it asks for, which is what
    keeps the row inside the screen. A browser is what says it worked, and it
    does not say it yet: there is no station behind the page in that job, so
    there are no tiles to measure (docs/ui/README.md).
    """
    styles = STYLES.read_text()
    assert "flex-wrap: wrap;" in rule(styles, ":host"), "the row runs off the side"
    assert "min-width: 0;" in rule(styles, ".tile"), "a tile cannot shrink"


def test_the_tiles_press_nothing() -> None:
    """They are readings. Nothing on this page commands track power but the
    band's one button and the flash sequence's own step (ADR-0011 d.3)."""
    drawn = TILES.read_text()
    for pressed in ("<button", "@click", "<form", "@submit", "<input"):
        assert pressed not in drawn, f"a tile carries a {pressed}"


def test_the_tiles_are_the_work_pane_s_and_not_the_chrome_s() -> None:
    """The chrome's four values say *this is the same project* across rails49's
    UIs and stay on the chrome; a pane follows the system's theme, which is
    Shoelace's tokens (LOOK.md)."""
    styles = STYLES.read_text()
    assert not HEX.findall(styles), "the tiles write a colour out"
    asked = set(re.findall(r"var\((--[a-z0-9-]+)\)", styles))
    borrowed = {token for token in asked if not token.startswith("--sl-")}
    assert borrowed == set(), f"the tiles take the chrome's {borrowed}"
