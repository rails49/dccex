"""What the **rail** offers, and what it decides.

That both buttons are drawn, say their **view**'s word and hand a press on is
asserted by mounting the component and pressing it (`ui/test/rail.test.ts`,
#126). What is held here is what a mounted check cannot see: that the views
come from the module both ends of the page read them from, that the rail
decides nothing about which one is showing, and what the rules do with the
size of a button and with the one that is showing.

Read off the sources, for the reason `tests/ui/test_band.py` gives: happy-dom
does no layout and has no cascade, and a rail that picked for itself would
draw exactly the same two buttons.
"""

from tests.ui.test_look import UI
from tests.ui.test_monitor import rule
from tests.ui.test_stream import code

#: The chrome down the side.
RAIL = UI / "src" / "ui" / "dccex-rail.ts"

#: What it is drawn with.
STYLES = UI / "src" / "ui" / "dccex-rail.styles.ts"

#: What the views are and where the current one is kept.
VIEW = UI / "src" / "view.ts"

#: The page that hands it the view and what picks one.
APP = UI / "src" / "ui" / "dccex-app.ts"


def test_the_rail_draws_a_button_for_every_view_and_names_none_itself() -> None:
    """One button per **view**, off the list both ends of the page read.

    A rail with the two views written out in its template would go on drawing
    two the day a third arrived, and the work pane would be the only thing
    that knew. The shape each one is drawn as is named here — `dccex-icon`
    knows no icon's name (issue 167) — and it is a record over `View`, so the
    third view is a shape the type checker asks for.
    """
    drawn = code(RAIL.read_text())
    assert 'from "../view.js"' in drawn, "the rail invents its own views"
    assert "VIEWS.map(" in drawn, "the rail draws a button list of its own"
    assert "Record<View, string>" in drawn, "a view could be drawn with no shape"
    assert drawn.count("<button") == 1, "a button is written out twice"


def test_the_rail_picks_nothing_itself() -> None:
    """Which view is showing is the page's, kept in the hash.

    The rail is handed the answer and hands a press up (`ui/src/view.ts`,
    `tests/ui/test_page.py`). A rail that wrote the hash or kept a view of its
    own would draw one thing while the work pane drew another for as long as
    the two disagreed — and it is chrome, which is the part of the page that
    is the same in every rails49 UI.
    """
    drawn = code(RAIL.read_text())
    for reached in ("location", "history", "hashed(", "#view =", "state: true"):
        assert reached not in drawn, f"the rail reaches {reached}"


def test_a_button_on_the_rail_is_a_thumb_wide_and_a_thumb_high() -> None:
    """`--rail-button` is the look rules' minimum for a thumb, and the rail is
    pressed on the phone held at the layout (`ui/look/README.md`)."""
    button = rule(STYLES.read_text(), "button")
    assert "width: var(--rail-button)" in button
    assert "height: var(--rail-button)" in button


def test_the_view_being_shown_is_marked_by_a_swap_and_not_by_a_shade() -> None:
    """The chip and the glyph trade colours on the button for the view in
    front of the person.

    Dimming the other button was the alternative and says the wrong thing: a
    dim glyph is what a control that cannot be pressed looks like on this
    chrome (`dccex-band.styles.ts`, ADR-0011 d.2), and a view that can be gone
    to is not one of those.
    """
    styles = STYLES.read_text()
    showing = rule(styles, "button[aria-current]")
    assert "background: var(--band-ink)" in showing
    assert "color: var(--rail-group)" in showing
    assert "opacity" not in showing + rule(styles, "button")


def test_the_page_hands_the_rail_the_view_and_what_picks_one() -> None:
    """Both, and nothing else: the rail draws what it is given and offers what
    it is handed."""
    assert (
        "<dccex-rail .view=${this.view} .picks=${this.#picks}>" in APP.read_text()
    ), "the page does not hand the rail the view it is showing"
