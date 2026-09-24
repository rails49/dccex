"""Where the page opens the **stream**, and what it reads off it.

Read off the sources rather than run. The gate is Python and needs no node on
the machine it runs on (`scripts/check.sh`, `tests/ui/test_look.py`), and the
one check that runs the page runs it inside the image and carries the `docker`
marker (`tests/ui/test_page_serves.py`); neither of them has a browser to open
a socket with. So what is held here is the part a reader of the sources can be
held to, and the first of them is the one a wrong answer to would take the page
off the box it was written for: the stream is opened on the page's **own**
origin, under the prefix the door strips, with no host and no port written into
the page anywhere (ADR-0004 d.2, d.3).

What none of it proves is that a browser does any of this. That is the cost of
a page checked in a Python gate, and it is the same cost `test_look.py` names.
"""

import re

from tests.ui.test_look import UI

#: Where the stream is, and what arrives on it.
STREAM = UI / "src" / "stream.ts"

#: Where the mirror's face is: the one place the page spells the prefix.
FACE = UI / "src" / "face.ts"

#: The prefix the mirror's face answers under on the page's origin, and the
#: whole of what it claims there (ADR-0004 d.2).
PREFIX = "/dccex-usb"

#: What a string literal must not carry: a host, an origin, or either of the
#: two ports this repository serves. Held against the literals rather than the
#: file, so that prose naming 2560 is prose and a literal naming it is a page
#: that has stopped being about its own origin.
NAMED = re.compile(r"://|BOX_DOMAIN|localhost|127\.0\.0\.1|\b(?:2560|8080)\b")


def modules() -> dict[str, str]:
    """Every module the page is made of, by file name.

    Both languages. Five of them are JavaScript with their types in JSDoc —
    what a line means, what is sent for what was typed, what the band and the
    tiles read, how the releases are listed, and what is done to the railroad
    before one is written — because those five are run under a bare node
    (`tests/ui/test_decoder.py`, `tests/ui/test_message.py`,
    `tests/ui/test_readings.py`, `tests/ui/test_releases.py`,
    `tests/ui/test_flash.py`), and a rule held over "every module" that looked
    at one language would stop holding the day a module changed it.
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


def test_the_stream_is_opened_on_the_page_s_own_origin() -> None:
    """One socket, opened at the page's own location.

    A browser is held to the origin of the page it loaded, and the face answers
    under a prefix on that origin (ADR-0004), so the address of the stream is
    the page's own address with the scheme swapped and nothing else touched.
    """
    source = STREAM.read_text()
    assert (
        "new URL(STREAM_PATH, where.href)" in source
    ), "the stream's address is not built from the page's own location"
    assert "new WebSocket(streamAt(window.location))" in source
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
    is no time on it but this one.
    """
    source = STREAM.read_text()
    assert "at: Date" in source, "a line the station said carries no time"
    assert "new Date()" in source


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


def test_every_line_says_which_end_of_the_conversation_it_is() -> None:
    """A line carries whether this page sent it, so the monitor can draw the
    two differently and a reader can tell their own traffic from the
    railroad's (#6). What arrives on the stream is the station's, always: the
    mirror hands a client the station's bytes and never its own."""
    source = STREAM.read_text()
    assert "readonly sent: boolean" in source, "a line does not say whose it is"
    assert "sent: false" in source, "what arrives is not marked as the station's"
    assert "sent: true" not in source, "the stream marks a line it did not send"
