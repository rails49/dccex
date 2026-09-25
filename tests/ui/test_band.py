"""What the **band** draws, and what it refuses to.

The words it shows for a set of facts are asserted by running the real
functions (`tests/ui/test_readings.py`): hand them what a page would hand them
and read the band back. What is held here is the rest of it — that the
component draws those readings and nothing of its own, that it presses
nothing, that red reaches the chrome only for a fault, and which reading
survives a band too narrow to carry both.

Read off the sources, for the reason `tests/ui/test_stream.py` gives: the gate
is Python, the node beside it is a bare one with no packages, and nothing in
either can mount a Lit component and read the DOM back.
"""

import re

from tests.ui.test_look import HEX, UI
from tests.ui.test_monitor import rule

#: The chrome across the top.
BAND = UI / "src" / "ui" / "dccex-band.ts"

#: What it is drawn with.
STYLES = UI / "src" / "ui" / "dccex-band.styles.ts"

#: The page that hands it the readings.
APP = UI / "src" / "ui" / "dccex-app.ts"


def test_the_band_draws_the_readings_the_page_hands_it() -> None:
    """The reading is the readings module's — a pure function of what the
    station said (ADR-0008 d.2) — and the drawing is this component's, which
    is the same division the monitor has with the decoder."""
    drawn = BAND.read_text()
    assert 'from "../readings.js"' in drawn, "the band works a reading out itself"
    assert "band(this.readings)" in drawn
    assert ".readings=${this.readings}" in APP.read_text(), "nothing hands it the facts"


def test_a_band_nobody_handed_readings_to_reads_a_station_that_said_nothing() -> None:
    """Not a blank band and not a hedge: before anything has arrived the link
    is down and the rails are unknown, which is what is true."""
    assert "readings: Readings = asOf(QUIET, 0);" in BAND.read_text()


def test_the_band_presses_nothing() -> None:
    """`control`'s band commands track power because `layout` checks the
    railroad is drained first, and this page is on no bus for anything to
    check (ADR-0008 d.5).

    No button, nothing listening for a press, and no form: the band is two
    readings, and the one place a command is typed at the station is the box
    at the foot of the monitor.
    """
    drawn = BAND.read_text()
    for pressed in ("<button", "@click", "<form", "@submit", "<input"):
        assert pressed not in drawn, f"the band carries a {pressed}"


def test_red_on_the_chrome_is_the_fault_and_nothing_else() -> None:
    """The look rules keep red on the chrome for stop or a fault (#138). This
    page draws no emergency stop, so the one red it draws is the fault: a link
    that is down.

    What the sheet may ask for is the chrome's own values and sizes. A colour
    of its own — a hex, or one of Shoelace's theme colours borrowed onto the
    chrome — would put a red there that means something else, and neither is
    here. The stop tokens are asked for by the fault's rule and by no other.
    """
    styles = STYLES.read_text()
    assert not HEX.findall(styles), "the band writes a colour out"
    asked = set(re.findall(r"var\((--[a-z0-9-]+)\)", styles))
    assert asked == {
        "--band",
        "--band-ink",
        "--rail-button",
        "--stop",
        "--stop-ink",
    }, f"the band asks {asked}"
    fault = rule(styles, ".fault")
    assert "background: var(--stop)" in fault
    assert "color: var(--stop-ink)" in fault
    without = styles.replace(fault, "")
    assert "--stop" not in re.sub(
        r"/\*.*?\*/", "", without, flags=re.DOTALL
    ), "a rule other than the fault's asks for red"


def test_the_band_marks_the_reading_that_is_a_fault() -> None:
    """Whether a reading is a fault is the readings module's to say
    (`tests/ui/test_readings.py`); the band draws the class it asks for."""
    assert '${shown.fault ? "fault" : ""}' in BAND.read_text()


def test_a_link_that_is_down_says_so_in_words() -> None:
    """A distinction carried by colour alone is no distinction to a reader who
    does not see it. The fault's red is drawn as well as the words, not
    instead of them, and the words are also what lets it be asserted as a pair
    (`tests/ui/test_readings.py`)."""
    drawn = BAND.read_text()
    assert "${shown.reads}" in drawn, "the band draws no words for a reading"
    assert "${shown.of}" in drawn, "a reading is drawn without saying which it is"


def test_the_narrow_band_keeps_the_link_and_drops_the_rails() -> None:
    """Below the width at which the band cannot carry both readings, the one
    that survives is whether the station is answering.

    A station that is not answering makes the other reading meaningless, and a
    band that kept the rails instead would show a power state nothing has
    confirmed since the link went.
    """
    styles = STYLES.read_text()
    narrow = re.search(
        r"@media \(max-width: (\d+)px\) \{(.*?)\n  \}", styles, re.DOTALL
    )
    assert narrow is not None, "the band carries both readings at every width"
    dropped = narrow.group(2)
    assert ".rails {" in dropped and "display: none" in dropped
    assert ".link" not in dropped, "the narrow band drops the link"


def test_the_readings_sit_at_the_end_the_eye_finishes_on() -> None:
    """The name of the UI on the left and what is true of the whole system on
    the right, which is where every rails49 band carries it."""
    styles = STYLES.read_text()
    assert "justify-content: space-between" in rule(styles, ":host")
    assert "white-space: nowrap" in rule(
        styles, ".reading"
    ), "a reading wraps and pushes the work pane down"
