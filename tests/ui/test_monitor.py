"""The page the conversation is shown on, read off its own sources.

The same reading rather than running that `tests/ui/test_stream.py` explains,
and the same limit: there is no browser here to scroll, so what is held is the
shape the follow rule has to have, not that a view followed. What the stream
carries and where it is opened is held over there.
"""

from tests.ui.test_look import UI

#: The page the station's conversation is drawn on.
MONITOR = UI / "src" / "ui" / "dccex-monitor.ts"

#: The page the monitor is one pane of.
APP = UI / "src" / "ui" / "dccex-app.ts"


def test_every_line_the_monitor_draws_carries_the_time_it_arrived() -> None:
    """Drawn as the operator's own clock says it, with the instant itself on the
    element, so nothing about when a line arrived is lost to the formatting."""
    drawn = MONITOR.read_text()
    assert "<time datetime=${" in drawn, "the time a line arrived is not drawn"
    assert "stamped(said.at)" in drawn


def test_the_view_is_measured_before_it_changes_and_followed_after() -> None:
    """Measured first, because afterwards every view is at the bottom of what it
    was.

    A monitor that read the scroll position after appending a line cannot tell a
    reader who was at the bottom from one who had scrolled up, and the
    scrolled-up one is who the rule exists for.
    """
    drawn = MONITOR.read_text()
    before = drawn.index("override willUpdate(")
    after = drawn.index("override updated(")
    assert before < after, "the measuring is written after the following"
    assert "atBottom(" in drawn[before:after], "nothing is measured before the update"
    assert (
        drawn.count("scrollTop =") == 1
    ), "the view is scrolled in more than one place"
    assert "scrollTop =" in drawn[after:], "the view is not followed after the update"


def test_the_monitor_is_the_page_s_and_is_in_the_work_pane() -> None:
    """The conversation goes in the work pane, which is where everything the
    page is about goes (ADR-0008, `dccex-app`)."""
    app = APP.read_text()
    assert 'import "./dccex-monitor.js";' in app
    assert "<dccex-monitor></dccex-monitor>" in app
    assert 'customElements.define("dccex-monitor"' in MONITOR.read_text()
