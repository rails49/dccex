"""What the station says, and the three facts this app reads out of it.

The station writes `<…>` messages to every client, replies and unasked
broadcasts alike, and one byte stream cannot say which a line is —
`dccex-usb` fans the whole conversation to everybody and routes nothing
(control ADR-0043). So what arrives here is everything the station has to say to
anyone, and the reading is deliberately narrow: the power each track is in,
whether the emergency-stop lock is on, the diagnostic lines that say a district
tripped (ADR-0016), the stash entry a boot clears (ADR-0021), and the turnouts the station keeps of its own, which are read for a **script** to be keyed on and for nothing else
(ADR-0013 d.3). Everything else — the banner, a slot's speed, a sensor it
polls, a fast clock — is another client's business and is passed over unread.

Pure, both of them. `messages` is the framing rule, bytes in and whole
messages out; `reply` is one message read into a fact or into `None`. Neither
raises, and a message this app does not recognise is not an error: it is the
ordinary case, most of the traffic on the port being somebody else's.

`dccex-usb` frames the same `<…>` delimiters and this is not shared with it.
Apps import `tc49.lib` and themselves, never each other (control ADR-0013), and the
delimiters are the hardware's rather than a contract of ours — `dccex-usb`
mirrors a device and holds its own copy for the same reason it imports
nothing else of ours.
"""

import re
from dataclasses import dataclass

from dccex.commands import STASH_ID

MAX_MESSAGE = 1024
"""How long a message may grow before it is taken for a broken sender. The
station's longest line is its status banner; nothing it says approaches this,
so a buffer that passes it is a stream that has lost its `>` and is dropped
rather than grown without bound."""

START = ord("<")
END = ord(">")

TRACKS = "ABCDEFGH"
"""The letters a track can be called. A `<p…>` line naming anything else —
`MAIN`, `PROG`, `JOIN` — is naming a **mode** rather than a district, and is
passed over: reading it as a track would put a district on the railroad that
the hardware does not have and leave the power reading `off` for good."""


@dataclass(frozen=True)
class Power:
    """What one `<p…>` line says: which track, and whether it reads on.

    `track` is empty on the line that names none, which the station sends
    only when every track is on or none is. The digit is `1` only for a track
    that is fully on — one that is powered but watching a rising current, and
    one that has tripped, both print `0`. The diagnostic lines tell those two
    apart (`Diagnostic`, ADR-0016).
    """

    track: str
    on: bool


@dataclass(frozen=True)
class Turnout:
    """What one `<H…>` line says: which turnout the station named, and
    whether it reads thrown.

    The station keeps turnouts of its own and this app commands none of them
    — a point is thrown with a stateless accessory packet, and the position
    the station answers with is one it faked (control ADR-0022). So this is
    never read back as an observation and `device/point` stays empty. It is
    read because a **script** may be keyed on it: a throw from JMRI or a
    hand-held throttle reaches a railroad's own commands only this way, after
    the station has acted (ADR-0013 d.3).

    The id is the station's own turnout number, which is what its table is
    keyed by and not the accessory number a `point` is commanded with.
    """

    point: str
    thrown: bool


@dataclass(frozen=True)
class Lock:
    """Whether the station says its emergency-stop lock is on: `<!PAUSED>`
    and `<!RESUMED>`, which it broadcasts on the lock changing and on being
    asked. This is the observation `stopped` is published from — never the
    fact that this app sent the lock command."""

    locked: bool


TRIP = "trip"
RESTORE = "restore"
NORMAL = "normal"
ALERT = "alert"
"""The kinds of `<* TRACK X … *>` line this app reads (ADR-0016)."""

_DIAGNOSTIC = re.compile(
    rb"\* TRACK ([A-H]) "
    rb"(?:(?P<trip>POWER OVERLOAD|FAULT PIN detected)"
    rb"|(?P<restore>POWER RESTORE)|(?P<normal>NORMAL)|(?P<alert>ALERT))\b"
)
"""The station's words, from `MotorDriver.cpp` at fork tag
`v5.6.4-rails49.1`. The rails49 fork owns them (ADR-0016, consequences)."""


_STASH = str(STASH_ID).encode()
"""The one stash entry this app reads, as the station writes it. The number is
`commands`' because it is this app's to choose; the rest of the station's
stash is EXRAIL's and other clients' (ADR-0021 d.1)."""


@dataclass(frozen=True)
class Stash:
    """What one `<jM 32000 …>` line says: whether the entry this app set is
    still there.

    A stash is held in the station's RAM and is empty after every boot
    (`Stash.cpp`), so `held` is false for a station that has restarted since
    the entry was set (ADR-0021 d.4). The value the station answers with is a
    locomotive id and names nothing here: anything that is not `0` is the
    mark.
    """

    held: bool


@dataclass(frozen=True)
class Diagnostic:
    """What one `<* TRACK X … *>` line says about district X: it tripped,
    the station is retrying it, it is back to normal, or its current is
    rising (ADR-0016 d.3, d.4)."""

    track: str
    kind: str


def messages(buffered: bytes, arrived: bytes) -> tuple[bytes, list[bytes]]:
    """Fold `arrived` into `buffered`: what is still partial, and the
    messages that completed, delimiters included and in the order they
    closed.

    Bytes outside a message are dropped — before a `<` there is nothing for
    them to belong to, and after a `>` the same — and a `<` inside a message
    starts it over, what came before never having been one.
    """
    partial = buffered
    whole: list[bytes] = []
    for byte in arrived:
        if byte == START:
            partial = b"<"
        elif not partial:
            continue
        elif byte == END:
            whole.append(partial + b">")
            partial = b""
        else:
            partial += bytes((byte,))
            if len(partial) > MAX_MESSAGE:
                partial = b""
    return partial, whole


def reply(
    message: bytes,
) -> Power | Lock | Turnout | Diagnostic | Stash | None:
    """The fact one whole message states, or None where it states none of
    those this app reads."""
    body = message[1:-1]
    if body.startswith(b"jM "):
        return _stash(body[3:])
    if body.startswith(b"*"):
        return _diagnostic(body)
    if body == b"!PAUSED":
        return Lock(locked=True)
    if body == b"!RESUMED":
        return Lock(locked=False)
    if body.startswith(b"H "):
        return _turnout(body[2:])
    if not body.startswith((b"p0", b"p1")):
        return None
    named = body[2:].strip().decode(errors="replace")
    if named == "":
        return Power(track="", on=body[1:2] == b"1")
    if len(named) == 1 and named in TRACKS:
        return Power(track=named, on=body[1:2] == b"1")
    return None


def _stash(named: bytes) -> Stash | None:
    """A `<jM id loco>` line read, or None where it is no such line or names
    another entry.

    An id and a value: the station answers one entry per line, and the longer
    forms it prints for `<JM>` with no id name more or fewer fields. An id
    that is not this app's is another client's entry and no fact of ours.
    """
    fields = named.split()
    if len(fields) != 2 or fields[0] != _STASH or not fields[1].isdigit():
        return None
    return Stash(held=fields[1] != b"0")


def _turnout(named: bytes) -> Turnout | None:
    """A `<H id state>` line read, or None where it is no such line.

    Two fields and a digit: `1` is thrown, the polarity a `point` is
    commanded with. The station's longer forms — a turnout's description, the
    `<H>` list it sends when asked — carry more fields or a word where the
    digit goes, and this app reads neither: a line it does not recognise is
    the ordinary case here (control ADR-0050).
    """
    fields = named.split()
    if len(fields) != 2 or fields[1] not in (b"0", b"1"):
        return None
    point = fields[0].decode(errors="replace")
    return Turnout(point=point, thrown=fields[1] == b"1")


def _diagnostic(body: bytes) -> Diagnostic | None:
    """A `<* TRACK X … *>` line read, or None where it is any other
    diagnostic."""
    found = _DIAGNOSTIC.match(body)
    if found is None:
        return None
    kind = next(name for name, said in found.groupdict().items() if said)
    return Diagnostic(track=found.group(1).decode(), kind=kind)
