"""What the **band** says, and what it asks for.

The words it shows for a set of facts are asserted by running the real
functions (`tests/ui/test_readings.py`), and that they reach look's elements,
and that each press asks for what it says, by drawing the band and pressing it
(`ui/test/band.test.ts`). The band itself is look's (ADR-0023). What is held
here is what neither of those can see: that the band works no reading out of
its own, that both presses go on the bus and nowhere else, that nothing asks
for a confirmation, and that the railroad is a reading.

Read off the sources, because a band that worked the reading out itself would
draw the same words until the two answers parted.
"""

from tests.ui.paths import UI
from tests.ui.test_stream import code

#: The band and the rail, as look's elements.
CHROME = UI / "src" / "ui" / "chrome.ts"

#: The page that draws them and listens for a press.
APP = UI / "src" / "ui" / "dccex-app.ts"


def test_the_band_works_no_reading_out_of_its_own() -> None:
    """The reading is the readings module's, a pure function of what the
    station said and what `layout` reported (ADR-0008 d.2, ADR-0017 d.2), and
    the page hands it the facts."""
    drawn = code(CHROME.read_text())
    assert 'from "../readings.js"' in drawn, "the band works a reading out itself"
    assert "band(readings, layout)" in drawn
    assert "drawBand(this.readings, this.layout)" in APP.read_text()


def test_the_presses_on_the_band_are_looks_power_and_ask_layout() -> None:
    """One `look-power` and nothing else to press (ADR-0017 d.1, ADR-0026 d.2,
    ADR-0011 d.3).

    look fires `off` or `on` from the toggle and `stopped` from the stop sign.
    The page maps that word through `asked` and puts the result on the bus, as
    `tc49/layout/power_wanted`, and types nothing at the station. A band
    that opened a connection of its own would be a second client of
    `control`'s broker for one page (`bus.ts`).
    """
    drawn = code(CHROME.read_text())
    assert drawn.count("<look-power") == 1
    for pressed in ("<button", "@click", "<form", "@submit", "<input"):
        assert pressed not in drawn, f"the band carries a {pressed}"
    for literal in ("<0>", "<1>", '"stopped"'):
        assert literal not in drawn, f"the band writes {literal} out itself"
    page = code(APP.read_text())
    assert "@look-power=" in page, "nothing listens for a press"
    assert "this.#wants(asked(e.detail.state))" in page, "a press is not mapped"
    assert "this.#bus.wants(power)" in page


def test_the_toggle_and_stop_are_held_on_one_rule() -> None:
    """Both presses are dead on one rule with one reason (ADR-0026 d.4), so
    the band holds both with look's `reason` and never the toggle alone."""
    drawn = code(CHROME.read_text())
    assert 'reason=${stop.wants === null ? stop.title : ""}' in drawn
    assert "toggle-reason=" not in drawn


def test_the_band_asks_for_no_confirmation() -> None:
    """The guard is `layout` and then the operator (ADR-0017, ADR-0006 d.2).

    The flash, which is not undone by pressing again, is the one thing here
    that warns anybody.
    """
    drawn = code(CHROME.read_text())
    for asked in ("confirm", "look-dialog", "WARNS"):
        assert asked not in drawn, f"the band asks {asked}"


def test_the_band_names_the_railroad_and_presses_nothing_with_it() -> None:
    """Which railroad `control` has loaded, as a `look-reading` (the
    organisation's ADR-0014, #239).

    A reading and not a control: nothing on this page loads one. The words for
    a box that has loaded none are the readings module's.
    """
    drawn = code(CHROME.read_text())
    assert drawn.count("<look-reading") == 1
    assert ">${railroad}${unbuilt" in drawn
    assert '<span class="unbuilt">${unbuilt}</span>' in drawn
    for written in ("no railroad loaded", "not built"):
        assert written not in drawn, f"the band writes out {written} itself"
