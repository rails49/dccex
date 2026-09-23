"""Tests at the stream's rule, with no socket and no browser.

What a browser opens is a stream on the page's own origin, and the rule it
rides on is a key answered with a token and frames either side of it. The rule
is pure, so it is asked here directly — every frame in these tests is bytes a
test wrote, and nothing in the file opens a connection (`test_framing.py` is
the same thing one protocol further in).

What the rule carries once a mirror and a browser are on either end of it is
`test_face.py`'s, where the pty is.
"""

import pytest

from dccex_usb.stream import (
    BINARY,
    CLOSE,
    CONTINUATION,
    FIN,
    GOING_AWAY,
    MAX_FRAME_BYTES,
    NORMAL,
    PING,
    PROTOCOL_ERROR,
    TEXT,
    TOO_LARGE,
    Frame,
    Unreadable,
    accepted,
    framed,
    goodbye,
    unframed,
)

MASK = b"\x37\xfa\x21\x3d"
"""A mask a test picks. A browser picks a fresh one per frame and this picks
one, because what is under test is that it comes off again."""


def masked(payload: bytes, opcode: int = TEXT, mask: bytes = MASK) -> bytes:
    """One frame as a browser writes it: whole, masked, and text unless a test
    says otherwise — which is what a page typing at the station sends."""
    size = len(payload)
    if size <= 125:
        head = bytes((FIN | opcode, 0x80 | size))
    else:
        head = bytes((FIN | opcode, 0x80 | 126)) + size.to_bytes(2, "big")
    scrambled = bytes(byte ^ mask[place % 4] for place, byte in enumerate(payload))
    return head + mask + scrambled


def test_a_browser_s_key_is_answered_with_the_token_the_protocol_names() -> None:
    """RFC 6455's own example, so the token is held to the standard rather
    than to whatever this file computes today: a browser that disagreed would
    refuse the stream and the page would have nothing to show."""
    assert accepted("dGhlIHNhbXBsZSBub25jZQ==") == "s3pPLMBiTxaQ9kYGzzhZRbK+xOo="


def test_what_the_station_says_goes_out_whole_and_unmasked() -> None:
    """Binary, because a serial line promises no valid UTF-8 and a text frame
    has to carry it: one garbled byte would end a stream whose whole contract
    is that every byte arrives unchanged."""
    said = b"<iDCC-EX V-5.4.16 / ESP32 G-9db8d0e>"

    out = framed(said)

    assert out[0] == FIN | BINARY
    assert not out[1] & 0x80, "the mirror masked what it sent"
    assert out[2:] == said


@pytest.mark.parametrize(
    "size", [pytest.param(125, id="in the header"), pytest.param(126, id="two bytes")]
)
def test_a_frame_says_how_long_it_is_however_long_that_is(size: int) -> None:
    said = b"." * size

    out = framed(said)

    assert out.endswith(said)
    assert unframed(b"", masked(said, BINARY))[1] == [Frame(BINARY, said)]


def test_what_a_browser_types_comes_back_as_the_bytes_it_typed() -> None:
    """The mask off, and the payload handed on as it is: what ends a message
    is `>` and the mirror is what reads for it (`framing.py`)."""
    rest, frames = unframed(b"", masked(b"<t 3 50 1>"))

    assert rest == b""
    assert frames == [Frame(TEXT, b"<t 3 50 1>")]


def test_a_frame_split_across_reads_is_held_until_it_is_whole() -> None:
    """Bytes arrive in whatever chunks TCP hands over, so a rule that needed a
    whole frame in one read would be a rule about the network."""
    whole = masked(b"<t 3 50 1>")
    partial = b""
    frames: list[Frame] = []
    for at in range(len(whole)):
        partial, taken = unframed(partial, whole[at : at + 1])
        frames += taken

    assert frames == [Frame(TEXT, b"<t 3 50 1>")]
    assert partial == b""


def test_frames_arriving_together_come_off_in_the_order_they_were_sent() -> None:
    one, two = masked(b"<t 3 50 1>"), masked(b"<a 12 1>", BINARY)

    rest, frames = unframed(b"", one + two)

    assert rest == b""
    assert frames == [Frame(TEXT, b"<t 3 50 1>"), Frame(BINARY, b"<a 12 1>")]


def test_a_message_split_over_frames_is_carried_on_as_bytes() -> None:
    """A browser may split one message over a frame and its continuation, and
    what makes the halves one command is the mirror's framing rather than
    anything here."""
    _, frames = unframed(b"", masked(b"<t 3 ", TEXT) + masked(b"50 1>", CONTINUATION))

    assert [frame.payload for frame in frames] == [b"<t 3 ", b"50 1>"]


def test_an_unmasked_frame_is_a_peer_that_is_not_speaking_the_protocol() -> None:
    """A client's frames are masked. One that is not is reported and let go,
    never read anyway (control ADR-0050)."""
    with pytest.raises(Unreadable) as broke:
        unframed(b"", framed(b"<t 3 50 1>", TEXT))

    assert broke.value.code == PROTOCOL_ERROR


def test_a_frame_larger_than_is_read_is_refused_on_its_header() -> None:
    """Refused on sight rather than buffered up to: a caller that could name
    how much is held for it names how much memory this app spends, and a
    message the station answers to is a kilobyte (control ADR-0042)."""
    header = bytes((FIN | BINARY, 0x80 | 127)) + (MAX_FRAME_BYTES + 1).to_bytes(
        8, "big"
    )

    with pytest.raises(Unreadable) as broke:
        unframed(b"", header + MASK)

    assert broke.value.code == TOO_LARGE


@pytest.mark.parametrize(
    "head",
    [
        pytest.param(bytes((FIN | 0x3, 0x80)), id="a kind nobody sends"),
        pytest.param(bytes((FIN | 0x40 | BINARY, 0x80)), id="a reserved bit set"),
        pytest.param(bytes((PING, 0x80)), id="a split control frame"),
        pytest.param(
            bytes((FIN | PING, 0x80 | 126)) + (200).to_bytes(2, "big"),
            id="a control frame too long",
        ),
    ],
)
def test_a_frame_that_breaks_the_rule_is_refused(head: bytes) -> None:
    """A control frame says one thing and says it whole, and a kind nobody
    sends is a peer speaking something else."""
    with pytest.raises(Unreadable) as broke:
        unframed(b"", head + MASK)

    assert broke.value.code == PROTOCOL_ERROR


def test_a_data_frame_that_is_not_the_last_is_read_all_the_same() -> None:
    """The one header bit this does not hold anybody to: a browser splits a
    long message over a frame and its continuation, and both halves are bytes
    on their way to the mirror's own framing."""
    started = bytes((BINARY, 0x80 | 5)) + MASK
    scrambled = bytes(byte ^ MASK[place % 4] for place, byte in enumerate(b"<t 3 "))

    assert unframed(b"", started + scrambled)[1] == [Frame(BINARY, b"<t 3 ")]


def test_a_goodbye_says_why_in_a_frame_a_browser_reads() -> None:
    said = goodbye(GOING_AWAY, "the mirror let this client go")

    assert said[0] == FIN | CLOSE
    assert said[2:4] == GOING_AWAY.to_bytes(2, "big")
    assert b"the mirror let this client go" in said


def test_a_goodbye_too_long_to_carry_is_cut_rather_than_overlong() -> None:
    """A control frame holds 125 bytes and no more, so a reason nobody has
    written yet does not make an unreadable frame out of a goodbye."""
    said = goodbye(NORMAL, "why " * 100)

    assert said[1] <= 125
    assert len(said) == said[1] + 2
