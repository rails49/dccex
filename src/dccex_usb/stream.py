"""The rule the monitor's stream rides on: what a browser sends, and what it
is sent.

The UI's monitor is a page, and a page cannot open a socket on 2560. What a
browser can open is a stream on the origin it is already on, which it does by
upgrading a request it has already made — a key on the way in, a token back,
and frames after that. The upgrade and the frames either side of it are this
file (ADR-0004 d.3, ADR-0007).

**The rule and nothing of the transport.** A handshake is a key answered with
a token, and a frame is a header, a mask and a payload. Nothing here holds a
socket, which is what lets the rule be read and tested on its own with no
mirror and no browser — `framing.py` is the same thing one protocol further
in.

**Every byte the station sends rides as binary.** A text frame has to carry
valid UTF-8 and a serial line promises none: one garbled byte would end the
stream, where the mirror's contract is that every byte reaches every client
unchanged (CONTEXT.md). What the page makes of them is the page's business.

**What a browser sends is payload and not a message.** Whole `<…>` messages
are the mirror's rule and the mirror is what applies it (`framing.py`), so a
frame's payload is handed on as the bytes it is — split across frames, or
several messages to a frame, the way a client's bytes arrive split across TCP
reads on 2560. Text and binary are the same bytes here; the browser chooses
which it types in.

**A client's frames are masked and a server's are not**, and a frame that
breaks the rule is not something to work around: it is a peer that is not
speaking the protocol, and the stream ends saying which rule it broke
(control ADR-0050).
"""

import base64
import hashlib
from typing import NamedTuple

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
"""The constant a browser's key is answered with, so that the token can only
have come from something that understood the request (RFC 6455). It proves
nothing about who asked — what does that is the origin the face is holding the
page to (ADR-0004)."""

CONTINUATION = 0x0
TEXT = 0x1
BINARY = 0x2
CLOSE = 0x8
PING = 0x9
PONG = 0xA

DATA = (CONTINUATION, TEXT, BINARY)
"""The frames that carry a caller's bytes. All three are the same bytes to the
mirror: what ends a message is `>` and not a frame (`framing.py`)."""

CONTROL = (CLOSE, PING, PONG)
"""The frames that are about the stream rather than about the station."""

FIN = 0x80
RESERVED = 0x70
OPCODE = 0x0F
MASKED = 0x80
SIZE = 0x7F

TWO_BYTES = 126
EIGHT_BYTES = 127
MAX_CONTROL = 125
"""The longest a control frame may be, and the largest size a header carries
in its own byte."""

MAX_FRAME_BYTES = 1 << 16
"""How much of one frame this reads. A message the station answers to is at
most `framing.MAX_MESSAGE` bytes, so a frame of this size is already not a
command; reading a larger one would be a buffer somebody else decides the size
of (control ADR-0042)."""

NORMAL = 1000
GOING_AWAY = 1001
PROTOCOL_ERROR = 1002
TOO_LARGE = 1009
"""Why a stream ended, in the codes a browser reads: a goodbye, the end this
app is going to, a peer that is not speaking the protocol, and a frame larger
than is read here."""


class Unreadable(Exception):
    """What arrived is not a frame this reads.

    Carries the code the browser is told it on, because that is the whole of
    what is done about it: a peer that breaks the framing rule is reported and
    let go, never guessed at (control ADR-0050).
    """

    def __init__(self, code: int, reason: str) -> None:
        super().__init__(reason)
        self.code = code
        self.reason = reason


class Frame(NamedTuple):
    """One whole frame a browser sent: what kind it is, and its bytes
    unmasked."""

    opcode: int
    payload: bytes


def accepted(key: str) -> str:
    """The token that answers a browser's key."""
    return base64.b64encode(hashlib.sha1((key + GUID).encode()).digest()).decode()


def framed(payload: bytes, opcode: int = BINARY) -> bytes:
    """One frame out: whole, unmasked, and binary unless it is said otherwise.

    Whole because nothing here has a reason to fragment — what is being framed
    is one read off the device, already sized by the read.
    """
    size = len(payload)
    if size <= MAX_CONTROL:
        head = bytes((FIN | opcode, size))
    elif size < 1 << 16:
        head = bytes((FIN | opcode, TWO_BYTES)) + size.to_bytes(2, "big")
    else:
        head = bytes((FIN | opcode, EIGHT_BYTES)) + size.to_bytes(8, "big")
    return head + payload


def goodbye(code: int = NORMAL, reason: str = "") -> bytes:
    """The frame that ends a stream, and says why in a sentence a person can
    read out of a browser's console.

    The sentence is cut to what a control frame holds rather than making the
    frame bigger than the rule allows: what it carries is why, and a reason
    that would not fit is one nobody has written yet.
    """
    said = reason.encode()[: MAX_CONTROL - 2]
    return framed(code.to_bytes(2, "big") + said, CLOSE)


def unframed(buffered: bytes, arrived: bytes) -> tuple[bytes, list[Frame]]:
    """Fold `arrived` into `buffered` and take off every whole frame.

    Returns what is still a partial frame, to be passed back as `buffered`
    next time, and the frames that completed, in the order they did — the
    shape `framing.frame` has, for the same reason: bytes arrive in whatever
    chunks TCP hands over and a rule that needed them whole would be a rule
    about the network.

    Raises `Unreadable` where what arrived is not a frame this reads. A
    header is all it takes: a size larger than `MAX_FRAME_BYTES` is refused
    on sight rather than buffered up to, so a browser cannot name how much
    this holds for it.
    """
    rest = buffered + arrived
    frames: list[Frame] = []
    while True:
        frame, taken = _one(rest)
        if frame is None:
            return rest, frames
        frames.append(frame)
        rest = rest[taken:]


def _one(data: bytes) -> tuple[Frame | None, int]:
    """The first whole frame in `data` and how many bytes it took, or None
    where there is not a whole one yet."""
    if len(data) < 2:
        return None, 0
    first, second = data[0], data[1]
    opcode = first & OPCODE
    if first & RESERVED:
        raise Unreadable(PROTOCOL_ERROR, "a frame reserved bits are set on")
    if opcode not in DATA and opcode not in CONTROL:
        raise Unreadable(PROTOCOL_ERROR, f"a frame of a kind ({opcode}) nobody sends")
    if not second & MASKED:
        raise Unreadable(
            PROTOCOL_ERROR, "a client's frames are masked, and this one was not"
        )
    size = second & SIZE
    at = 2
    if size == TWO_BYTES:
        if len(data) < at + 2:
            return None, 0
        size = int.from_bytes(data[at : at + 2], "big")
        at += 2
    elif size == EIGHT_BYTES:
        if len(data) < at + 8:
            return None, 0
        size = int.from_bytes(data[at : at + 8], "big")
        at += 8
    if opcode in CONTROL and (size > MAX_CONTROL or not first & FIN):
        raise Unreadable(PROTOCOL_ERROR, "a control frame that is split or too long")
    if size > MAX_FRAME_BYTES:
        raise Unreadable(
            TOO_LARGE,
            f"a frame of {size} bytes is more than the stream reads"
            f" ({MAX_FRAME_BYTES})",
        )
    if len(data) < at + 4 + size:
        return None, 0
    mask = data[at : at + 4]
    at += 4
    payload = bytes(
        byte ^ mask[place % 4] for place, byte in enumerate(data[at:][:size])
    )
    return Frame(opcode, payload), at + size
