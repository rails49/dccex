"""What the page itself does: opens the stream, polls, keeps the readings, and
shows the **view** its hash names.

Read off the sources rather than run, for the reason `tests/ui/test_stream.py`
gives — there is no browser in a Python gate to hold a timer, a socket or an
address bar. What the readings *are* is run instead, scenarios through the
real functions (`tests/ui/test_readings.py`), and so is which view a hash
names (`ui/test/view.test.ts`); what is held here is that the page feeds the
readings the station's own lines, asks the station anything at all, and reads
the view off the one place it is kept.

**That the mirror originates nothing is held on the mirror's side**, where it
can be: `tests/dccex_usb/test_station.py` runs the app's whole life against a
device that never goes away and asserts that the only bytes that reached it
are the one message a client sent (ADR-0010 d.5).
"""

import re

from tests.ui.test_look import UI
from tests.ui.test_stream import code, modules, quoted

#: The page: the chrome, the work pane, and the conversation they are made of.
APP = UI / "src" / "ui" / "dccex-app.ts"

#: Where the page asks the mirror about the mirror.
FACE = UI / "src" / "face.ts"

#: What a page that commanded track power would type at the station. The box
#: at the foot can still be typed into with any of them, which is what a raw
#: monitor is; what is counted here is a control on the page that sends one.
COMMANDS = ("<0>", "<1>", "<!>")

#: The one module that may carry the emergency stop: the flash sequence, which
#: stops the locomotives and cuts track power as its own steps, after an
#: operator has been told what flashing does and has said yes (#9, ADR-0006
#: d.2). It is the exception docs/ui/README.md already names, and it is one
#: module wide.
SEQUENCE = "flash.js"

#: The one module that may carry the two power messages: the readings, which
#: answer what the band's power button sends for what the station last said
#: about power (ADR-0011 d.1). The colour and the message are one answer there,
#: so a component cannot draw one and send the other.
POWER = "readings.js"


def test_the_page_polls_the_station_on_its_own_schedule() -> None:
    """Nothing else on the box asks (ADR-0010).

    A command station on a cable with no railroad loaded has no translator
    polling beside it, and readings made of an idle station's silence are no
    readings. So the page asks, on a schedule of its own, and the mirror keeps
    its one sentence: every byte that reached the device came from a client.
    """
    page = APP.read_text()
    assert 'const POLLS = ["<s>", "<=>"];' in page, "the page asks the station nothing"
    assert 'const CURRENTS = "<JI>";' in page, "the page does not ask for the current"
    assert 'const LIMITS = "<JG>";' in page, "the page does not ask for the limits"
    assert re.search(r"POLL_MS\s*=\s*\d+", page) is not None, "there is no schedule"
    assert "setInterval(" in page, "the page asks once and never again"
    assert "this.#stream.send(poll)" in page, "the poll does not go up the stream"


def test_the_poll_goes_up_the_way_anything_typed_does() -> None:
    """One rule about what a whole message is, and one place it is written.

    The page is one more client of the mirror's port and is subject to every
    rule that port has (ADR-0007 d.2), so its own polls go through the same
    `Stream.send` an operator's typing goes through. They skip `#sends`, which
    is what writes a line to the monitor: a poll every second that nobody
    typed is noise there (ADR-0010 d.1, amended).
    """
    page = APP.read_text()
    asking = page[page.index("#ask(): void {") : page.index("#now(): void {")]
    assert "this.#stream.send(poll)" in asking, "the poll does not go up the stream"
    assert "this.#stream.send(CURRENTS)" in asking, "the current is never asked"
    assert "this.#sends(" not in asking, "the poll is written to the monitor"


def test_the_most_each_track_may_draw_is_asked_on_the_link_and_not_the_poll() -> None:
    """The one question that is asked on the **link** rather than on the
    schedule (issue 170).

    A limit is compiled into the **build** and does not move while the station
    is running, so asking four times a second would spend every client's line on
    an answer that is the same all evening. A station running a different one has
    come up again, which is the link coming up again — so it is asked where the
    link is worked out, and a station written and restarted is asked afresh.
    """
    page = APP.read_text()
    asking = page[page.index("#ask(): void {") : page.index("#now(): void {")]
    assert "LIMITS" not in asking, "the limits are asked on the poll"
    now = page[page.index("#now(): void {") :]
    now = now[: now.index("\n  }")]
    assert (
        "asOf(" in now and "this.#stream.send(LIMITS)" in now
    ), "the limits are not asked where the link comes up"
    assert "this.readings.answering && !" in now, "they are asked on every reading"


def test_the_page_asks_when_the_stream_is_open() -> None:
    """Not while the socket is still connecting, which is where the first
    `<s>` went (#82).

    `connectedCallback` opened the stream and asked in the next line, with the
    socket `CONNECTING`; `send` refused it and returned `null`, so nothing
    left, and nothing asked again until the interval fired five seconds later.
    Until an answer arrives the readings are made of silence, so every load of
    the page said a healthy station was not answering, with the **build** blank
    on the band and no **tile**s on the monitor view.

    So the page asks on the stream saying it is open — the signal `Stream`
    hands up beside the lines (`tests/ui/test_stream.py`) — and the one `#ask`
    left in `connectedCallback` is the interval's. A reopen is the same case
    and needs nothing more: the socket drops, the reopen timer dials another,
    and the page asks as soon as that one is open rather than waiting out an
    interval.
    """
    page = APP.read_text()
    handed = page[page.index("new Stream(") : page.index("override connectedCallback(")]
    assert "this.#ask();" in handed, "the page is never told the stream is open"

    joining = page[
        page.index("override connectedCallback(") : page.index("/** Let the stream go")
    ]
    assert "this.#stream.open();" in joining
    assert joining.count("this.#ask();") == 1, "the page asks twice on connecting"
    assert joining.index("setInterval(") < joining.index("this.#ask();"), (
        "the page asks before the stream is open, which is where the first " "poll went"
    )


def test_a_stream_that_comes_back_leaves_one_schedule_running() -> None:
    """The page asks on every open and starts a timer on none of them.

    A page left open across a morning's outages reopens its stream as often as
    the cable goes (`REOPEN_MS`, `stream.ts`), and a schedule started on the
    open would be one more poller each time — a page asking the station a dozen
    times every five seconds, which is not the schedule ADR-0010 d.1 gives it.
    All three timers are started where the page joins the document and stopped
    where it leaves, and nowhere else. The third is the flash's, and it is on
    the same rule for the same reason: one started on a press would be a second
    poller for every release an operator chose (ADR-0012 d.3).
    """
    page = APP.read_text()
    joining = page[
        page.index("override connectedCallback(") : page.index("/** Let the stream go")
    ]
    assert joining.count("setInterval(") == 3, "a timer is started somewhere else"
    assert page.count("setInterval(") == 3, "the page starts a timer off the schedule"


def test_the_page_stops_asking_when_it_goes() -> None:
    """A conversation that is quiet when nobody is watching is the correct
    conversation (ADR-0010 d.4). A page that kept a timer alive after it left
    would be a poller nobody is reading the answers of."""
    page = APP.read_text()
    leaving = page[page.index("override disconnectedCallback(") :]
    assert leaving.count("clearInterval(") == 3, "a timer outlives the page"
    assert "this.#stream.close()" in leaving


def test_the_page_follows_a_flash_on_load_and_while_one_is_running() -> None:
    """Twice a second while a flash is in flight, and once on load so that a tab
    opened or reloaded mid-flash shows it (ADR-0012 d.3).

    And nothing the rest of the time. The schedule runs for as long as the page
    is in the document, as the other two do, and asks only where there is a
    flash to follow: one the mirror said is running, or one this page asked for
    and has not been answered about. A page polling a route about a flash
    nobody asked for would be asking a question with one answer, four times a
    minute each, for every tab left open on the box (ADR-0010).
    """
    page = APP.read_text()
    assert re.search(r"FOLLOW_MS\s*=\s*\d+", page) is not None, "there is no schedule"
    joining = page[
        page.index("override connectedCallback(") : page.index("/** Let the stream go")
    ]
    assert "FOLLOW_MS)" in joining, "the flash is followed off the schedule"
    assert (
        "this.flashing !== null || this.#writing" in joining
    ), "the page asks about a flash where none is running"
    assert joining.count("this.#follows();") == 2, "the page never asks on load"


def test_the_page_asks_the_face_and_the_row_presses() -> None:
    """The counterparty is the page's, the flash included (#9). A pane holding
    one of its own would be a second answer to what the page talks to, which is
    the rule `tests/ui/test_flash.py` names the owner of.

    What the row does is press; what asks the mirror to write and what asks how
    far that write has got are both here, and the row is handed the answer as it
    is handed the releases and the **build** (ADR-0012 d.3).
    """
    page = code(APP.read_text())
    assert 'import { flash, flashing, releases } from "../face.js";' in page
    writing = page[page.index("#writes = async (") :]
    assert "await flash(tag)" in writing, "the page asks nobody to write"
    assert "this.#follows()" in writing, "a write of the page's own is not followed"
    view = page[page.index("#releases(): TemplateResult {") :]
    assert ".flashing=${this.flashing}" in view, "the row is handed no flash"
    assert ".writes=${this.#writes}" in view, "the row is handed no way to write"


def test_the_view_the_work_pane_shows_is_kept_in_the_hash() -> None:
    """One place, and the page reads it rather than remembering it (#169).

    A view kept in a field of the page's own would be a view nobody could send
    to anybody, a reload would open on the monitor whatever was in front of a
    person, and the browser's back button would step off the page. So a press
    on the **rail** writes the hash and the page reads the hash: one direction
    each, and no second answer to which view is showing. Which view a hash
    names is `ui/src/view.js`'s and is run rather than read.
    """
    page = APP.read_text()
    assert 'from "../view.js"' in page, "the page names the views itself"
    assert "viewed(location.hash)" in page, "the page does not read the hash"
    assert "location.hash = hashed(" in page, "a press does not reach the address bar"


def test_the_page_hears_the_hash_change_and_lets_it_go_when_it_goes() -> None:
    """The hash changes under the page: the rail writes it, and so does the
    back button and anybody editing the address bar.

    Heard where the page joins the document and let go where it leaves, as the
    two schedules are — a listener that outlived the page would be drawing a
    view for a page that is gone.
    """
    page = APP.read_text()
    joining = page[
        page.index("override connectedCallback(") : page.index("/** Let the stream go")
    ]
    assert 'window.addEventListener("hashchange"' in joining, "the hash is read once"
    leaving = page[page.index("override disconnectedCallback(") :]
    assert 'window.removeEventListener("hashchange"' in leaving, "a listener outlives"


def test_the_monitor_view_is_drawn_only_while_it_is_showing() -> None:
    """The releases are a view of their own and the conversation is the other
    (CONTEXT.md **view**, #169).

    Taken away rather than hidden: a monitor left in the document behind the
    releases would go on measuring a scroller with no height and go on drawing
    two thousand rows nobody is looking at.
    """
    drawn = code(APP.read_text())
    monitor = drawn[
        drawn.index("#monitor(): TemplateResult {") : drawn.index(
            "#releases(): TemplateResult {"
        )
    ]
    assert "<dccex-tiles" in monitor and "<dccex-monitor" in monitor
    assert "<dccex-releases" not in monitor, "the releases are drawn on both views"
    assert 'this.view === "releases" ? nothing : this.#monitor()' in drawn


def test_the_releases_are_hidden_and_not_taken_away() -> None:
    """The one pane that stays in the document, and the flash is why (#169).

    Which step a flash is on and what became of it are that pane's
    (`dccex-releases.ts`), and the minute a write takes is when an operator
    goes to the monitor to watch the station drop and come back. A pane built
    again on the way back would have forgotten a write that is still running
    and would offer the press that starts a second one.
    """
    drawn = code(APP.read_text())
    assert '?hidden=${this.view !== "releases"}' in drawn, "the pane is taken away"
    assert (
        ":host([hidden])"
        in (UI / "src" / "ui" / "dccex-releases.styles.ts").read_text()
    ), "a host with a display of its own is drawn whatever hidden says"


def test_the_readings_are_made_of_what_the_station_said_and_not_of_the_poll() -> None:
    """A line this page sent is this page speaking.

    Folding one in would be a page keeping its own link up by polling, and the
    band would be saying that the page is running rather than that the station
    is answering (ADR-0008, control ADR-0066).
    """
    page = APP.read_text()
    keeping = page[page.index("#keep(said: Said[])") :]
    assert "if (!line.sent)" in keeping, "the page reads its own lines as the station's"
    assert "heard(this.#kept, line.line, line.at.getTime())" in keeping


def test_the_link_can_go_down_with_nothing_arriving() -> None:
    """The link going down is the absence of a line, so it happens on the
    clock: a page that only worked the readings out when the station spoke
    would say a station was answering for as long as it stayed silent."""
    page = APP.read_text()
    assert re.search(r"TICK_MS\s*=\s*\d+", page) is not None, "the readings never tick"
    assert "asOf(this.#kept, Date.now())" in page, "the readings are never worked out"


def test_two_modules_command_track_power_and_the_rest_of_the_page_does_not() -> None:
    """The band's power button and the flash sequence, and nothing else.

    `control`'s band presses power because `layout` checks the railroad is
    drained first; this page is on no bus, and that check never guarded the
    station — any client of the mirror's port sends `<0>` or `<1>` and the
    guard is the operator (ADR-0011, superseding ADR-0008 d.5). So the two
    messages are in the readings, where what the button says and what it sends
    are one answer, and the emergency stop is in the sequence, which is held
    below.

    Held against the literals rather than the prose, because saying what the
    page does not command is not commanding it — and because the one thing that
    may still carry `<0>` anywhere is what an operator types into the box,
    which is not a literal at all.
    """
    for name, module in modules().items():
        if name in (SEQUENCE, POWER):
            continue
        for literal in quoted(module):
            assert literal not in COMMANDS, f"{name} sends {literal}"


def test_the_readings_carry_the_two_the_power_button_sends_and_no_stop() -> None:
    """`<0>` and `<1>`, which are the two a press offers depending on what the
    station last said about power (ADR-0011 d.1).

    Not the emergency stop: stopping the locomotives is a step of writing a
    release and is the sequence's, and a band that could send `<!>` would be
    one press from halting a railroad nobody warned.
    """
    sent = [literal for literal in quoted(modules()[POWER]) if literal in COMMANDS]

    assert set(sent) == {"<0>", "<1>"}, f"the readings send {sent}"


def test_the_flash_sequence_is_the_one_caller_that_cuts_power() -> None:
    """It stops the locomotives and cuts the rails before a release is
    written, in that order, and an operator is warned and asked first (#9,
    ADR-0006 d.2). What the sequence *does* with them is run rather than read
    (`tests/ui/test_flash.py`); what is held here is that this is the only
    module that carries one at all.

    **And nothing turns power back on.** A page that put the rails back after
    a flash would be commanding power with nothing having checked what is on
    the layout — the thing this page does not do (ADR-0008 d.5). What happens
    after a station comes back is the operator's.
    """
    sent = [literal for literal in quoted(modules()[SEQUENCE]) if literal in COMMANDS]

    assert set(sent) == {"<!>", "<0>"}, f"the sequence sends {sent}"
