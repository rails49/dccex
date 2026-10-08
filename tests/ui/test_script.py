"""What the page edits a railroad's **script** in, held against the sources.

The rules the view is made of — the text a railroad with no script opens with,
whether the editor holds unapplied edits, what a Tab puts in it — are run
through the real functions, and the gesture is made on a mounted pane, and both
are in the UI's own toolchain (`ui/test/script.test.ts`, #126). They run in the
workflow's `node` job and not in the gate (`scripts/check.sh`).

**So what is here is what that toolchain cannot say and the gate must.** The
sample the page offers is the translator's own text, copied because the mirror
imports nothing but the standard library and itself and so cannot serve it
(`tests/test_nothing_reaches_in.py`): a copy nothing holds to its original is
a second recommendation about what a railroad's districts may draw, and this
is what holds it. The rest is the shape of the view: that the pane holds no
counterparty, that the page asks the **face** and hands the answers down, that
the addresses are built from the one prefix, and that the pane is hidden rather
than taken away — because unapplied edits are held in it and nowhere else
(ADR-0015 d.5).

Read off the sources, for the reason `tests/ui/test_page.py` gives: there is no
browser in a Python gate to hold an editor, a listener or an address bar.
"""

import re

from dccex.sample import TEXT
from tests.ui.test_look import HEX, UI
from tests.ui.test_monitor import rule
from tests.ui.test_stream import code

#: The rules the view is made of, and the page's copy of the sample.
SCRIPT = UI / "src" / "script.ts"

#: The pane the script view is.
PANE = UI / "src" / "ui" / "dccex-script.ts"

#: What it is drawn with.
STYLES = UI / "src" / "ui" / "dccex-script.styles.ts"

#: The page that hands it the railroads and the two hands.
APP = UI / "src" / "ui" / "dccex-app.ts"

#: Where the page asks the mirror about the mirror.
FACE = UI / "src" / "face.ts"

#: The views, and the hash the current one is kept in.
VIEW = UI / "src" / "view.ts"

#: The rail that offers one button per view.
RAIL = UI / "src" / "ui" / "dccex-rail.ts"


def sample() -> str:
    """The sample as `script.ts` carries it.

    The one difference from the translator's text is the back quotes in its
    prose: a template literal cannot carry one unescaped, so the copy escapes
    the four that are in it and this reads them back. Everything else is the
    text character for character, which is the whole claim below.
    """
    written = SCRIPT.read_text()
    opened = written.index("export const SAMPLE = `") + len("export const SAMPLE = `")
    closed = written.index("`;", opened)
    return written[opened:closed].replace("\\`", "`")


def test_the_samples_the_page_offers_is_the_translators_own() -> None:
    """Character for character (#185, ADR-0015 d.5).

    The values in it are this installation's — what a district can take is
    what is wired to it — so a copy that drifted would be the page
    recommending current limits for a railroad nobody measured
    (`dccex/sample.py`). The mirror cannot serve the text, because it imports
    nothing but the standard library and itself, so the copy is the page's and
    this is what keeps it one text.
    """
    assert sample() == TEXT


def test_a_railroad_with_no_script_opens_on_the_sample_commented_out() -> None:
    """Commented, so that applying it unchanged is a railroad whose script
    does nothing rather than one running values a page suggested (ADR-0013
    d.2). What `commented` does to a line is run rather than read
    (`ui/test/script.test.ts`)."""
    rules = code(SCRIPT.read_text())
    opening = rules[rules.index("export function opened(") :]
    opening = opening[: opening.index("\n}")]
    assert "commented(SAMPLE)" in opening, "a railroad with none opens on nothing"
    assert "stored: false" in opening, "the sample reads as the store's text"


def test_the_pane_holds_no_counterparty() -> None:
    """The page asks the face and hands the answers down (the organisation's
    ADR-0002, `dccex-app.ts`).

    A pane holding one of its own would be a second answer to what the page
    talks to, which is the rule the releases pane is held to for the same
    reason (`tests/ui/test_releases.py`).
    """
    drawn = code(PANE.read_text())
    assert '"../face.js"' not in drawn, "the pane holds the face"
    assert "fetch(" not in drawn, "the pane asks somebody itself"
    assert "http" not in drawn, "the pane names an address"


def test_the_pane_compiles_nothing() -> None:
    """The face compiles an applied script and refuses one that does not, with
    the line and the message (ADR-0015 d.5, `face.py`).

    There is no Python in a browser, and a second opinion here about what
    compiles is exactly the disagreement that would put a text in the store
    that the translator cannot load.
    """
    drawn = code(PANE.read_text())
    assert "compile" not in drawn, "the pane judges a script itself"


def test_the_pane_works_no_reading_out_of_its_own() -> None:
    """No clock, no socket and no protocol: what it draws is a function of what
    the page handed it and what somebody typed (ADR-0009 d.1).

    `window` is the one thing it reaches, and it reaches it for one question:
    the page being closed with unapplied edits in the editor, which is a thing
    only the browser can tell it (ADR-0015 d.5).
    """
    drawn = code(PANE.read_text())
    for held in ("Date", "setInterval", "setTimeout", "WebSocket", "decoder.js"):
        assert held not in drawn, f"the pane reaches {held}"
    assert drawn.count("window.") == 2, "the pane reaches the window for something else"
    assert 'addEventListener("beforeunload"' in drawn
    assert 'removeEventListener("beforeunload"' in drawn, "a listener outlives the pane"


def test_the_page_asks_the_face_and_the_pane_edits() -> None:
    """The three asks are the page's, as the flash's is: what the pane does is
    pick, edit and press (#185, `tests/ui/test_page.py`)."""
    page = code(APP.read_text())
    assert 'from "../face.js";' in page, "the page asks nobody"
    for asked in ("applies,", "railroads,", "script,"):
        assert asked in page, f"the page does not ask for {asked.rstrip(',')}"
    pane = page[page.index("#script(): TemplateResult {") :]
    pane = pane[: pane.index("\n  }")]
    assert ".railroads=${this.railroads}" in pane, "the pane is handed no railroads"
    assert ".opens=${this.#opens}" in pane, "the pane is handed no way to open one"
    assert ".applies=${this.#applies}" in pane, "the pane is handed no way to apply"


def test_the_railroads_are_asked_for_once_and_not_on_a_schedule() -> None:
    """What a store holds changes when somebody draws a railroad in
    `control`'s editor, not under the eye: a page that asked every five
    seconds would be polling another app's store for an answer that is the
    same all evening (ADR-0010). The way to ask again is to reload.

    That the page starts no timer for it is held where the timers are counted
    (`tests/ui/test_page.py`).
    """
    page = APP.read_text()
    joining = page[
        page.index("override connectedCallback(") : page.index("/** Let the stream go")
    ]
    assert joining.count("this.#holds();") == 1, "the railroads are asked twice"
    holding = page[page.index("async #holds(): Promise<void> {") :]
    holding = holding[: holding.index("\n  }")]
    assert "await railroads()" in holding, "the page asks nobody for the railroads"


def test_the_pane_is_hidden_and_not_taken_away() -> None:
    """Unapplied edits are held in the pane and nowhere else until Apply
    (ADR-0015 d.5), so a pane built again on the way back from the monitor
    would have discarded somebody's typing without asking — which is the one
    thing this view promises not to do."""
    assert '?hidden=${this.view !== "script"}' in code(
        APP.read_text()
    ), "the pane is taken away"
    assert (
        ":host([hidden])" in STYLES.read_text()
    ), "a host with a display of its own is drawn whatever hidden says"


def test_the_addresses_are_built_from_the_one_prefix() -> None:
    """The prefix is written once and everything is built from it: a second
    spelling would be a second answer to where the app is, and the day the
    door's route moves only one of them would follow (ADR-0004 d.2,
    `face.ts`)."""
    asking = code(FACE.read_text())
    assert "RAILROADS_PATH = `${FACE}/railroads`" in asking
    assert (
        "`${FACE}/scripts/${encodeURIComponent(railroad)}`" in asking
    ), "the railroad is not escaped into one level of the address"


def test_a_railroad_with_no_script_is_told_apart_from_one_that_is_away() -> None:
    """A `404` is a railroad nobody has written a script for and opens on the
    sample; anything else is a page that has not been told what the store
    holds and must not offer to overwrite it (ADR-0009 d.2, ADR-0015 d.5)."""
    asking = code(FACE.read_text())
    reading = asking[asking.index("export async function script(") :]
    reading = reading[: reading.index("\n}")]
    assert "answered.status === NOT_FOUND" in reading, "the two read alike"
    assert "return opened(null)" in reading, "a railroad with none opens on nothing"
    assert "} catch {" in reading, "a face that is away takes the page with it"


def test_the_editor_is_monospace_and_takes_a_tab() -> None:
    """A script is Python, where the indentation is the structure: a
    proportional font hides which lines line up, and a Tab in a text area is a
    browser moving to the next control unless the page takes it (#185)."""
    editor = rule(STYLES.read_text(), ".script")
    assert "font-family: var(--sl-font-mono)" in editor, "the editor is not monospace"
    drawn = code(PANE.read_text())
    assert "<textarea" in drawn, "the editor is not a text area"
    assert (
        'event.key !== "Tab"' in drawn and "event.preventDefault()" in drawn
    ), "a Tab leaves the editor"
    assert "tabbed(" in drawn, "what a Tab puts in is the pane's own"


def test_the_pane_is_the_work_panes_and_not_the_chromes() -> None:
    """The chrome's values say *this is the same project* across rails49's UIs
    and stay on the chrome; a pane follows the system's theme, which is
    Shoelace's tokens (LOOK.md).

    The one look value it may ask for is `--rail-button`, and it is a size
    rather than a colour: it is the rules' minimum for a thumb, and this view
    is pressed on a phone held at the layout.
    """
    styles = STYLES.read_text()
    assert not HEX.findall(styles), "the pane writes a colour out"
    asked = set(re.findall(r"var\((--[a-z0-9-]+)\)", styles))
    borrowed = {token for token in asked if not token.startswith("--sl-")}
    assert borrowed == {"--rail-button"}, f"the pane takes the chrome's {borrowed}"


def test_the_script_is_a_view_the_rail_offers() -> None:
    """One entry in the list both ends of the page read, and one shape on the
    rail (`view.ts`, `tests/ui/test_rail.py`). Which view a hash names is run
    rather than read (`ui/test/view.test.ts`)."""
    assert '"script"' in VIEW.read_text(), "the hash names no script view"
    assert "script: mdi" in RAIL.read_text(), "the rail draws it with no shape"
