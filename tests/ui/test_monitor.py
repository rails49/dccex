"""The page the conversation is shown on.

**What it works out without drawing is run.** Whether the reader is at the
bottom, the time a line arrived, which repeats are worth showing and the
conversation itself — what is on screen, what waits behind a pause, and what a
line arriving, a press of the pause and a press of the clear do to either —
are `ui/src/monitor.js`'s, and each is a pure function of what it is handed, so
the pairs that matter go through the real rules under `node`, by way of
`tests/ui/monitor.mjs` (#78, #125, #144). The `node` marker is what asks for
one: the gate does not collect these and the workflow runs them, where a node
that is not there is red rather than skipped (`scripts/check.sh`, #101). The
first two were read off their source for as long as there was no node to run
them with, and reading is what a stamp an hour out would have walked past —
and what the page's own keeping was read off its source for as long as it was
written there, which is how a pause that suppressed the line it had dropped
and a resume that left a silent gap were both walked past twice (#142, #143).

**What it draws is mounted** (#126). A conversation handed to the component in
happy-dom is read back off the rows: the line the **decoder** knows carrying its
**gloss**, the line it does not carrying nothing at all, the stamp on every row
and the mark on the ones this page sent — and the two controls pressed, the
pause saying what pressing it will do, and what is waiting read off the count
(`ui/test/monitor.test.ts`, #144). An absence is what a source-text check was
worst at — a template drawing an empty sentence and one drawing none read the
same off the source.

**The rest is read off its own sources**, as `tests/ui/test_stream.py` explains
and with the same limit: happy-dom does no layout, so there is still no browser
here to scroll, and what is held that way is the shape the follow rule has to
have rather than that a view followed. What the stream carries and where it is
opened is held over there.
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

#: The rules that are not drawing, which a bare node runs rather than reads.
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
    """What the rules answer for `asks`, in one running of them.

    In a zone of this module's choosing, because one of them is about the
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


def test_the_rules_hold_nothing() -> None:
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


def test_the_reading_a_line_carries_is_the_decoder_s() -> None:
    """No protocol is known here, where a clock and a socket are in reach
    (ADR-0009 d.1, d.3): the page asks the pure function what a line says and
    puts the sentence beside it.

    That the sentence reaches the row it is about, and that a line the decoder
    said nothing about gets none, is the mounted check's
    (`ui/test/monitor.test.ts`). A monitor that knew the protocol itself would
    draw the same sentences until the two readings parted, which is what this
    one is for.
    """
    assert (
        'from "../decoder.js"' in MONITOR.read_text()
    ), "the monitor reads lines itself"


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
    assert "said: readonly Shown[] = []" in drawn, "the lines are not handed down"
    assert "sends: (typed: string) => string | null" in drawn
    app = APP.read_text()
    assert "new Stream(" in app, "nothing on the page opens the stream"
    assert ".said=${this.conversation.said}" in app
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


def test_the_colour_a_sent_line_is_drawn_in_is_not_the_whole_distinction() -> None:
    """A mark and a colour, not a colour alone.

    Which lines this page put on the railroad is the one thing the monitor must
    not be ambiguous about, and a distinction carried by colour alone is no
    distinction to a reader who does not see it. The mark is read off a mounted
    row (`ui/test/monitor.test.ts`); the colour beside it and the column the
    mark sits in are the stylesheet's, which happy-dom has no cascade to ask.
    """
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
        re.search(r"repeat\(\s*this\.said,\s*\(said: Shown\) => said\.key,", drawn)
        is not None
    ), "the conversation is not drawn keyed by the key it was kept under"


def test_two_identical_lines_in_the_same_millisecond_are_two_rows() -> None:
    """The key is assigned when a line is kept and is nothing the line carries.

    A line and the moment it arrived in are both ordinary to see twice on a
    serial port, so a key made of either would draw two rows as one. That no
    two entries of a conversation are keyed the same is run rather than read,
    below.
    """
    keying = MONITOR.read_text()
    keying = keying[keying.index("repeat(") : keying.index("const read = gloss(")]
    assert "said.at" not in keying, "the key is made of when the line arrived"
    assert "said.line" not in keying, "the key is made of what the line says"


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


def test_the_loco_slot_count_is_shown_only_when_it_changes() -> None:
    """Another client asks `<#>` every thirty seconds and every client sees
    the answer, `<# 120>`, which does not change."""
    said = [("<# 120>", False), ("<# 120>", False), ("<# 50>", False)]
    assert quiet(said)["shown"] == [True, False, True]


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


#: A queue with nothing in it and nothing dropped, as the runner takes one.
EMPTY: dict[str, Any] = {"lines": [], "dropped": 0}


def queued(behind: dict[str, Any], said: list[str]) -> dict[str, Any]:
    """The queue after `said` arrived behind a pause, and what went to make
    room for it."""
    answered: dict[str, Any] = run([{"queue": {"behind": behind, "said": said}}])[0]
    return answered


@lru_cache(maxsize=1)
def own() -> dict[str, Any]:
    """The module's own three, asked of it rather than read off it: how many
    lines the page keeps, how many the queue holds, and the queue with nothing
    in it.

    The numbers are the module's to choose and this suite's to hold the shape
    to: what is asserted below is that the oldest queued lines go past the cap
    and are counted, and that the cap is a quarter of what is kept, at
    whatever either of them is.
    """
    answered: dict[str, Any] = run([{"own": True}])[0]
    return answered


def cap() -> int:
    """How many lines wait behind a pause."""
    held: int = own()["queue"]
    return held


def kept() -> int:
    """How many lines the page keeps."""
    shown: int = own()["kept"]
    return shown


def says(behind: dict[str, Any]) -> str | None:
    """What the monitor says about a queue, or `None` where it says nothing."""
    said: str | None = run([{"waiting": behind}])[0]["says"]
    return said


#: A press of the pause, and a press of the clear, as the runner takes them.
HOLDS: dict[str, Any] = {"held": True}
CLEARS: dict[str, Any] = {"cleared": True}


def heard(lines: list[str]) -> dict[str, Any]:
    """A step of a conversation: `lines`, arriving from the station."""
    return {"said": [[line, False] for line in lines]}


def keeping(steps: list[dict[str, Any]]) -> dict[str, Any]:
    """The conversation `steps` leaves behind, from the one a page opens
    with."""
    answered: dict[str, Any] = run([{"keeping": steps}])[0]
    return answered


def lines(conversation: dict[str, Any]) -> list[str | None]:
    """What the entries on screen say, in the order they are drawn. A note the
    page put there says nothing the station said, and reads as `None`."""
    said: list[dict[str, Any]] = conversation["said"]
    return [entry.get("line") for entry in said]


@pytest.mark.node
def test_lines_that_arrive_while_paused_are_queued_in_arrival_order() -> None:
    """Out of sight and in the order they came, so resuming appends the
    conversation as the station held it."""
    behind = queued(EMPTY, ["<p1 A>", "<p0 B>"])
    assert behind["lines"] == ["<p1 A>", "<p0 B>"]
    assert queued(behind, ["<X>"])["lines"] == ["<p1 A>", "<p0 B>", "<X>"]


@pytest.mark.node
def test_the_queue_has_a_cap_and_the_oldest_queued_lines_go_past_it() -> None:
    """The oldest *queued* lines, and not the conversation on screen: what a
    pause promises is that nothing the reader is looking at is trimmed, and
    what it cannot promise is an unbounded queue behind it."""
    behind = queued(EMPTY, [f"<H {n} 1>" for n in range(cap() + 5)])
    assert len(behind["lines"]) == cap()
    assert behind["lines"][0] == "<H 5 1>", "the newest queued lines went"
    assert behind["dropped"] == 5


@pytest.mark.node
def test_what_was_dropped_is_counted_across_arrivals() -> None:
    """The count is of the whole pause and not of the last arrival: a reader
    coming back to a monitor that has been full for a minute is owed how much
    of the conversation went, not how much went in the last read."""
    full = queued(EMPTY, [f"<H {n} 1>" for n in range(cap())])
    assert full["dropped"] == 0
    assert queued(queued(full, ["<X>"]), ["<Y>", "<Z>"])["dropped"] == 3


@pytest.mark.node
def test_a_monitor_that_is_not_paused_holds_an_empty_queue() -> None:
    """The one the page starts at, and the one resuming and clearing leave
    behind: nothing waiting and nothing dropped."""
    assert own()["emptied"] == EMPTY


@pytest.mark.node
def test_the_count_says_how_many_lines_are_waiting() -> None:
    """A reader who has paused a busy station is told what is piling up behind
    it, so the pause is a decision they can take back knowingly."""
    assert says(queued(EMPTY, [f"<H {n} 1>" for n in range(137)])) == "137 waiting"
    assert says(queued(EMPTY, ["<X>"])) == "1 waiting"


@pytest.mark.node
def test_what_the_queue_dropped_is_said_and_not_hidden() -> None:
    """A gap is shown, never hidden: a queue that quietly forgot the oldest of
    what it was holding would have the page pretending the station was quiet
    (ADR-0009 d.2)."""
    full = queued(EMPTY, [f"<H {n} 1>" for n in range(cap() + 12)])
    assert says(full) == f"{cap()} waiting, 12 dropped"


@pytest.mark.node
def test_a_queue_with_nothing_in_it_says_nothing() -> None:
    """Nothing is waiting, so there is no count to read — an empty monitor
    does not carry a `0 waiting` for the whole of an evening."""
    assert says(EMPTY) is None


@pytest.mark.node
def test_what_the_queue_dropped_is_handed_back_and_not_only_counted() -> None:
    """The caller has something to forget about a line that went (#142), so
    the lines themselves come back beside the count."""
    behind = queued(EMPTY, [f"<H {n} 1>" for n in range(cap() + 3)])
    assert behind["went"] == ["<H 0 1>", "<H 1 1>", "<H 2 1>"]
    assert queued(EMPTY, ["<X>"])["went"] == []


@pytest.mark.node
def test_the_queue_is_a_quarter_of_what_the_page_keeps() -> None:
    """One number and not two (#152). The queue is appended to the
    conversation on a resume and the usual trim applies from there, so a queue
    as long as the conversation would mean resuming replaced the whole of what
    the pause was holding still. The quarter was prose in three places and
    arithmetic in none, which is a quarter nothing kept true."""
    assert cap() == kept() / 4


@pytest.mark.node
def test_nothing_on_screen_is_trimmed_while_the_view_is_held() -> None:
    """Which is the whole of what a pause is for (#125).

    Scrolling up already holds the view, but at capacity the page goes on
    dropping the oldest lines and the reader loses the line they are reading.
    So a conversation at capacity is paused here and fifty more lines arrive:
    not one of the entries on screen moves, and the fifty wait behind the
    pause.
    """
    full = [f"<H {n} 1>" for n in range(kept())]
    more = [f"<H {n} 2>" for n in range(50)]
    before = keeping([heard(full)])
    after = keeping([heard(full), HOLDS, heard(more)])
    assert len(before["said"]) == kept()
    assert [entry["key"] for entry in after["said"]] == [
        entry["key"] for entry in before["said"]
    ], "the conversation moved under the reader while the view was held"
    assert len(after["behind"]["lines"]) == 50, "the arrivals were not queued"


@pytest.mark.node
def test_resuming_appends_the_queue_in_arrival_order_and_trims_from_there() -> None:
    """Through the one trim there is, so what a reader resumes into is trimmed
    exactly as a line that arrived is (#125)."""
    full = [f"<H {n} 1>" for n in range(kept())]
    more = [f"<H {n} 2>" for n in range(50)]
    after = keeping([heard(full), HOLDS, heard(more), HOLDS])
    assert len(after["said"]) == kept(), "the resume was not trimmed"
    assert lines(after)[-50:] == more, "the queue was not appended as it arrived"
    assert after["behind"] == EMPTY, "the queue outlived the pause"
    assert after["paused"] is False


@pytest.mark.node
def test_a_line_this_page_sent_waits_behind_the_pause_with_the_rest() -> None:
    """The pause is the view, and the view is one thing.

    A page that let the operator's own line through would be appending to the
    conversation while it was held, which at capacity is a trim — the one
    thing a pause promises there will not be. The line still went: the stream
    is not paused, the send is not refused, and the count turning over is what
    says so.
    """
    after = keeping([HOLDS, {"said": [["<s>", True], ["<X>", False]]}])
    assert after["said"] == [], "the operator's own line went on the screen"
    waits: list[dict[str, Any]] = after["behind"]["lines"]
    assert [entry["line"] for entry in waits] == ["<s>", "<X>"]
    assert [entry["sent"] for entry in waits] == [True, False]


@pytest.mark.node
def test_the_gap_a_full_queue_left_is_marked_where_it_is() -> None:
    """A resume said how much went and then said nothing about it (#143).

    The count the monitor was carrying — "500 waiting, 12 dropped" — goes away
    with the pause that made it, so a reader came back to twelve lines of
    conversation missing and nothing at all marking the place. One note goes
    in where the gap is, ahead of the lines that survived, and it is trimmed
    and cleared like any other entry.
    """
    arriving = [f"<H {n} 1>" for n in range(cap() + 12)]
    after = keeping([HOLDS, heard(arriving), HOLDS])
    said: list[dict[str, Any]] = after["said"]
    assert len(said) == cap() + 1
    assert said[0]["note"] == "12 lines dropped while paused"
    assert "line" not in said[0], "the gap is drawn as something the station said"
    assert lines(after)[1:] == arriving[12:], "the queue did not follow the note"


@pytest.mark.node
def test_a_resume_that_dropped_nothing_marks_nothing() -> None:
    """There is no gap, so there is nothing to say about one: a note on every
    resume would be the page talking about itself in a conversation about a
    railroad."""
    after = keeping([HOLDS, heard(["<X>", "<Y>"]), HOLDS])
    assert lines(after) == ["<X>", "<Y>"]


@pytest.mark.node
def test_a_subject_the_queue_dropped_says_something_new_again() -> None:
    """The pause suppressed the line it had thrown away (#142).

    Paused, a `<p1>` is queued and then pushed off the front of a full queue —
    so it never reached the conversation. It still stood for what the power
    last said, and every later poll answering `<p1>` was left out as nothing
    new, so the monitor never said the power came on. A line that went is
    forgotten with it.
    """
    filling = [f"<H {n} 1>" for n in range(cap())]
    after = keeping([HOLDS, heard(["<p1>"]), heard(filling), HOLDS, heard(["<p1>"])])
    said: list[dict[str, Any]] = after["said"]
    assert said[0]["note"] == "1 line dropped while paused"
    assert said[-1].get("line") == "<p1>", "the power coming on was never shown"


@pytest.mark.node
def test_a_subject_the_queue_still_holds_is_not_forgotten() -> None:
    """Only the line that went is forgotten, and only while it is still what
    its subject last said.

    `<p1>` and `<p0>` are one subject — the power — so a queue that dropped
    the older of the two and forgot the subject would show the newer one twice.
    """
    filling = [f"<H {n} 1>" for n in range(cap() - 1)]
    after = keeping(
        [HOLDS, heard(["<p1>", "<p0>"]), heard(filling), HOLDS, heard(["<p0>"])]
    )
    assert lines(after)[1] == "<p0>", "the line that went was not the oldest"
    assert lines(after)[-1] != "<p0>", "a repeat of what is on screen was shown"


@pytest.mark.node
def test_clearing_empties_the_conversation_and_the_queue_and_nothing_else() -> None:
    """A clear is the reader emptying what is on screen, not the page
    forgetting what the station has told it (#125).

    What each subject last said stays, so a poll answered the same way after a
    clear is still not news, and the view is still held if that is how the
    reader left it.
    """
    emptied = keeping([heard(["<p1 A>"]), HOLDS, heard(["<X>"]), CLEARS])
    assert emptied["said"] == [], "the conversation was not emptied"
    assert emptied["behind"] == EMPTY, "a queue survived the clear"
    assert emptied["paused"] is True, "the clear let the view go"
    again = keeping(
        [heard(["<p1 A>"]), HOLDS, heard(["<X>"]), CLEARS, HOLDS, heard(["<p1 A>"])]
    )
    assert again["said"] == [], "the clear forgot what the subject last said"


@pytest.mark.node
def test_a_key_is_assigned_once_and_never_reused() -> None:
    """Stable for the life of an entry, which is what makes the row its own.

    One counter, never wound back: a conversation that renumbered what it
    holds on a trim or on a clear would hand the monitor the same shift the
    keys are there to save it (#74).
    """
    steps = [heard(["<X>", "<X>"]), HOLDS, heard(["<Y>", "<Z>"])]
    paused = keeping(steps)
    waits: list[dict[str, Any]] = paused["behind"]["lines"]
    keys = [entry["key"] for entry in paused["said"]] + [
        entry["key"] for entry in waits
    ]
    assert keys == sorted(keys), "the entries are not keyed in the order they came"
    assert len(set(keys)) == len(keys), "two entries are keyed the same"
    after = keeping([*steps, HOLDS, CLEARS, heard(["<W>"])])
    assert after["said"][0]["key"] > max(
        keys
    ), "a cleared entry's key was handed out again"


def test_the_page_holds_the_conversation_and_the_rules_change_it() -> None:
    """The conversation is the page's and what happens to it is the rules'
    (#125, #144).

    The page holds one value and calls three functions of it, and the monitor
    draws the two controls and is handed what they do, the way it is handed
    its lines and its sending: a pane that kept a queue of its own would be
    keeping part of the conversation where the band and the tiles cannot see
    it. That the controls are there and do what they are handed is read off a
    mounted monitor (`ui/test/monitor.test.ts`); where the rules live is a
    claim about the source, because a DOM cannot see which module worked an
    answer out.
    """
    app = APP.read_text()
    assert 'from "../monitor.js"' in app
    for calls in (
        "arrived(this.conversation, said)",
        "held(this.conversation)",
        "cleared(this.conversation)",
    ):
        assert calls in app, f"the page does not call {calls}"
    for handed in (
        ".paused=${this.conversation.paused}",
        ".behind=${this.conversation.behind}",
    ):
        assert handed in app, f"the monitor is not handed {handed}"
    assert ".pauses=${this.#pauses}" in app
    assert ".clears=${this.#clears}" in app
    drawn = MONITOR.read_text()
    for kept in ("queued(", "arrived(", "QUEUE ="):
        assert kept not in drawn, f"the monitor keeps the conversation itself: {kept}"


def test_a_pause_stops_neither_the_stream_the_polling_nor_the_tiles() -> None:
    """It is the view and not the conversation (#125).

    Every line is heard into the readings before the conversation is told
    about it and whether the view is held or not, so the band and the tiles go
    on saying what the station is doing while a reader holds the monitor
    still. The page reads the pause nowhere: it hands every line it heard to
    the rules and they decide what becomes of it. The stream and the two
    intervals are never spoken to by either control.
    """
    app = APP.read_text()
    keeping = app[app.index("#keep(said: Said[])") :]
    assert keeping.index("heard(this.#kept") < keeping.index(
        "arrived(this.conversation"
    ), "the conversation is told before the readings hear it"
    assert "this.#now()" in keeping, "a paused page works out no readings"
    assert "paused" not in keeping, "the page reads the pause itself"
    for pressed in ("#pauses = ", "#clears = "):
        body = app[app.index(pressed) :]
        body = body[: body.index("};")]
        for untouched in ("#stream", "setInterval(", "clearInterval(", "#kept"):
            assert untouched not in body, f"{pressed.strip()} reaches {untouched}"


def test_the_controls_are_their_own_row_and_sized_for_a_thumb() -> None:
    """Above the lines and out of the scroller, so they do not move with the
    conversation, and quieter than the send: what is typed is what goes on the
    railroad, and holding the view is not."""
    drawn = MONITOR.read_text()
    assert drawn.index('class="controls"') < drawn.index(
        'class="lines"'
    ), "the controls are inside or below the conversation"
    styles = STYLES.read_text()
    controls = rule(styles, ".controls")
    assert "flex: none" in controls, "the controls grow with the conversation"
    quieter = rule(styles, ".controls button")
    assert (
        "background:" in quieter and "primary" not in quieter
    ), "the pause and the clear are drawn as loudly as the send"


def test_a_line_this_page_sent_goes_through_the_same_keeping() -> None:
    """The line the operator typed is kept the way an arriving one is, which
    is what puts it behind a pause with the rest (run above).

    The page has one way in for both, so there is nowhere for a sent line to
    take a shorter road into a held conversation.
    """
    app = APP.read_text()
    sending = app[app.index("#sends = ") :]
    assert "this.#keep(" in sending[: sending.index("};")], "a sent line skips the keep"
