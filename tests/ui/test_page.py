"""What the page itself does: opens the stream, polls, and keeps the readings.

Read off the sources rather than run, for the reason `tests/ui/test_stream.py`
gives — there is no browser in a Python gate to hold a timer or a socket. What
the readings *are* is run instead, scenarios through the real functions
(`tests/ui/test_readings.py`); what is held here is that the page feeds them
the station's own lines and asks the station anything at all.

**That the mirror originates nothing is held on the mirror's side**, where it
can be: `tests/dccex_usb/test_station.py` runs the app's whole life against a
device that never goes away and asserts that the only bytes that reached it
are the one message a client sent (ADR-0010 d.5).
"""

import re

from tests.ui.test_look import UI
from tests.ui.test_stream import modules, quoted

#: The page: the chrome, the work pane, and the conversation they are made of.
APP = UI / "src" / "ui" / "dccex-app.ts"

#: Where the page asks the mirror about the mirror.
FACE = UI / "src" / "face.ts"

#: What a page that commanded track power would type at the station. The box
#: at the foot can still be typed into with any of them, which is what a raw
#: monitor is; what may not exist is a control on the page that sends one
#: (ADR-0008 d.5).
COMMANDS = ("<0>", "<1>", "<!>")

#: The one module that may carry one of them: the flash sequence, which stops
#: the locomotives and cuts track power as its own steps, after an operator has
#: been told what flashing does and has said yes (#9, ADR-0006 d.2). It is the
#: exception docs/ui/README.md already names, and it is one module wide.
SEQUENCE = "flash.js"


def test_the_page_polls_the_station_on_its_own_schedule() -> None:
    """Nothing else on the box asks (ADR-0010).

    A command station on a cable with no railroad loaded has no translator
    polling beside it, and readings made of an idle station's silence are no
    readings. So the page asks, on a schedule of its own, and the mirror keeps
    its one sentence: every byte that reached the device came from a client.
    """
    page = APP.read_text()
    assert 'const POLL = "<s>";' in page, "the page asks the station nothing"
    assert re.search(r"POLL_MS\s*=\s*\d+", page) is not None, "there is no schedule"
    assert "setInterval(" in page, "the page asks once and never again"
    assert "this.#sends(POLL)" in page, "the poll does not go up the stream"


def test_the_poll_goes_up_the_way_anything_typed_does() -> None:
    """One rule about what a whole message is, and one place it is written.

    The page is one more client of the mirror's port and is subject to every
    rule that port has (ADR-0007 d.2), so its own polls go through the same
    `send` an operator's typing goes through — which is also what marks them
    as this page's in the monitor (ADR-0010 d.1).
    """
    page = APP.read_text()
    asking = page[page.index("#ask(): void {") : page.index("#now(): void {")]
    assert "this.#stream.send" not in asking, "the poll dials past the page's own send"
    assert "this.#sends(POLL)" in asking


def test_the_page_asks_when_the_stream_is_open() -> None:
    """Not while the socket is still connecting, which is where the first
    `<s>` went (#82).

    `connectedCallback` opened the stream and asked in the next line, with the
    socket `CONNECTING`; `send` refused it and returned `null`, so nothing
    left, and nothing asked again until the interval fired five seconds later.
    Until an answer arrives the readings are made of silence, so every load of
    the page said a healthy station was not answering and left the **build**
    tile blank.

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
    Both timers are started where the page joins the document and stopped where
    it leaves, and nowhere else.
    """
    page = APP.read_text()
    joining = page[
        page.index("override connectedCallback(") : page.index("/** Let the stream go")
    ]
    assert joining.count("setInterval(") == 2, "a timer is started somewhere else"
    assert page.count("setInterval(") == 2, "the page starts a timer off the schedule"


def test_the_page_stops_asking_when_it_goes() -> None:
    """A conversation that is quiet when nobody is watching is the correct
    conversation (ADR-0010 d.4). A page that kept a timer alive after it left
    would be a poller nobody is reading the answers of."""
    page = APP.read_text()
    leaving = page[page.index("override disconnectedCallback(") :]
    assert leaving.count("clearInterval(") == 2, "a timer outlives the page"
    assert "this.#stream.close()" in leaving


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


def test_the_count_of_clients_comes_off_the_face() -> None:
    """The one reading that is not the station talking (ADR-0008 d.4), asked
    for on the page's own origin under the prefix the door strips."""
    assert "CLIENTS_PATH = `${FACE}/clients`" in FACE.read_text()
    assert "clients().then(" in APP.read_text(), "the page never asks the face"


def test_a_face_that_did_not_answer_says_nothing_rather_than_nobody() -> None:
    """A face that is away, a status that is not a 200, an answer that is not
    a count: `null`, and the tile blanks. Drawing `0` for an app the page
    could not ask would be reporting an empty port nobody saw (ADR-0009
    d.2).

    Read over the count alone. The other thing asked of the face answers the
    same way for the same reason and is held where it is drawn
    (`tests/ui/test_releases.py`).
    """
    asking = FACE.read_text()
    counting = asking[
        asking.index("export async function clients(") : asking.index(
            "export const RELEASES_PATH"
        )
    ]
    assert "Promise<number | null>" in asking
    assert counting.count("return null;") == 3, "a way of not knowing reads as a count"
    assert "} catch {" in counting, "a face that is away takes the page with it"


def test_nothing_on_the_page_commands_track_power() -> None:
    """`control`'s band presses ON, STOP and OFF because `layout` checks the
    railroad is drained first; this page is on no bus for anything to check,
    so a press here would go down the cable with nothing having checked
    (ADR-0008 d.5).

    Held against the literals rather than the prose, because saying what the
    page does not command is not commanding it — and because the one thing
    that may still carry `<0>` is what an operator types into the box, which
    is not a literal anywhere.

    The flash sequence is the one exception and is held below: it cuts power as
    a step of writing a release, which is the one caller docs/ui/README.md has
    always named (#9).
    """
    for name, module in modules().items():
        if name == SEQUENCE:
            continue
        for literal in quoted(module):
            assert literal not in COMMANDS, f"{name} sends {literal}"


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
