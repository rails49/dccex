"""Where the page opens the **stream**, and what it reads off it.

**Where the stream is and where a line ends are run.** Both of them are
`ui/src/framing.js`'s — a scheme and a path, and bytes in with whole lines
out — and each is a pure function of what it is handed, so the pairs that
matter go through the real rules under `node`, by way of `tests/ui/framing.mjs`
(#78). The `node` marker is what asks for one: the gate does not collect these
and the workflow runs them, where a node that is not there is red rather than
skipped (`scripts/check.sh`, #101). Both were read off their source for as long
as there was no node to run them with, and reading is what a framing that kept
its delimiter or a scheme picked the wrong way round would have walked past.

**The rest is read off the sources, because the rest is the socket** — a
`WebSocket`, a timer and `window.location`. The gate has no browser to open one
with, and neither has the one check that runs the page inside the image
(`tests/ui/test_page_serves.py`, the `docker` marker). So what is held that way
is what a reader of the sources can be held to, and the first of them is the
one a wrong answer to would take the page off the box it was written for: no
host and no port is written into the page anywhere (ADR-0004 d.2, d.3). That
one stays read whatever else is run — it is a claim about every literal in
every module, which no running of a function can make.

What none of the reading proves is that a browser does any of this. That is the
cost of a page checked in a Python gate, and it is the same cost
`test_look.py` names.
"""

import re
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import pytest

from tests.ui.node import ran
from tests.ui.test_look import UI

#: The socket: where the stream is held open, and what is done with what
#: arrives on it.
STREAM = UI / "src" / "stream.ts"

#: The two rules that are not the socket — where the stream is, and where a
#: line ends — which a bare node runs rather than reads.
FRAMING = UI / "src" / "framing.js"

#: Where the mirror's face is: the one place the page spells the prefix.
FACE = UI / "src" / "face.ts"

#: What puts the two rules through themselves.
RUNNER = Path(__file__).resolve().parent / "framing.mjs"

#: The prefix the mirror's face answers under on the page's origin, and the
#: whole of what it claims there (ADR-0004 d.2).
PREFIX = "/dccex-usb"

#: What a string literal must not carry: a host, an origin, or either of the
#: two ports this repository serves. Held against the literals rather than the
#: file, so that prose naming 2560 is prose and a literal naming it is a page
#: that has stopped being about its own origin.
NAMED = re.compile(r"://|BOX_DOMAIN|localhost|127\.0\.0\.1|\b(?:2560|8080)\b")

#: Where the face answers the stream on the page's own origin, as the page
#: builds it. Written out rather than read off the module that spells it, for
#: the reason `ROUTE` is written out in `tests/ui/test_compose_serves.py`: a
#: check that took what it asserts from the file it is checking would pass on
#: whatever that file said. What holds the two spellings together is
#: `test_the_stream_is_under_the_door_s_prefix` below.
STREAM_PATH = f"{PREFIX}/stream"

#: A page's own address and what it was served over, and where the stream is
#: for a page read off it. The scheme is the only thing that changes: `wss`
#: from a page served over `https` and `ws` from one served over plain HTTP, on
#: whatever host and port the page itself came from (ADR-0004 d.3).
OPENED: dict[tuple[str, str], str] = {
    ("https://box.rails49.example/", "https:"): (
        f"wss://box.rails49.example{STREAM_PATH}"
    ),
    ("http://box.rails49.example/", "http:"): (
        f"ws://box.rails49.example{STREAM_PATH}"
    ),
    # A page served on a port opens the stream on that port, because the stream
    # is on the page's own origin and a page has one origin. Neither number is
    # written into the page; both are read off the page's address.
    ("https://box.rails49.example:8443/", "https:"): (
        f"wss://box.rails49.example:8443{STREAM_PATH}"
    ),
    ("http://box.rails49.example:5173/", "http:"): (
        f"ws://box.rails49.example:5173{STREAM_PATH}"
    ),
    # Wherever in the page the reader had got to. The path is the door's and is
    # absolute, so what the page is at reaches neither it nor anything after
    # it.
    ("https://box.rails49.example/monitor/", "https:"): (
        f"wss://box.rails49.example{STREAM_PATH}"
    ),
    ("https://box.rails49.example/index.html?at=12#foot", "https:"): (
        f"wss://box.rails49.example{STREAM_PATH}"
    ),
}

#: A conversation arriving on the socket, by what it is a case of: the frames
#: in the order the network handed them over, each with the page's clock at the
#: read that carried it. The clock is a small number because what these are
#: about is which read a line was stamped with.
ARRIVING: dict[str, tuple[tuple[str, int], ...]] = {
    "one whole line": (("<p1>\n", 10),),
    "several lines in one frame": (("<p1>\n<p0>\n<* MAIN *>\n", 10),),
    "a line across two frames": (("<p", 10), ("1>\n", 11)),
    "a frame that finishes a line and starts another": (
        ("<p1>\n<p", 10),
        ("0>\n<H 12 1>\n", 11),
    ),
    "an empty frame": (("", 10),),
    "an empty frame in the middle of a line": (("<p", 10), ("", 11), ("1>\n", 12)),
    "a carriage return before the newline": (("<p1>\r\n", 10),),
    "blank lines the station wrote": (("\n\r\n\n<p1>\n", 10),),
    "a frame that is nothing but newlines": (("\n\n\n", 10),),
    "nothing but a partial": (("<p1", 10),),
    "the same line twice in one read": (("<p1>\n<p1>\n", 10),),
}

#: What the page has of each afterwards: every whole line as the stamp it
#: carries and the line itself, in the order they completed, and what is still
#: a partial line waiting for the rest of itself.
READ: dict[str, tuple[tuple[tuple[int, str], ...], str]] = {
    "one whole line": (((10, "<p1>"),), ""),
    "several lines in one frame": (
        ((10, "<p1>"), (10, "<p0>"), (10, "<* MAIN *>")),
        "",
    ),
    # Stamped with the read that finished it, which is the read it arrived on:
    # the bytes before it were not a line yet.
    "a line across two frames": (((11, "<p1>"),), ""),
    "a frame that finishes a line and starts another": (
        ((10, "<p1>"), (11, "<p0>"), (11, "<H 12 1>")),
        "",
    ),
    "an empty frame": ((), ""),
    "an empty frame in the middle of a line": (((12, "<p1>"),), ""),
    "a carriage return before the newline": (((10, "<p1>"),), ""),
    "blank lines the station wrote": (((10, "<p1>"),), ""),
    "a frame that is nothing but newlines": ((), ""),
    "nothing but a partial": ((), "<p1"),
    # Two of them, because two of them arrived. A serial port repeats itself
    # and a page that folded these into one row would be hiding what the
    # station said (`Line`, `monitor.js`).
    "the same line twice in one read": (((10, "<p1>"), (10, "<p1>")), ""),
}


def run(asks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """What the two rules answer for `asks`, in one running of them."""
    answered: list[dict[str, Any]] = ran(RUNNER, asks, "the page's rules")
    return answered


@lru_cache(maxsize=1)
def opened() -> dict[tuple[str, str], str]:
    """Every page the suite has, put through the address rule once."""
    asks: list[dict[str, Any]] = [
        {"where": {"href": href, "protocol": protocol}, "path": STREAM_PATH}
        for href, protocol in OPENED
    ]
    return dict(zip(OPENED, (answer["opened"] for answer in run(asks)), strict=True))


@lru_cache(maxsize=1)
def framed() -> dict[str, dict[str, Any]]:
    """Every conversation the suite has, put through the framing once."""
    asks: list[dict[str, Any]] = [
        {"arrived": [list(frame) for frame in ARRIVING[case]]} for case in ARRIVING
    ]
    return dict(zip(ARRIVING, run(asks), strict=True))


def read() -> dict[str, tuple[tuple[tuple[int, str], ...], str]]:
    """What the framing made of each conversation, in the shape `READ` is in."""
    return {
        case: (
            tuple((said["at"], said["line"]) for said in answer["said"]),
            answer["rest"],
        )
        for case, answer in framed().items()
    }


def modules() -> dict[str, str]:
    """Every module the page is made of, by file name.

    Both languages. Seven of them are JavaScript with their types in JSDoc —
    what a line means, what is sent for what was typed, what the band and the
    tiles read, how the releases are listed, what is done to the railroad
    before one is written, where the stream is and where a line ends, and what
    the monitor works out without drawing — because those seven are run under a
    bare node (`tests/ui/test_decoder.py`, `tests/ui/test_message.py`,
    `tests/ui/test_readings.py`, `tests/ui/test_releases.py`,
    `tests/ui/test_flash.py`, and this module and `tests/ui/test_monitor.py`),
    and a rule held over "every module" that looked at one language would stop
    holding the day a module changed it.
    """
    return {
        module.name: module.read_text()
        for kind in ("*.ts", "*.js")
        for module in sorted((UI / "src").rglob(kind))
    }


def code(source: str) -> str:
    """A module with its prose off.

    The prose is where a page says what it is *not* doing — a sentence about
    2560 is not a page dialling it — and the back quotes it says it in are a
    template literal to a reader that cannot tell a comment from a rule. Whole
    comment lines and comment blocks come off; a `//` in the middle of a line
    is left where it is, because that is where a written-in address would sit.
    """
    without = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"^\s*//.*$", "", without, flags=re.MULTILINE)


def quoted(source: str) -> list[str]:
    """Every string literal in a module, single, double and back quoted."""
    found: list[str] = []
    for pattern in (r'"([^"\n]*)"', r"'([^'\n]*)'", r"`([^`]*)`"):
        found.extend(match.group(1) for match in re.finditer(pattern, code(source)))
    return found


@pytest.mark.node
@pytest.mark.parametrize("where", OPENED)
def test_the_stream_is_the_page_s_own_address_with_the_scheme_swapped(
    where: tuple[str, str],
) -> None:
    assert opened()[where] == OPENED[where]


@pytest.mark.node
def test_the_scheme_is_the_one_the_page_was_served_over() -> None:
    """`wss` from a page on `https` and `ws` from one on plain HTTP.

    The pair that matters, and the one a module saying every right word cannot
    be told apart by (#78). A page on `https` that opened `ws://` would be
    mixed content a browser refuses outright; one on plain HTTP that opened
    `wss://` would be asking the box for a certificate it has no reason to
    have, and the monitor would be dark on the bench.
    """
    for (href, protocol), address in opened().items():
        wanted = "wss://" if protocol == "https:" else "ws://"
        assert address.startswith(wanted), f"{href} opens {address}"
    assert {address.split(":")[0] for address in opened().values()} == {"ws", "wss"}


@pytest.mark.node
@pytest.mark.parametrize("where", OPENED)
def test_the_address_is_the_page_s_own_host_under_the_door_s_prefix_once(
    where: tuple[str, str],
) -> None:
    """Nothing of the stream's own on either side of the page's origin.

    The host and the port are the page's, whatever they are; the prefix is
    spelled once, where the door strips it; and what follows it is the one path
    the face answers a stream on. A second spelling of the prefix is what a
    page that built the address out of its own path would produce.
    """
    href, _served_over = where
    address = opened()[where]
    assert urlsplit(address).netloc == urlsplit(href).netloc
    assert address.count(PREFIX) == 1, f"{address} spells the prefix twice"
    assert address.endswith(STREAM_PATH)


@pytest.mark.node
@pytest.mark.parametrize("arriving", ARRIVING)
def test_bytes_arriving_are_taken_off_as_whole_lines(arriving: str) -> None:
    assert read()[arriving] == READ[arriving]


@pytest.mark.node
def test_a_line_a_frame_ends_in_the_middle_of_waits_for_the_rest_of_itself() -> None:
    """The criterion in one line (#78).

    Bytes arrive in whatever chunks the network hands over, so half a line is
    an ordinary read. What is held back is handed on when the newline that
    finishes it comes, stamped with the read that finished it — and a frame
    with nothing in it between the halves changes none of that.
    """
    assert read()["a line across two frames"] == (((11, "<p1>"),), "")
    assert read()["an empty frame in the middle of a line"] == (((12, "<p1>"),), "")
    assert read()["nothing but a partial"] == ((), "<p1")


@pytest.mark.node
def test_no_line_carries_the_delimiter_it_was_cut_at() -> None:
    """The newline the station wrote is where a line ends and is not part of
    it, and neither is the `\r` of a `\r\n` pair. A page that kept either
    would be drawing it in the monitor and sending it nowhere anybody
    would see it."""
    for case, (said, rest) in read().items():
        for _at, line in said:
            assert "\n" not in line, f"{case} keeps a newline"
            assert not line.endswith("\r"), f"{case} keeps a carriage return"
        assert "\n" not in rest, f"{case} holds a whole line back"


@pytest.mark.node
def test_everything_that_arrives_is_marked_as_the_station_s() -> None:
    """The mirror hands a client the station's bytes and never its own
    (ADR-0007), so nothing the framing makes is this page's. What the page sent
    is kept by the page, out of what `send` handed back (`dccex-app.ts`)."""
    for case, answer in framed().items():
        whose = [said["sent"] for said in answer["said"]]
        assert whose == [False] * len(whose), f"{case} marks a line as the page's"


def test_the_two_rules_hold_nothing() -> None:
    """No socket, no state and no clock of their own.

    Held against the source because it is the import that would bring one in.
    A line is stamped with the page's clock at the read that carried it, and
    the read is the socket's: a framing that reached for a clock itself would
    stamp a line with the moment it was cut, and two lines out of one read
    would carry different times. The address is the same kind of claim — it is
    made of what it is handed, so the page it is for is the page that asked.
    """
    source = FRAMING.read_text()
    assert "import " not in source, "the rules import something"
    for held in ("new Date(", "Math.random", "window", "document", "WebSocket"):
        assert held not in source, f"the rules reach {held}"


def test_the_stream_is_opened_on_the_page_s_own_origin() -> None:
    """One socket, opened at the page's own location.

    What the address is is run above. What is read here is the other half of
    it: that the one socket the page opens is opened at what that rule makes of
    the page's own location, rather than at something assembled beside it.
    """
    source = STREAM.read_text()
    assert "new WebSocket(streamAt(window.location, STREAM_PATH))" in source
    for name, module in modules().items():
        opened = module.count("new WebSocket(")
        assert opened == (
            1 if name == STREAM.name else 0
        ), f"{name} opens {opened} streams of its own"


def test_the_page_writes_no_host_port_or_origin_into_itself() -> None:
    """Not in the module that opens the stream, and not anywhere else.

    A page that named a host would work on the machine it was written on and
    nowhere else, and the box this UI exists for is not that machine.
    """
    for name, module in modules().items():
        for literal in quoted(module):
            assert not NAMED.search(literal), f"{name} names {literal!r}"


def test_the_stream_is_under_the_door_s_prefix() -> None:
    """The face claims the prefix and the page keeps the rest of the origin
    (ADR-0004 d.2), so the one path the page opens is under it.

    The prefix is written once, in the module that says where the face is, and
    everything the page asks for is built from that one spelling: a second
    would be a second answer to where the app is.
    """
    assert f'FACE = "{PREFIX}"' in FACE.read_text()
    assert "STREAM_PATH = `${FACE}/stream`" in STREAM.read_text()
    for name, module in modules().items():
        written = quoted(module).count(PREFIX)
        assert written == (
            1 if name == FACE.name else 0
        ), f"{name} spells the door's prefix {written} times"


def test_the_station_s_bytes_are_read_as_bytes() -> None:
    """One byte, one character, and none thrown away.

    The station's bytes ride as binary frames because a serial line promises no
    UTF-8 (ADR-0007 d.5). Decoding them as UTF-8 on this end would draw a
    replacement character where the byte the station sent should be, which is
    the page editing the conversation it is showing.
    """
    source = STREAM.read_text()
    assert 'binaryType = "arraybuffer"' in source, "the frames are not read as bytes"
    assert re.findall(r"new TextDecoder\(([^)]*)\)", source) == ['"latin1"']


def test_a_line_carries_the_time_it_arrived() -> None:
    """The page's own clock at the read that carried it.

    There is nothing on the stream but bytes (ADR-0007, ADR-0008 d.2), so there
    is no time on it but this one. That a line carries the stamp it was handed
    is run above; where that stamp comes from is the socket's, and read here —
    one clock, taken once per read, so two lines in one read carry the same
    stamp, which is what happened.
    """
    source = STREAM.read_text()
    assert source.count("const at = new Date();") == 1, "the read takes no clock"
    assert "lines(this.#partial, text, at)" in source


def test_the_page_types_up_the_stream_in_one_place() -> None:
    """One module writes to the socket, and it is the one that holds it (#6).

    What a page types on the stream reaches the mirror's own framing and goes
    down the cable, so anything written here reaches the command station. That
    is worth having in one place: a second writer somewhere on the page would
    be a second rule about what a whole message is, and the day the two
    disagree is the day a command goes down half-formed.
    """
    for module, source in modules().items():
        written = code(source).count("socket.send(")
        assert written == (
            1 if module == STREAM.name else 0
        ), f"{module} writes to the socket {written} times"


def test_what_goes_up_is_one_whole_message_and_the_rule_is_its_own() -> None:
    """The message is composed by the pure function and written in one call.

    The composing is `message.js`'s, which the gate runs pairs through
    (`tests/ui/test_message.py`); what is held here is that the stream sends
    what that function returned and nothing it assembled itself, and that it
    sends it whole — one `send` of one string, so two pages open at once cannot
    interleave a command (ADR-0007 d.2).
    """
    source = STREAM.read_text()
    assert 'from "./message.js"' in source, "the stream composes a message itself"
    assert "const said = message(typed);" in source
    assert "socket.send(said);" in source


def test_nothing_is_sent_on_a_stream_that_is_not_open() -> None:
    """A page that drew a line it had not managed to send would be telling an
    operator a command reached the station when it reached nothing (ADR-0009
    d.2). What the caller gets back is what went, or nothing."""
    source = STREAM.read_text()
    assert "socket.readyState !== WebSocket.OPEN" in source
    assert "send(typed: string): string | null" in source


def test_the_stream_says_when_it_is_open() -> None:
    """A signal of the same kind as a line arriving, and the page polls on it.

    `open()` dials and the socket is `CONNECTING`, so a message written to it
    then does not go — which is what happened to the page's first `<s>`, and
    why a healthy station read as absent until the interval fired five seconds
    later (#82). The socket having opened is therefore handed up to whoever
    asked for the stream, beside the lines, and the page asks there.

    Held against the one place a socket is dialled, which is also the place the
    reopen timer dials from
    (`test_the_stream_is_opened_on_the_page_s_own_origin`): a reopen is the
    same case, so the socket that follows an outage says it is open too rather
    than leaving the page to wait out an interval for a reading it could have
    had.
    """
    source = STREAM.read_text()
    assert (
        "constructor(said: (said: Said[]) => void, opened: () => void)" in source
    ), "the stream has no second signal to hand the open up on"
    dialling = code(source)
    dialling = dialling[dialling.index("#dial(): void {") : dialling.index("#arrived(")]
    assert 'addEventListener("open"' in dialling, "the open is never noticed"
    assert "this.#opened();" in dialling, "the open is noticed and not handed up"


def test_the_stream_holds_no_queue_of_things_to_send() -> None:
    """What was typed while the socket was down is refused and not kept.

    A message is a command to a command station, and one arriving seconds after
    it was typed, when the page has moved on, is worse than one that never went
    (#6). So `send` goes on returning `null` and the box at the foot says so
    (`test_nothing_is_sent_on_a_stream_that_is_not_open`), and nothing is held
    back here to be flushed when a socket opens.

    The page's own poll is the thing that is sent again, and it is the page
    that sends it: it is stateless and safe to repeat, which is what makes it
    the one message a page may ask twice (#82, `dccex-app.ts`).
    """
    source = code(STREAM.read_text())
    assert "= []" not in source, "the stream holds a list of its own"
    assert ".push(" not in source, "the stream keeps something back"
    sending = source[
        source.index("send(typed: string)") : source.index("#dial(): void {")
    ]
    assert sending.count("socket.send(") == 1, "the one write is not where send is"
    assert source.count("socket.send(") == 1, "something else writes to the socket"


def test_every_line_says_which_end_of_the_conversation_it_is() -> None:
    """A line carries whether this page sent it, so the monitor can draw the
    two differently and a reader can tell their own traffic from the
    railroad's (#6). What arrives on the stream is the station's, always: the
    mirror hands a client the station's bytes and never its own."""
    framing = FRAMING.read_text()
    assert "readonly sent: boolean" in framing, "a line does not say whose it is"
    for name, module in ((FRAMING.name, framing), (STREAM.name, STREAM.read_text())):
        assert "sent: true" not in module, f"{name} marks a line it did not send"
