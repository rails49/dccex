"""The page the conversation is shown on.

**Two of what it works out are run.** Whether the reader is at the bottom and
the time a line arrived are `ui/src/monitor.js`'s — three numbers off a
scroller, and a `Date` — and each is a pure function of what it is handed, so
the pairs that matter go through the real rules under `node`, by way of
`tests/ui/monitor.mjs` (#78). The `node` marker is what asks for one: the gate
does not collect these and the workflow runs them, where a node that is not
there is red rather than skipped (`scripts/check.sh`, #101). Both were read off
their source for as long as there was no node to run them with, and reading is
what a stamp an hour out would have walked past.

**The rest is read off its own sources**, as `tests/ui/test_stream.py` explains
and with the same limit: there is no browser here to scroll, so what is held
that way is the shape the follow rule has to have, not that a view followed.
What the stream carries and where it is opened is held over there.
"""

import re
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

import pytest

from tests.ui.node import ran
from tests.ui.test_look import UI

#: The page the station's conversation is drawn on.
MONITOR = UI / "src" / "ui" / "dccex-monitor.ts"

#: What it is drawn with.
STYLES = UI / "src" / "ui" / "dccex-monitor.styles.ts"

#: The page the monitor is one pane of.
APP = UI / "src" / "ui" / "dccex-app.ts"

#: The two rules that are not drawing, which a bare node runs rather than
#: reads.
RULES = UI / "src" / "monitor.js"

#: What puts them through themselves.
RUNNER = Path(__file__).resolve().parent / "monitor.mjs"

#: A scroller as the three numbers being at the bottom of one is a question
#: about — how tall what is in it is, how far down it has been scrolled, and
#: how much of it a reader can see — and whether that is a reader the newest
#: line should be scrolled to.
SCROLLED: dict[str, tuple[tuple[float, float, float], bool]] = {
    "at the bottom": ((1000, 800, 200), True),
    # A scroller a rounded sub-pixel from the end is a reader who has not
    # scrolled up, which is the whole of what the slack is for: the numbers a
    # browser gives back do not add up exactly, and a monitor that asked for
    # zero would stop following the tail on its own.
    "a fraction off the bottom": ((1000.5, 800.25, 200), True),
    "one pixel off the bottom": ((1000, 799, 200), True),
    "the whole of the slack off the bottom": ((1000, 796, 200), True),
    "a pixel past the slack": ((1000, 795, 200), False),
    "a line or two up": ((1000, 700, 200), False),
    "at the top of a long conversation": ((10000, 0, 200), False),
    # Less in it than it can show: there is nowhere to have scrolled up to, and
    # a reader looking at three lines is following the tail.
    "shorter than its viewport": ((120, 0, 200), True),
    "nothing said yet": ((0, 0, 200), True),
}

#: What a clock in the operator's own zone reads when a line arrives, and the
#: stamp the monitor draws beside it. To the millisecond, because a burst of
#: `<…>` messages arrives inside one second, and padded, because a column of
#: stamps a person is reading down is a column.
STAMPED: dict[tuple[int, int, int, int], str] = {
    (13, 4, 5, 7): "13:04:05.007",
    (0, 0, 0, 0): "00:00:00.000",
    (23, 59, 59, 999): "23:59:59.999",
    (9, 30, 0, 50): "09:30:00.050",
    (7, 8, 9, 100): "07:08:09.100",
}

#: One instant on the stream, in milliseconds since the epoch.
INSTANT = int(datetime(2026, 1, 1, 13, 4, 5, 7000, tzinfo=UTC).timestamp() * 1000)

#: What that instant is stamped as, by where the machine reading it is. Zones
#: with no summer time in them, so the pair holds in January and in July alike.
ZONED: dict[str, str] = {
    "UTC": "13:04:05.007",
    "Pacific/Honolulu": "03:04:05.007",
}

#: A stamp: a time on a clock, to the millisecond, and no date on it.
CLOCK = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3}$")


def run(asks: list[dict[str, Any]], zone: str = "UTC") -> list[dict[str, Any]]:
    """What the two rules answer for `asks`, in one running of them.

    In a zone of this module's choosing, because one of the two is about the
    machine's own: a stamp is the operator's clock rather than UTC, and a check
    that ran in whatever zone the machine happened to be set to could not tell
    those two apart on a box in London.
    """
    answered: list[dict[str, Any]] = ran(RUNNER, asks, "the page's rules", zone=zone)
    return answered


@lru_cache(maxsize=1)
def bottom() -> dict[str, bool]:
    """Every scroller the suite has, put through the rule once."""
    asks: list[dict[str, Any]] = [
        {
            "scroller": {
                "scrollHeight": height,
                "scrollTop": top,
                "clientHeight": seen,
            }
        }
        for (height, top, seen), _bottom in SCROLLED.values()
    ]
    return dict(zip(SCROLLED, (answer["bottom"] for answer in run(asks)), strict=True))


@lru_cache(maxsize=1)
def stamps() -> dict[tuple[int, int, int, int], str]:
    """Every arrival the suite has, put through the stamp once."""
    asks: list[dict[str, Any]] = [{"clock": list(clock)} for clock in STAMPED]
    return dict(zip(STAMPED, (answer["stamp"] for answer in run(asks)), strict=True))


@pytest.mark.node
@pytest.mark.parametrize("scrolled", SCROLLED)
def test_whether_the_reader_is_at_the_bottom_of_the_conversation(
    scrolled: str,
) -> None:
    _where, at = SCROLLED[scrolled]
    assert bottom()[scrolled] is at


@pytest.mark.node
def test_the_slack_is_a_rounded_sub_pixel_and_not_a_line() -> None:
    """The criterion in one line (#78).

    What the slack is for is the arithmetic: a browser's three numbers do not
    always add up to zero at the end of a scroller. What it is not for is
    forgiving a reader who has scrolled up — a line of the conversation is
    taller than it, so scrolling back by one line is a reader the tail stops
    being followed for.
    """
    assert bottom()["the whole of the slack off the bottom"] is True
    assert bottom()["a pixel past the slack"] is False


@pytest.mark.node
def test_a_scroller_with_less_in_it_than_it_shows_is_at_its_own_bottom() -> None:
    """There is nowhere to have scrolled up to, so a reader watching the first
    three lines of an evening is following the tail — and the conversation
    nothing has been said in yet is the same reader."""
    assert bottom()["shorter than its viewport"] is True
    assert bottom()["nothing said yet"] is True


@pytest.mark.node
@pytest.mark.parametrize("clock", STAMPED)
def test_a_line_is_stamped_to_the_millisecond(clock: tuple[int, int, int, int]) -> None:
    assert stamps()[clock] == STAMPED[clock]


@pytest.mark.node
def test_the_stamp_is_the_clock_of_the_machine_reading_it() -> None:
    """Local time, because the person reading is at the layout correlating what
    they saw with what the station said (#78).

    One instant, two machines, two stamps ten hours apart — which is the thing
    a module saying `getHours` reads exactly like whether it is right or an
    hour out. What is not lost to it is the instant itself: that rides on the
    element's `datetime`, which is read below.
    """
    for zone, drawn in ZONED.items():
        answered = run([{"at": INSTANT}], zone)
        assert answered[0]["stamp"] == drawn, f"a clock in {zone} reads it otherwise"


@pytest.mark.node
def test_a_stamp_is_a_time_and_carries_no_date() -> None:
    """A conversation a person is reading as it arrives is today's, and a date
    on every row would be a column of the same eleven characters between the
    reader and the bytes."""
    for clock, drawn in stamps().items():
        assert CLOCK.match(drawn) is not None, f"{clock} is stamped {drawn!r}"


def test_the_two_rules_hold_nothing() -> None:
    """No state, no clock of their own and no DOM.

    Held against the source because it is the import that would bring one in.
    A stamp is of the moment a line arrived, which the page took at the read
    that carried it (`stream.ts`), and a module that could reach a clock could
    stamp a line with when it was drawn instead. Whether the reader is at the
    bottom is three numbers somebody else read off an element, for the same
    reason: a rule that went looking for the element would be a rule only a
    browser could be asked.
    """
    source = RULES.read_text()
    assert "import " not in source, "the rules import something"
    for held in ("new Date(", "Math.random", "window", "document", "querySelector"):
        assert held not in source, f"the rules reach {held}"


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
    assert 'import { type Said } from "../framing.js"' in drawn
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
    a size and not one of the chrome's colours, which is what makes it the one
    look value a control on the work pane may ask for — this box's send, and the
    flash on a release's row (#9, `tests/ui/test_releases.py`).
    """
    styles = STYLES.read_text()
    assert "min-height: var(--rail-button)" in styles, "the box is not thumb-sized"
    typed = rule(styles, ".typed")
    assert "flex: 1 1 auto" in typed
    assert "min-width: 0" in typed, "a long command pushes the send off the side"
    assert "flex: none" in rule(styles, "button"), "the send button shrinks away"


def test_the_rows_are_keyed_by_the_key_the_page_gave_each_line() -> None:
    """Keyed, so a line falling off the front moves the rows above it rather
    than re-committing every binding on all two thousand of them (#74).

    Lit's unkeyed diff matches template instances by position, and at capacity
    every arriving frame shifts every row by one — which is a few thousand
    times the work the page needs, exactly when the station is busiest.
    """
    drawn = MONITOR.read_text()
    assert (
        'from "lit/directives/repeat.js"' in drawn
    ), "the conversation is drawn unkeyed"
    assert "this.said.map(" not in drawn, "the rows are still matched by position"
    assert (
        re.search(r"repeat\(\s*this\.said,\s*\(said: Keyed\) => said\.key,", drawn)
        is not None
    ), "the conversation is not drawn keyed by the key the page assigned"


def test_two_identical_lines_in_the_same_millisecond_are_two_rows() -> None:
    """The key is assigned when a line is kept and is nothing the line carries.

    A line and the moment it arrived in are both ordinary to see twice on a
    serial port, so a key made of either would draw two rows as one. It is the
    page's to assign, because the page is what keeps the conversation.
    """
    keying = MONITOR.read_text()
    keying = keying[keying.index("repeat(") : keying.index("const read = gloss(")]
    assert "said.at" not in keying, "the key is made of when the line arrived"
    assert "said.line" not in keying, "the key is made of what the line says"
    app = APP.read_text()
    keeping = app[app.index("#keep(said: Said[])") :]
    assert "key: this.#keys++" in keeping, "the page numbers nothing it keeps"


def test_a_key_is_assigned_once_and_never_reused() -> None:
    """Stable for the life of a line, which is what makes the row the line's.

    One counter, incremented in one place and never wound back: a page that
    renumbered what it holds on a trim would hand the monitor the same shift it
    was keyed to avoid.
    """
    app = APP.read_text()
    assert (
        app.count("this.#keys++") == 1
    ), "the lines are numbered in more than one place"
    assert (
        app.count("#keys = 0") == 1
    ), "the counter is wound back somewhere after it is declared"


def test_several_frames_arriving_before_the_next_paint_are_one_update() -> None:
    """One update per animation frame, which is what a reader can see (#74).

    Lit batches what changes within a task and WebSocket frames arrive in their
    own tasks, so a busy line is one update per frame; waiting for the frame
    the browser will paint coalesces the burst into the one drawing of it
    anybody looks at.
    """
    drawn = MONITOR.read_text()
    assert "override async scheduleUpdate(" in drawn, "every arriving frame is drawn"
    scheduling = drawn[drawn.index("override async scheduleUpdate(") :]
    assert "requestAnimationFrame(" in scheduling, "the update waits for nothing"
    assert "super.scheduleUpdate()" in scheduling, "the update is never made"


def test_the_place_a_reader_holds_is_a_row_and_not_a_number_of_pixels() -> None:
    """A trim takes lines off the front, and a position measured from the front
    moves under the reader by the height of what went (#75).

    So what is held across an update is a row and where in the view that row
    sat. A row is carried up with everything below it, so putting the view back
    on the row puts the reader back where they were — for a trim of any size,
    and for nothing at all, since an update that only appended moves no row
    already drawn.
    """
    drawn = MONITOR.read_text()
    holding = drawn[
        drawn.index("override willUpdate(") : drawn.index("override updated(")
    ]
    assert "holding(scroller)" in holding, "nothing is held before the lines change"
    assert (
        "below: sits(scroller, row)" in drawn
    ), "the place held is not a row and where it sat"
    following = drawn[drawn.index("override updated(") :]
    assert "this.#back(scroller)" in following, "the reader is not put back"
    assert (
        "scroller.scrollTop + sits(scroller, held.row) - held.below" in drawn
    ), "the view is not moved by what the row moved by"


def test_the_correction_is_measured_and_not_counted() -> None:
    """Off the rectangles, so it is right for rows of any height.

    `offsetTop` is rounded to whole pixels, and a fraction of a pixel lost on
    every trim is a view that creeps away from the line the reader is on. The
    row that is measured against is the newest one drawn — lines arrive below
    it, so nothing arriving moves it — and it is measured only while it is
    still on the page.
    """
    drawn = MONITOR.read_text()
    assert "getBoundingClientRect()" in drawn, "the place is not measured"
    assert ".offsetTop" not in drawn, "the place is measured in whole pixels"
    assert ".line:last-of-type" in drawn, "the row held is not the one a trim spares"
    assert "isConnected" in drawn, "a row that is gone is still measured against"


def test_a_reader_at_the_bottom_still_follows_the_tail() -> None:
    """The two readers are the two branches of one answer (#4, #75).

    One at the bottom is put on the end of the conversation, one who has
    scrolled up is put back on their row, and the view is set in the one place
    either way — so there is one answer to where it goes.
    """
    drawn = MONITOR.read_text()
    following = drawn[drawn.index("override updated(") :]
    assert (
        re.search(r"this\.#following\s*\?\s*scroller\.scrollHeight", following)
        is not None
    ), "a reader at the bottom no longer follows the tail"
    assert (
        drawn.count("scrollTop =") == 1
    ), "the view is scrolled in more than one place"


def test_nothing_rests_on_the_browser_s_scroll_anchoring() -> None:
    """The scroller says so itself (#75).

    Scroll anchoring is best-effort, it is off in cases of its own and it is
    not the same in every browser, so the criterion that the view does not move
    under a reader who has scrolled up cannot rest on it. The component does
    the arithmetic; the browser is told not to do any of its own.
    """
    assert "overflow-anchor: none" in rule(
        STYLES.read_text(), ".lines"
    ), "the scroller leans on the browser's scroll anchoring"


def test_the_lines_scroll_and_not_the_pane_they_are_in() -> None:
    """The monitor's row in the work pane cannot grow with the conversation.

    A bare `1fr` row grows to fit what is in it, so a long conversation made
    the work pane scroll and left the lines' own scroller with nothing to do.
    The row has a floor of its own instead of the content's height, so the
    lines are what scrolls. This reads the rule rather than laying the page
    out; #127 is where a browser checks it.
    """
    work = rule((UI / "src" / "ui" / "dccex-app.styles.ts").read_text(), ".work")
    rows = re.search(r"grid-template-rows: ([^;]+);", work)
    assert rows is not None, "the work pane does not say how its rows are sized"
    assert re.search(
        r"minmax\([^)]*\)$", rows.group(1)
    ), "the monitor's row grows with the conversation"


#: One answer to `<s>`, as the station on the layout sent it (5.6.4, EX-CSB1,
#: 2026-09-25).
STATUS = [
    "<iDCC-EX V-5.6.4 / ESP32 / EXCSB1_WITH_EX8874 G-v5.6.4-rails49.1>",
    "<p1 A>",
    "<p1 B>",
    "<p1 C>",
    "<p1 D>",
    "<p1>",
    "<p1 MAIN>",
    '<@ 0 2 "PWR On">',
]


def quiet(
    said: list[tuple[str, bool]], last: dict[str, str] | None = None
) -> dict[str, Any]:
    """What the monitor shows of `said`, given what each subject last said."""
    ask = {"quiet": {"last": last or {}, "said": [list(line) for line in said]}}
    answered: dict[str, Any] = run([ask])[0]
    return answered


def test_the_first_answer_to_a_poll_is_shown_whole() -> None:
    """Nothing has been said about any of it yet, so all of it is news."""
    assert quiet([(line, False) for line in STATUS])["shown"] == [True] * len(STATUS)


def test_an_answer_that_repeats_the_last_one_is_not_shown() -> None:
    """The log was a banner and seven power lines every five seconds, from
    every open page. A second answer that says what the first said is left
    out of the monitor."""
    first = quiet([(line, False) for line in STATUS])
    again = quiet([(line, False) for line in STATUS], first["last"])
    assert again["shown"] == [False] * len(STATUS)


def test_a_line_that_changed_is_shown_and_the_rest_are_not() -> None:
    """Track B going off is the one thing in the answer worth reading."""
    first = quiet([(line, False) for line in STATUS])
    changed = [line.replace("<p1 B>", "<p0 B>") for line in STATUS]
    shown = quiet([(line, False) for line in changed], first["last"])["shown"]
    assert shown == [line == "<p0 B>" for line in changed]


def test_each_track_is_its_own_subject() -> None:
    """`<p1 A>` and `<p1 B>` in one answer are two readings, not a repeat."""
    assert quiet([("<p1 A>", False), ("<p1 B>", False), ("<p1>", False)])["shown"] == [
        True,
        True,
        True,
    ]


def test_modes_are_shown_only_when_they_change() -> None:
    """The per-track mode lines repeat on a poll the same way."""
    first = quiet([("<= A MAIN>", False)])
    assert quiet([("<= A MAIN>", False)], first["last"])["shown"] == [False]
    assert quiet([("<= A PROG>", False)], first["last"])["shown"] == [True]


def test_currents_and_limits_are_never_shown() -> None:
    """The measured current moves on nearly every poll, so showing it when it
    changed would be showing it every time. The tiles are where it is read."""
    said = [
        ("<jI 13 2 0 0>", False),
        ("<jG 1233 1233>", False),
        ("<jI 14 2 0 0>", False),
    ]
    assert quiet(said)["shown"] == [False, False, False]


def test_a_line_that_is_not_a_status_line_is_always_shown() -> None:
    """A turnout, a refusal, anything the monitor does not know: every time."""
    said = [("<H 12 1>", False), ("<X>", False), ("<H 12 1>", False)]
    assert quiet(said)["shown"] == [True, True, True]


def test_what_this_page_sent_is_always_shown_and_hides_nothing() -> None:
    """A line typed here is the operator's and is shown every time. It is not
    the station speaking, so it does not count as the last thing a subject
    said."""
    first = quiet([("<= A MAIN>", False)])
    said = [("<= A MAIN>", True), ("<= A MAIN>", True)]
    answered = quiet(said, first["last"])
    assert answered["shown"] == [True, True]
    assert answered["last"] == first["last"]
