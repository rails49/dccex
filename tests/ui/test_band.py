"""What the **band** draws, and what it refuses to.

The words it shows for a set of facts are asserted by running the real
functions (`tests/ui/test_readings.py`), and that they reach a page — the one
control on it included — is asserted by mounting the component and pressing it
(`ui/test/band.test.ts`, #126). What is held here is what neither of those can
see: that the band works no reading out of its own, that the one press on it is
the power button's, which colours reach the chrome and what they mean, and what
survives a band too narrow to carry all three of the things on it.

Read off the sources, because these are claims about the shape of the page
rather than about what it says. happy-dom does no layout, so a width is not a
thing a mounted check can assert; and a component that worked the reading out
itself would draw exactly the same words, so the one place that shows is the
source.

What the last of them is about *is* a width, and a browser draws it:
`tests/ui/test_page_at_a_phones_width.py` loads the built page at 375px and
reads back a dot and a power button with a size, a build and the link's words
with none (#127, issue 168). It stays here as well, and the two are not the
same claim — this one says which of them the rules name and which they leave
alone, which a measurement of a band that drew one of them cannot say.
"""

import re

from tests.ui.test_look import HEX, UI
from tests.ui.test_monitor import rule
from tests.ui.test_stream import code

#: The chrome across the top.
BAND = UI / "src" / "ui" / "dccex-band.ts"

#: What it is drawn with.
STYLES = UI / "src" / "ui" / "dccex-band.styles.ts"

#: The page that hands it the readings.
APP = UI / "src" / "ui" / "dccex-app.ts"


def test_the_band_works_no_reading_out_of_its_own() -> None:
    """The reading is the readings module's — a pure function of what the
    station said (ADR-0008 d.2) — and the drawing is this component's, which
    is the same division the monitor has with the decoder.

    A band that worked it out again would draw the same words until the two
    answers parted, so the rendered check cannot see this one and the source
    can: the reading comes from the module, and the page is what hands the
    facts down.
    """
    drawn = BAND.read_text()
    assert 'from "../readings.js"' in drawn, "the band works a reading out itself"
    assert ".readings=${this.readings}" in APP.read_text(), "nothing hands it the facts"


def test_the_one_press_on_the_band_is_the_power_button() -> None:
    """The band presses power and nothing else (ADR-0011 d.1, d.3).

    `control`'s band presses it because `layout` checks the railroad is drained
    first, and that check never guarded the station: any client of the mirror's
    port sends `<0>` or `<1>` and the guard is the operator (ADR-0011,
    ADR-0006). So there is one button, one thing listening for a press, and
    what it sends is the readings module's rather than a literal here — the
    colour and the message are one answer and a band that chose the message
    itself could disagree with the colour it drew.

    No form and no field: the one place a command is *typed* at the station is
    the box at the foot of the monitor.

    With the prose off, as `tests/ui/test_page.py` holds the same claim about
    every module: a sentence saying what the band sends is not the band sending
    it (`code`, `tests/ui/test_stream.py`).
    """
    drawn = code(BAND.read_text())
    assert drawn.count("<button") == 1, "the band carries a second control"
    assert drawn.count("@click") == 1, "the band listens for a second press"
    assert "power.sends" in drawn, "the band does not send what the readings say"
    for literal in ("<0>", "<1>"):
        assert literal not in drawn, f"the band writes {literal} out itself"
    for pressed in ("<form", "@submit", "<input"):
        assert pressed not in drawn, f"the band carries a {pressed}"


def test_the_press_goes_up_the_stream_the_way_anything_typed_does() -> None:
    """A press is a line on the stream like any other client's (ADR-0011).

    The page hands the band the same `#sends` it hands the monitor and the
    releases, so `<0>` goes up the way a typed command does and is written to
    the monitor as this page's — and the station's `<p…>` answer is what turns
    the button's colour. A band that opened a stream of its own would be a
    second client of the mirror's port for one page.
    """
    assert (
        "<dccex-band .readings=${this.readings} .sends=${this.#sends}>"
        in APP.read_text()
    ), "nothing hands the band its sending"
    assert "new Stream(" not in BAND.read_text(), "the band opens a stream of its own"


def test_the_power_button_is_disabled_while_the_link_is_down() -> None:
    """Power is then unknown and a press would reach a station that is not
    answering (ADR-0011 d.2).

    The attribute is what stops a pointer and a keyboard; that nothing is sent
    even where a press gets through is the component's own guard, and both are
    pressed in `ui/test/band.test.ts`.
    """
    drawn = BAND.read_text()
    assert "?disabled=${power.sends === null}" in drawn, "the band presses a dead link"


def test_the_band_asks_for_no_confirmation() -> None:
    """The guard is the operator, as for a flash (ADR-0011 d.4, ADR-0006 d.2).

    A page that asked *are you sure* about `<0>` would be asking about the one
    gesture on it that is undone by pressing it again, and the flash — which is
    not — is the one thing here that warns anybody.
    """
    drawn = code(BAND.read_text())
    for asked in ("confirm", "window.confirm", "WARNS"):
        assert asked not in drawn, f"the band asks {asked}"


def test_the_band_paints_with_the_look_rules_values_and_no_others() -> None:
    """What the sheet may ask for is the chrome's own values and sizes.

    A colour of its own — a hex, or one of Shoelace's theme colours borrowed
    onto the chrome — would put a colour there that means something else, and
    one of Shoelace's would follow the system's light or dark setting while the
    chrome around it did not (LOOK.md, `theme.ts`). Neither is here.

    `--rail-group` is the sixth: the look rules give this chrome one green and
    that is it, so the dot and a power button with the rails hot take it
    (issue 168).
    """
    styles = STYLES.read_text()
    assert not HEX.findall(styles), "the band writes a colour out"
    asked = set(re.findall(r"var\((--[a-z0-9-]+)\)", styles))
    assert asked == {
        "--band",
        "--band-ink",
        "--rail-button",
        "--rail-group",
        "--stop",
        "--stop-ink",
    }, f"the band asks {asked}"


def test_red_on_the_chrome_is_the_fault_and_the_stop_and_nothing_else() -> None:
    """The look rules keep red on the chrome for stop or a fault.

    This band draws both: a link that is down is the fault, in words on
    `--stop` with a dot in `--stop-ink` (#138), and rails with no power is the
    stop, which is what the power button says while every track is off
    (ADR-0011 d.1). Nothing else on it is red — a band that drew the rails hot
    in it would be saying stop about a railroad that is running.
    """
    styles = STYLES.read_text()
    assert "background: var(--stop)" in rule(styles, ".says")
    assert "color: var(--stop-ink)" in rule(styles, ".says")
    left = re.sub(r"/\*.*?\*/", "", styles, flags=re.DOTALL)
    for selector in (".says", ".dot.off", ".power.off"):
        drawn = rule(styles, selector)
        assert "var(--stop" in drawn, f"{selector} is not drawn in red"
        left = left.replace(drawn, "")
    assert "--stop" not in left, "a rule that is neither the fault nor the stop is red"


def test_green_on_the_chrome_is_the_station_answering_and_the_rails_hot() -> None:
    """The one green the look rules give this chrome, and the two readings that
    are worth it: a station that is answering, and a track with power on it
    (ADR-0011 d.1)."""
    styles = STYLES.read_text()
    left = re.sub(r"/\*.*?\*/", "", styles, flags=re.DOTALL)
    for selector in (".dot.on", ".power.on"):
        drawn = rule(styles, selector)
        assert "var(--rail-group)" in drawn, f"{selector} is not drawn in green"
        left = left.replace(drawn, "")
    assert "--rail-group" not in left, "a rule that is neither reading is green"


def test_the_power_button_is_grey_and_not_red_while_the_link_is_down() -> None:
    """Power is then unknown, and a red button would be this page saying every
    track is off — which nothing has confirmed since the link went (ADR-0011
    d.2, ADR-0009 d.2).

    Grey is the band's own ink at half strength: none of the six colours is a
    dimmer ink, and a seventh would be a colour of this page's own. The chip it
    wears while it can be pressed goes with the colour, so a reader who cannot
    tell the green from the red is still left a difference.
    """
    dead = rule(STYLES.read_text(), ".power:disabled")
    assert "color: var(--band-ink)" in dead
    assert "background: none" in dead, "the button keeps its chip while it is dead"
    assert "opacity" in dead, "the button is drawn as brightly as a live one"
    assert "--stop" not in dead and "--rail-group" not in dead


def test_neither_colour_is_laid_straight_on_the_bands_blue() -> None:
    """`--rail-group` on `--band` is 1.8 to 1 and `--stop-ink` on it is 1.3,
    where a control a person has to read needs 3.

    So the dot is ringed in the band's ink, the words sit on `--stop`, and the
    power button is a chip of the band's ink with the colour on it. What is held
    is the ring and the chip; what the numbers are is `look.css`'s and this is
    the reason they are not drawn against.
    """
    styles = STYLES.read_text()
    assert "border: 2px solid var(--band-ink)" in rule(styles, ".dot")
    assert "background: var(--band-ink)" in rule(styles, ".power")
    assert "background: var(--stop)" in rule(styles, ".says")


def test_the_power_button_is_a_thumb_wide_and_a_thumb_high() -> None:
    """It is pressed on the phone held at the layout, and `--rail-button` is
    the look rules' minimum for a thumb (`ui/look/README.md`)."""
    power = rule(STYLES.read_text(), ".power")
    assert "min-width: var(--rail-button)" in power
    assert "min-height: var(--rail-button)" in power


def test_the_narrow_band_drops_the_build_then_the_words_and_keeps_the_rest() -> None:
    """Three things on the band and two widths that take one away each.

    The **build** goes first: it is the longest thing on the band and the one a
    reader at the layout is least often after — what the station is doing is on
    the tiles and what it is running is not (issue 170). Then the
    link's words go and the link is the dot alone — the dot is the reading and
    the words are that reading a second time. The dot and the power button
    survive every width: the button is the one control on the page that
    commands power and a thumb has to reach it (ADR-0011 d.1).

    The rules as they are written: which part each query names, in the order
    the widths come. That a browser does it is
    `tests/ui/test_page_at_a_phones_width.py`'s (#127).
    """
    styles = STYLES.read_text()
    narrow = re.findall(
        r"@media \(max-width: (\d+)px\) \{(.*?)\n  \}", styles, re.DOTALL
    )
    assert len(narrow) == 2, "the band does not give up the build and then the words"
    (wider, drops_build), (narrower, drops_words) = narrow
    assert int(narrower) < int(wider), "the words go before the build does"
    assert ".build {" in drops_build and "display: none" in drops_build
    assert ".says {" in drops_words and "display: none" in drops_words
    for kept in (".dot", ".power", ".link {"):
        assert kept not in drops_build + drops_words, f"a narrow band drops {kept}"


def test_the_build_is_on_the_left_and_the_rest_at_the_end_the_eye_finishes_on() -> None:
    """The name of the UI and the **build** on the left, and what is true of
    the whole system on the right, which is where every rails49 band carries
    it (CONTEXT.md **band**)."""
    styles = STYLES.read_text()
    assert "justify-content: space-between" in rule(styles, ":host")
    assert "white-space: nowrap" in rule(
        styles, ".readings"
    ), "a reading wraps and pushes the work pane down"
    assert "white-space: nowrap" in rule(
        styles, ".build"
    ), "the build wraps and pushes the work pane down"
