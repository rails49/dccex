"""The page the conversation is shown on, read off its own sources.

The same reading rather than running that `tests/ui/test_stream.py` explains,
and the same limit: there is no browser here to scroll, so what is held is the
shape the follow rule has to have, not that a view followed. What the stream
carries and where it is opened is held over there.
"""

import re

from tests.ui.test_look import UI

#: The page the station's conversation is drawn on.
MONITOR = UI / "src" / "ui" / "dccex-monitor.ts"

#: What it is drawn with.
STYLES = UI / "src" / "ui" / "dccex-monitor.styles.ts"

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


def test_a_line_the_decoder_knows_carries_its_gloss() -> None:
    """The reading is the decoder's and the drawing is the component's.

    The page asks the pure function what a line says and puts the sentence
    beside it; no protocol is known here, where a clock and a socket are in
    reach (ADR-0009 d.1, d.3).
    """
    drawn = MONITOR.read_text()
    assert 'from "../decoder.js"' in drawn, "the monitor reads lines itself"
    assert "gloss(said.line)" in drawn


def test_a_line_with_no_gloss_is_drawn_raw_with_nothing_beside_it() -> None:
    """Nothing in the gloss column, rather than a hedge or an empty sentence
    (ADR-0009 d.2). The absence is the page saying it does not know."""
    drawn = MONITOR.read_text()
    assert drawn.count('class="gloss"') == 1, "the gloss is drawn in more than one way"
    assert (
        re.search(r"===?\s*null\s*\?\s*nothing", drawn) is not None
    ), "a line the decoder said nothing about is not drawn as nothing"


def rule(css: str, selector: str) -> str:
    """What one rule of a stylesheet declares."""
    found = re.search(rf"\n  {re.escape(selector)} \{{([^}}]*)\}}", css)
    assert found is not None, f"no rule for {selector}"
    return found.group(1)


def test_the_gloss_is_subordinate_to_the_line_the_station_said() -> None:
    """The raw bytes stay the primary reading and the sentence sits beside
    them: quieter and smaller, never instead of them (ADR-0009)."""
    styles = STYLES.read_text()
    said = rule(styles, ".said")
    glossed = rule(styles, ".gloss")
    weight = re.compile(r"color: var\(--sl-color-neutral-(\d+)\)")
    said_colour = weight.search(said)
    gloss_colour = weight.search(glossed)
    assert said_colour is not None and gloss_colour is not None
    assert int(gloss_colour.group(1)) < int(
        said_colour.group(1)
    ), "the gloss is drawn as loudly as the line the station said"
    sizes = ("2x-small", "x-small", "small", "medium", "large")
    size = re.compile(r"font-size: var\(--sl-font-size-([a-z0-9-]+)\)")
    lines_size = size.search(rule(styles, ".lines"))
    gloss_size = size.search(glossed)
    assert lines_size is not None and gloss_size is not None
    assert sizes.index(gloss_size.group(1)) < sizes.index(
        lines_size.group(1)
    ), "the gloss is drawn as large as the line the station said"
