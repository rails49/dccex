"""What the **rail** offers, and what it decides.

That every view is offered, named, drawn and handed on is asserted by drawing
the rail and choosing a view (`ui/test/rail.test.ts`). What is held here is
what a drawn check cannot see: that the views come from the module both ends
of the page read them from, and that the rail decides nothing about which one
is showing. The rail itself is look's (ADR-0023).
"""

from tests.ui.paths import UI
from tests.ui.test_stream import code

#: The band and the rail, as look's elements.
CHROME = UI / "src" / "ui" / "chrome.ts"

#: The page that draws them and listens for a choice.
APP = UI / "src" / "ui" / "dccex-app.ts"


def test_the_rail_draws_a_view_for_every_view_and_names_none_itself() -> None:
    """One `look-view` per **view**, off the list both ends of the page read.

    A rail with the views written out in its template would go on drawing four
    the day a fifth arrived, and the work pane would be the only thing that
    knew. What each is called and drawn as is a record over `View` in
    `view.ts`, so a fifth view is a glyph the type checker asks for.
    """
    drawn = code(CHROME.read_text())
    assert 'from "../view.js"' in drawn, "the rail invents its own views"
    assert "VIEWS.map(" in drawn, "the rail draws a list of its own"
    assert drawn.count("<look-view") == 1, "a view is written out twice"
    assert "Record<View, { label: string; icon: string }>" in code(
        (UI / "src" / "view.ts").read_text()
    ), "a view could be drawn with no glyph"


def test_the_rail_picks_nothing_itself() -> None:
    """Which view is showing is the page's, kept in the hash.

    A choice goes up as `look-view` and the page writes the hash; the view
    comes back down from it (`ui/src/view.ts`, `tests/ui/test_page.py`).
    """
    drawn = code(CHROME.read_text())
    for reached in ("location", "history", "hashed("):
        assert reached not in drawn, f"the rail reaches {reached}"
    page = code(APP.read_text())
    assert "@look-view=" in page, "nothing listens for a view being chosen"
    assert (
        "this.#picks(viewed(e.detail.name))" in page
    ), "a chosen view does not go through the hash"
