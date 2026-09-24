"""What the **tile**s draw, and what they blank.

Which words appear for a set of facts is asserted by running the real
functions (`tests/ui/test_readings.py`): hand them what a page would hand them
and read the four tiles back, blanks and all. What is held here is the rest —
that the component draws those readings and works none out, where the tiles
sit, and that a blank tile keeps its shape.

Read off the sources, for the reason `tests/ui/test_stream.py` gives: there is
no browser in a Python gate to mount a Lit component in.
"""

import re

from tests.ui.test_look import HEX, UI
from tests.ui.test_monitor import rule

#: The station's particulars.
TILES = UI / "src" / "ui" / "dccex-tiles.ts"

#: What they are drawn with.
STYLES = UI / "src" / "ui" / "dccex-tiles.styles.ts"

#: The page that hands them the readings.
APP = UI / "src" / "ui" / "dccex-app.ts"


def test_the_tiles_draw_the_readings_the_page_hands_them() -> None:
    """The reading is the readings module's — a pure function of what the
    station said and of the moment it is asked for (ADR-0008 d.2) — and the
    drawing is this component's."""
    drawn = TILES.read_text()
    assert 'from "../readings.js"' in drawn, "the tiles work a reading out themselves"
    assert "tiles(this.readings)" in drawn
    assert "<dccex-tiles .readings=${this.readings}>" in APP.read_text()


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


def test_a_blank_tile_keeps_its_shape() -> None:
    """Three of the four blank together when the link goes down (ADR-0008
    d.3), and a row that collapsed as it happened would move the monitor under
    the reader's thumb at the moment the station went away."""
    reads = rule(STYLES.read_text(), ".reads")
    assert "min-height:" in reads, "a tile with nothing in it collapses"


def test_the_tiles_press_nothing() -> None:
    """They are readings. Nothing on this page commands track power and
    nothing on it writes the station outside the flash sequence, which is its
    own ticket's (ADR-0008 d.5)."""
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
