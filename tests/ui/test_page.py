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
    """
    for name, module in modules().items():
        for literal in quoted(module):
            assert literal not in COMMANDS, f"{name} sends {literal}"
