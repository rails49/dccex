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


def test_a_line_the_page_sent_is_kept_as_the_page_s_own() -> None:
    """The line the page keeps is what `send` handed back, which is what left
    it, and it is marked as this page's so the monitor can draw it as such."""
    app = APP.read_text()
    sending = app[app.index("#sends = ") :]
    assert "this.#stream.send(typed)" in sending
    assert "line: sent, sent: true" in sending, "the line kept is not what went"
    assert sending.index("sent !== null") < sending.index(
        "line: sent"
    ), "a line is kept before it is known that anything was sent"


def test_the_monitor_is_the_page_s_and_is_in_the_work_pane() -> None:
    """The conversation goes in the work pane, which is where everything the
    page is about goes (ADR-0008, `dccex-app`)."""
    app = APP.read_text()
    assert 'import "./dccex-monitor.js";' in app
    assert "<dccex-monitor" in app
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


def test_the_box_at_the_foot_sends_what_is_typed_in_it() -> None:
    """One form, submitted, and what goes up is the stream's to write (#6).

    A form rather than a key handler, because what sends a command on a phone
    is the keyboard's own send key and what sends it on a laptop is Enter, and
    a form is the one thing both of them reach.
    """
    drawn = MONITOR.read_text()
    assert 'class="box" @submit=${this.#send}' in drawn, "there is no box to type in"
    assert 'class="typed"' in drawn
    assert 'type="submit"' in drawn, "the box cannot be sent on a phone"
    assert "this.sends(box.value)" in drawn, "the box sends nothing"


def test_the_monitor_is_handed_its_lines_and_its_sending() -> None:
    """The conversation is the page's and not this pane's (#7).

    The band and the tiles are made of the same bytes the monitor draws
    (ADR-0008 d.2), so the page holds the stream and hands the lines down. A
    monitor that owned it would be the one pane of the page the rest had to
    ask, and a second stream for the readings would be a second client of the
    mirror's port for one page.
    """
    drawn = MONITOR.read_text()
    assert "new Stream(" not in drawn, "the monitor opens a stream of its own"
    assert 'import { type Said } from "../stream.js"' in drawn
    assert "sends: (typed: string) => string | null" in drawn
    app = APP.read_text()
    assert "new Stream(" in app, "nothing on the page opens the stream"
    assert ".said=${this.said}" in app
    assert ".sends=${this.#sends}" in app


def test_the_box_clears_only_for_what_left_the_page() -> None:
    """A command that was not sent — nothing typed, or no stream open to send
    it on — leaves the typing where it is and draws no line: a line claiming
    the station was asked something it was never asked is the observation
    nobody made (ADR-0009 d.2)."""
    sending = MONITOR.read_text()
    sending = sending[sending.index("#send(") :]
    assert re.search(r"if \(sent === null\) \{\s*return;", sending) is not None
    assert sending.index("sent === null") < sending.index(
        'box.value = ""'
    ), "the box is cleared before it is known that anything was sent"


def test_a_line_this_page_sent_is_drawn_differently_from_one_the_station_said() -> None:
    """A mark and a colour, not a colour alone.

    Which lines this page put on the railroad is the one thing the monitor must
    not be ambiguous about, and a distinction carried by colour alone is no
    distinction to a reader who does not see it.
    """
    drawn = MONITOR.read_text()
    assert 'said.sent ? "line sent" : "line"' in drawn, "a sent line is not marked"
    assert "said.sent ? SENT_MARK : nothing" in drawn
    styles = STYLES.read_text()
    said = rule(styles, ".said")
    sent = rule(styles, ".sent .said")
    assert "color:" in sent and sent.strip() != said.strip()
    assert "width: 1ch" in rule(
        styles, ".mark"
    ), "the mark column collapses on a line with no mark in it"


def test_the_box_is_usable_at_the_width_of_a_phone() -> None:
    """A thumb's worth of height, and a field that shrinks rather than pushing
    the send button off the side.

    `--rail-button` is the look rules' minimum for a thumb (`look.css`). It is
    a size and not one of the chrome's colours, which is what makes it the
    value the work pane's one control may ask for.
    """
    styles = STYLES.read_text()
    assert "min-height: var(--rail-button)" in styles, "the box is not thumb-sized"
    typed = rule(styles, ".typed")
    assert "flex: 1 1 auto" in typed
    assert "min-width: 0" in typed, "a long command pushes the send off the side"
    assert "flex: none" in rule(styles, "button"), "the send button shrinks away"
