"""dccex: the translator between the device vocabulary and the command station.

The first of the thin apps that hang under `layout` (control ADR-0043). Above
it the bus carries the **device vocabulary** — what each device should do, and
what each is observed to do — and below it is one TCP connection to
`dccex-usb`, which owns the command station's serial device and serves it on
port 2560 so that JMRI and hand-held throttles share the same command station.
That mirror is the other app in this repository (`src/dccex_usb`) and this one
is a client of its port beside the others; the USB device is never opened
here.

**The boundary this app exists to hold.** Every other component is oblivious
to what powers the layout, and nothing above the layout interface expects
this command station or any other — they are one family of devices among
many. The `<…>` syntax is this app's private business: it appears on no bus
topic, in no other package and in no normative document, and `docs/dccex/`
is the only page in the repository that writes it down. A different command
station gets a different translator, or reaches the system through JMRI, and
nothing else moves.

*Subscribes* `tc49/layout/state/wanted/#`. *Publishes*
`tc49/layout/state/device/track` and `tc49/layout/state/device/link/<id>`,
where the id is the one this app is started with — the package's name where
it is given no other, a value and not a contract (control ADR-0059).

**It acts on an address only if it recognises it**, and there is no ownership
table anywhere: every point and signal address it hears, and every traction
and function address, an address naming no system (control ADR-0059). What this
station has no packet for — a turnout numbered outside the accessory range,
say — falls away where the packet is built. An address nothing answers to does
no harm, as a packet nobody picks up does.

**On connect it applies the retained desired state, power excepted.** The
desired values are the whole picture, so there is no handshake and no session
state to agree: whatever `layout` last wanted is waiting on those topics, and
applying it is the whole of coming up. The power is left out of it — after a
station or a translator restart the rails stay as the station reports them and
come back when a person presses ON (ADR-0013 d.6) — and every other value
replays through its handler.

**It runs one railroad's script.** `--store` is where `control`'s store
serves the documents; the railroad is the one named on
`tc49/layout/state/railroad`, and that railroad's script is fetched from the
store and loaded at start (ADR-0015 d.2). A **handler** in it keyed on a
desired value runs in place of the command this app would have sent, and one
keyed on something the station reported runs after the fact. That is where
this railroad's `<…>` that the bus has no word for is written: the mode each
track is set to, the current each may draw, a track reversed when a turnout
throws (ADR-0013).

**A script that does not load leaves the railroad dark.** No script at all is
a railroad with the defaults, which is what this app sent before there were
scripts. A script that raises on load, or a store that has not answered yet,
is no handlers: OFF, STOP and speeds are carried out, power ON is refused, the
link row says why, and it keeps asking (ADR-0015 d.4). Once a script is
loaded a fetch that fails changes nothing.

**A new script text exits the process.** The script for the current railroad
is fetched again every few seconds and compared with the one running; a text
that differs stands the railroad down and ends the process, which compose
restarts (ADR-0015 d.3). Nothing is reloaded in place.

Two rules are not a row of the mapping table:

**The stop is the one-shot, and no row of this app's holds it.** `stopped`
tells every decoder to stand with the track still live and holds nothing
afterwards, so any throttle on the shared port may drive away from it. That
is the operator's call to make — they are the one holding the layout.
`device/track` is `on` and `off` (control ADR-0063): the observed supply goes back to
`on` as soon as the broadcast is out, because the rails are live under a stop
and there is nothing else the supply could truthfully read. The stop is not
lost for going unobserved — `layout` holds the one it commanded and publishes
`state/power: stopped` above this app until a person clears it. A station's
emergency-stop *lock* would hold it in the hardware instead, which is the
better answer where a station has one, and nothing has to be asked before
using it: each translator implements `stopped` as well as its own hardware
allows and never by removing power (control ADR-0063, decision 3). One product's
firmware-branch command is dialect this app absorbs, not a word the bus
learns (control ADR-0058, control#463, control#464).

**An overload is polled for.** A district that trips is not broadcast on TCP
— the station cuts it and says so on its USB diagnostics only — so this app
asks for the status on a cadence of its own, and `device/track` telling the
truth does not depend on a person noticing.

**A clean exit stands the railroad down**, `shutdown()`: zero to every
locomotive this app has commanded, then the track off. The process ending is
not by itself an instruction to the railroad — the station goes on running
whatever it was last told — and a session that exits over a rolling
locomotive leaves it rolling, which is not recoverable the way switching the
power back on is. Whoever constructs this app calls it before letting the
loop go (`__main__.py`).

**No `device/point` is ever published.** This railroad's turnouts have no
feedback and the station's answer to a throw is one it faked (control ADR-0022), so
the row stays empty: a faked observation is worse than silence (control ADR-0050).

**`device/link`** is `up` while the station is answering, `down` otherwise,
with `detail` carrying what a person would want to read. It is the station
answering and not the socket being open: the poll goes on asking for as long
as the link lasts, and ten intervals of silence lower the row where the
connection underneath is still there — a station switched off behind a mirror
that holds its clients, a pulled cable, a wedged one. An answer afterwards
raises it again, and nothing is torn down for it (control ADR-0066). That is where
the physical link becomes visible at runtime, which is where verifying it
belongs — not in a gate that would need a powered layout to pass. The same
words go on `device/track` as its `reason` while the station is unreachable,
so a person reading why the railroad is dark reads it off the supply itself
rather than off a second row (control ADR-0059).

The framing and the mapping are pure and live in `replies` and `commands`;
what is here is the connection and the state that a connection is made of.
"""

import asyncio
import contextlib
import logging
import time
from collections.abc import Awaitable, Callable
from typing import NamedTuple

from tc49.lib.bus import Bus, Payload
from tc49.lib.inventory import OFF, ON, STOPPED, device_topic, split_device
from tc49.lib.loading import RAILROAD
from tc49.lib.payload import (
    commanded_power,
    desired_aspect,
    desired_function,
    desired_position,
    desired_speed,
)

from dccex import commands, replies, script
from dccex.store import Scripts, Unanswered

_log = logging.getLogger(__name__)

ID = "dccex"
"""What this app calls itself on its link row where it is started with no
other name: the package's, because a name has to come from somewhere. A
value and not a contract — the id is whatever the publisher calls itself, it
appears in no drawing, no configuration and no list of ours, and nothing but
`layout` reads the row it keys (control ADR-0059)."""

HOST = "mirror"
PORT = 2560
"""Where the mirror serves the command station where this app is given no
other: the service beside this one on the box, on the port `dccex-usb` listens
on (`compose.box.yaml`)."""

WANTED = "tc49/layout/state/wanted/#"

WANTED_TRACTION = "tc49/layout/state/wanted/traction"
WANTED_FUNCTION = "tc49/layout/state/wanted/function"
WANTED_POINT = "tc49/layout/state/wanted/point"
WANTED_SIGNAL = "tc49/layout/state/wanted/signal"
WANTED_TRACK = "tc49/layout/state/wanted/track"

SCRIPT_ROW = {
    WANTED_TRACK: script.ROW_POWER,
    WANTED_POINT: script.ROW_POINT,
    WANTED_SIGNAL: script.ROW_SIGNAL,
    WANTED_TRACTION: script.ROW_TRACTION,
    WANTED_FUNCTION: script.ROW_FUNCTION,
}
"""What a script calls each row this app acts on. The bus carries the
railroad's power on `wanted/track` and a script is written about `power`: the
topic is the contract's word and the other is the one a person writes in a
document (BUS.md, *Device vocabulary*, CONTEXT.md **script**)."""

WANTED_BY_ROW = {row: topic for topic, row in SCRIPT_ROW.items()}

REPORTED_EVENT = {
    script.ROW_POWER: script.REPORTED_POWER,
    script.ROW_POINT: script.REPORTED_POINT,
}
"""The two things the station reports that a handler can be keyed on, and the
event each is. Power and turnouts; others are added when a script needs one
(ADR-0013 d.3)."""

DEVICE_TRACK = "tc49/layout/state/device/track"
DEVICE_LINK = "tc49/layout/state/device/link"

UP = "up"
DOWN = "down"

POLL_S = 1.0
"""How often the station is asked what it is doing, which bounds how long a
tripped district reads as live and how long a fresh connection reads as
`down`. A second is far inside what a person recovering from either would
notice, and the two questions are two short lines on a port that carries the
whole railroad's traffic."""

MISSED_POLLS = 10
"""How many polls may go unanswered before the link is lowered, counted off
`poll_s` rather than held as a second number so the two cannot drift apart.

This is the number with teeth: `layout` folds any `down` to
`state/power: off`, so one that fires early stops the railroad in the middle
of a session. It can afford to be generous, because the mirror closes its
clients for a device it knows is away and that ends the session through the
path that already exists — what is left for this to catch is a station that
is powered, enumerated and mute, and ten seconds is well outside anything a
healthy station does with a status query under load (control ADR-0066)."""

SCRIPT_S = 5.0
"""How often the store is asked for the current railroad's script. It bounds
how long a script applied on the page waits before the railroad stands down
for it, and how long a store that was not up at start leaves the railroad
without handlers. A few seconds is one small request on a face that is
answering layouts and rosters besides (ADR-0015 d.3)."""

FIRST_BACKOFF_S = 0.5
MAX_BACKOFF_S = 8.0

READ_SIZE = 4096


Connect = Callable[[], Awaitable[tuple[asyncio.StreamReader, asyncio.StreamWriter]]]
"""How a connection is made, injected so a test drives a socket pair rather
than hardware: nothing in the gate may need a command station."""

Now = Callable[[], float]
"""Where the silence is measured against, injected for the same reason: a
suite that had to wait out ten real poll intervals would be asserting the
machine's scheduler as much as this app."""


class Asked(NamedTuple):
    """What one ask of the store came back with: the script's text, `None`
    where the railroad has none, or why the store did not answer.

    A value rather than an exception, because the ask is made on a thread of
    its own and what is done about it is done on the loop thread
    (`DccEx.following`)."""

    text: str | None
    away: str | None


class Wanted(NamedTuple):
    """One desired value as this app holds it: the row and the address, which
    are the topic's, the payload that arrived on it, and the command it
    becomes.

    The command is built where the value arrives and kept, so it is built once
    per value rather than again on every firing; a value that becomes no
    command is not held at all (`DccEx._on_wanted`). The payload is kept
    beside it because what a handler reads is the value and never the bytes
    (`Event.desired`)."""

    row: str
    address: str
    payload: Payload
    default: bytes


class Event:
    """What a handler is handed: the event that fired, and the four things a
    handler may do about it.

    A handler sends raw `<…>`, reads the desired picture and the last
    reports, and **publishes nothing** on the bus — there is no method here
    for it, which is the whole of that rule (ADR-0013 d.4). What it is given
    is the two pictures as this app holds them, so a handler sets everything
    it depends on from the desired values each time it runs rather than from
    what an earlier handler sent (d.5).

    Built per firing and not held: `default()` sends once whichever handler
    of the event asks for it, and `sent_default` is what the translator reads
    to decide whether a handler that raised has left its command unsent
    (d.8).
    """

    def __init__(
        self,
        row: str,
        address: str | None,
        *,
        sends: Callable[[bytes], None],
        default: bytes | None,
        wanted: dict[str, "Wanted"],
        reported: dict[tuple[str, str], str],
    ) -> None:
        self.row = row
        """The row this event is on, in the script's words."""
        self.address = address
        """The address on it, and None where the row has none."""
        self.sent_default = False
        """Whether this app's own command for the value has gone out."""
        self._sends = sends
        self._default = default
        self._wanted = wanted
        self._reported = reported

    def default(self) -> None:
        """Send this app's own command for the value that fired.

        A handler runs **in place of** that command, so this is how a script
        keeps it and adds to it — the power-on that then sets its districts'
        limits (ADR-0013 d.2). Once per firing whoever asks: two handlers on
        one value both calling it is one command, not two. It sends nothing
        for something the station reported: a report has already happened
        and replaces nothing (d.3).
        """
        if self.sent_default or self._default is None:
            return
        self.sent_default = True
        self._sends(self._default)

    def send(self, text: str) -> None:
        """One raw message to the station, as typed.

        This is the point of a script: what a railroad needs of its station
        that the bus has no word for is written in the station's own
        language, and this app grows no vocabulary for it (ADR-0013).
        """
        self._sends(text.strip().encode())

    def desired(self, row: str, address: str | None = None) -> object | None:
        """What the bus last wanted of one device, or None where it has not
        said. The rows are the script's: `power`, `point`, `signal`,
        `traction`, `function`.

        The value and not the frame: a position, an aspect, a speed, a
        function's bit, or the word the power is wanted in. A row this app
        does not act on raises, so a typo in a script is a handler that says
        so in the log rather than one that reads None for ever.
        """
        if row not in script.DESIRED_ROWS:
            raise ValueError(
                f"'{row}' is no desired value: the rows are"
                f" {', '.join(script.DESIRED_ROWS)}"
            )
        held = self._wanted.get(_topic(row, address))
        return None if held is None else _value(held)

    def reported(self, row: str, address: str | None = None) -> str | None:
        """What the station last said about one thing, or None where it has
        said nothing this session. `power`, by the track it named, and
        `point`, by the id it named.

        The station's own words — `on` and `off` for a track, `closed` and
        `thrown` for a turnout — and the picture goes with the link: a
        reading nobody can take is not the last one taken.

        The track a `<p…>` line names, which is the empty address where it
        names none; that line is sent only when every track is on or none is.
        A turnout's id is the station's own, which is the one a throw from
        JMRI or a throttle is reported under and not the accessory number a
        `point` is commanded by.
        """
        if row not in REPORTED_EVENT:
            raise ValueError(
                f"'{row}' is nothing the station reports: the rows are"
                f" {', '.join(REPORTED_EVENT)}"
            )
        return self._reported.get((row, address or ""))


class DccEx:
    """The translator, on the bus and on one connection to `dccex-usb`.

    `run()` is the whole of the connection: it connects, applies the retained
    desired state, reads what the station says until the link goes, and
    reconnects with backoff, publishing `device/link: down` for the whole
    outage. The bus half needs none of it — a desired value that arrives
    while the link is down is remembered and applied on the next connect,
    which is the same thing that happens to the retained value at startup.

    `following()` is the script: the store asked again on a cadence of its
    own, and a coroutine that comes back where the text has changed and the
    process is to end (ADR-0015 d.3). `asks()` is one of those asks, made by
    whoever assembles this app before the link is opened, and `load()` takes
    a script's text directly.
    """

    def __init__(
        self,
        bus: Bus,
        host: str = HOST,
        port: int = PORT,
        *,
        id: str = ID,
        connect: Connect | None = None,
        now: Now = time.monotonic,
        scripts: Scripts | None = None,
        poll_s: float = POLL_S,
        script_s: float = SCRIPT_S,
        first_backoff_s: float = FIRST_BACKOFF_S,
        max_backoff_s: float = MAX_BACKOFF_S,
    ) -> None:
        self._bus = bus
        self._id = id
        self._where = f"{host}:{port}"
        self._connect: Connect = connect or (
            lambda: asyncio.open_connection(host, port)
        )
        self._now = now
        self._scripts = scripts
        self._script_s = script_s
        self._poll_s = poll_s
        self._first_backoff_s = first_backoff_s
        self._max_backoff_s = max_backoff_s
        self._writer: asyncio.StreamWriter | None = None
        # The desired picture, one entry per topic in the order each topic
        # was first heard: what a connection is handed.
        self._wanted: dict[str, Wanted] = {}
        # Every locomotive this app has commanded, in that order — what a
        # clean exit sends zero to. The link does not outlive it: the station
        # keeps a slot per locomotive and resumes it, so one commanded before
        # an outage is one that resumes after it.
        self._commanded: dict[str, None] = {}
        # What the station says about itself, and forgotten with the link:
        # an outage is not an observation, and what cannot be read may not be
        # called good (control#181).
        self._answered = False
        # When the station last said anything, and `None` where it has said
        # nothing this app has heard. What the poll measures its silence
        # against: the link is the station answering, so a station that has
        # stopped answering is one this app has to stop calling reachable,
        # however open the socket underneath stays (control ADR-0066).
        self._last_heard: float | None = None
        self._tracks: dict[str, bool] = {}
        self._every: bool | None = None
        self._paused = False
        # The last report the station made of each thing a handler can be
        # keyed on, by row and address. What a report event fires on a change
        # of, and what `Event.reported` reads. Forgotten with the link, like
        # everything else the station told us.
        self._reported: dict[tuple[str, str], str] = {}
        # The railroad this broker runs, as the row names it, and the script
        # it is running. `None` where no script is loaded, which is a
        # railroad this app carries out OFF, STOP and speeds for and refuses
        # power ON (ADR-0015 d.4); `_text` is what the running script was
        # loaded from and `_refused` the text that would not load.
        self._railroad = ""
        self._script: script.Script | None = None
        self._text: str | None = None
        self._refused: str | None = None
        self._trouble: str | None = None
        self._changed = False
        # What was last said on each of the two rows this app writes. The
        # supply carries why it is off where this app cannot reach the
        # station, so what is held is the pair rather than the word.
        self._track: tuple[str, str | None] | None = None
        self._link: tuple[bool, str] | None = None
        # The station's own half of the link row, before the script's trouble
        # is said beside it.
        self._reached = (False, f"not connected to {self._where}")
        # The railroad is dark and the station unreached, which is what is
        # true before anything is connected, and a client joining now is
        # served that rather than an absence (control ADR-0032).
        self._said_link()
        self._publish_track()
        bus.subscribe(WANTED, self._on_wanted)
        bus.subscribe(RAILROAD, self._on_railroad)

    # -- the bus: what the hardware should do --------------------------------

    def _on_wanted(self, topic: str, payload: Payload) -> None:
        """One desired value, remembered and — if the link is up — applied.

        The row and the address come from the **topic**, which is where a
        device topic states them; the payload repeats the address so a trace
        line reads on its own, and a repetition is not a second authority.

        A value that cannot be turned into a message is not remembered
        either: it is dropped whole, so a connect does not replay something
        that sent nothing when it arrived. Dropped silently and to the trace,
        the frame being on it by virtue of having been published — this app
        answers nothing, so a refusal would have nowhere to go (control ADR-0034).
        """
        split = split_device(topic)
        if split is None:
            return
        row, address = split
        if not self._recognises(row, address):
            return
        default = _built(row, address, payload)
        if default is None:
            return
        wanted = Wanted(row, address, payload, default)
        self._wanted[topic] = wanted
        if self._writer is not None:
            self._act(wanted)

    def _recognises(self, row: str, address: str) -> bool:
        """Whether this app answers for the address, which is the whole of
        what it decides for itself. There is no ownership table: a translator
        recognises its own addresses and everything else is somebody's or
        nobody's, and an address nobody answers to does no harm.

        An address names no system (control ADR-0059), so a point or signal address
        is **every** one this app hears: it is the string the drawing carries
        and the hardware answers to, and an address this station has no packet
        for falls away where the packet is built, not here. Traction is one
        level and a function two — the decoder and the function number — which
        is the shape of the row rather than anyone's claim on it.
        """
        levels = address.split("/")
        if row == WANTED_TRACK:
            return True
        if row == WANTED_TRACTION:
            return len(levels) == 1 and bool(address)
        if row == WANTED_FUNCTION:
            return len(levels) == 2 and all(levels)
        if row in (WANTED_POINT, WANTED_SIGNAL):
            return bool(address)
        return False

    def _act(self, wanted: Wanted) -> None:
        """What one desired value asks of the station: the script's handlers
        for it, or this app's own command where the script has none.

        A handler runs **in place of** the command (ADR-0013 d.2) and every
        handler keyed on the event runs, in the order the script registered
        them. The power is the row a handler runs on every value of — `on`,
        `off` and the stop alike, which is what `t.desired("power")` is read
        for; there is no transition kept here, and two ONs run the handler
        twice (d.7).

        **Power ON with no script is refused.** Track modes and current
        limits are the script's, so a railroad whose script did not load is
        one whose rails may not be made live: the OFF, the stop and the
        speeds are carried out and the link row says why (ADR-0015 d.4).

        A locomotive is remembered as commanded whether a handler or this app
        sent the speed: what a clean exit sends zero to is every locomotive
        this app has driven, however the bytes were composed.
        """
        row = SCRIPT_ROW[wanted.row]
        power = commanded_power(wanted.payload) if row == script.ROW_POWER else None
        if power == ON and self._script is None:
            _log.warning("power ON refused: %s", self._trouble or "no script")
            return
        if wanted.row == WANTED_TRACTION:
            self._commanded[wanted.address] = None
        # The power's topic has no address under it, which is the row having
        # one thing in it rather than an address that is the empty string.
        address = wanted.address or None
        handlers = self._handlers(row, address)
        if not handlers:
            self._send(wanted.default)
            return
        self._ran(handlers, self._firing(row, address, wanted.default))

    def _handlers(self, row: str, address: str | None) -> list[script.Handler]:
        """The script's handlers for one event, and none at all where no
        script is loaded."""
        loaded = self._script
        return [] if loaded is None else loaded.handlers(row, address)

    def _firing(self, row: str, address: str | None, default: bytes | None) -> Event:
        """One event, as a handler is handed it."""
        return Event(
            row,
            address,
            sends=self._send,
            default=default,
            wanted=self._wanted,
            reported=self._reported,
        )

    def _ran(self, handlers: list[script.Handler], firing: Event) -> None:
        """Run the handlers of one event, and send the default behind a
        handler that raised.

        A handler is a person's Python on the far end of a document, so
        anything at all comes out of it. What is done about that is the rule
        broken hardware gets: it is logged, and the command the handler was
        standing in for is sent unless the handler had already asked for it
        (ADR-0013 d.8). A handler that raised has done something to the
        station either way — the bytes it sent before it raised are on the
        wire — so what is left is to not leave the value unapplied as well.
        """
        raised = False
        for handler in handlers:
            try:
                handler(firing)
            except Exception:  # noqa: BLE001 - a handler is a person's Python
                raised = True
                _log.exception(
                    "the handler %s raised on %s",
                    getattr(handler, "__name__", handler),
                    firing.row,
                )
        if raised:
            firing.default()

    def _applied(self) -> list[Wanted]:
        """The desired picture in the order a fresh connection is handed it:
        every row but the power, in the order the topics were first heard.

        **The power is not replayed.** After a station or a translator
        restart the rails stay as the station reports them and come back when
        a person presses ON, which is the one desired value a connect does
        not carry out (ADR-0013 d.6). `layout` holds power as desired and
        reads it off the supply, as it does for any report of off.

        Every other value goes out through its handler, which is what makes a
        connect the same path as a value arriving live.
        """
        return [w for w in self._wanted.values() if w.row != WANTED_TRACK]

    # -- the script: the railroad's own commands -----------------------------

    @property
    def railroad(self) -> str:
        """The railroad the bus names, whose script this app runs. Empty
        where none is named, which is an ordinary state of a box that has
        chosen none (control ADR-0060)."""
        return self._railroad

    @property
    def changed(self) -> bool:
        """Whether the script's text has changed under this process, which is
        what ends it."""
        return self._changed

    def _on_railroad(self, topic: str, payload: Payload) -> None:
        """The railroad named on the row. Nothing is rebuilt on it — the link
        this app has and the supply it reports are the command station's, and
        the station is the same station — it is the script that is that
        railroad's and is asked for again (ADR-0015 d.3)."""
        name = payload.get("name")
        if isinstance(name, str):
            self._railroad = name

    def load(self, text: str | None) -> None:
        """Run `text` and hold the handlers it registered.

        The **text** and not a path or a URL, which is what lets the tests
        load the sample directly (ADR-0015 d.2). `None` is a railroad with no
        script: an empty script, and every desired value sends what this app
        sends with no script at all.

        A text that raises leaves this app with no handlers and the link row
        saying so, and the text is remembered as refused so that the same one
        is not run again on every ask. The person who has to fix it reads the
        log and the row (control ADR-0050).
        """
        if text is None:
            self._script, self._text, self._refused = script.Script(), None, None
            self._trouble = None
        else:
            try:
                loaded = script.load(text)
            except Exception as broken:  # noqa: BLE001 - so is loading one
                _log.exception("the script for '%s' does not load", self._railroad)
                self._script, self._refused = None, text
                self._trouble = (
                    f"the script for '{self._railroad}' does not load: {broken}"
                )
            else:
                self._script, self._text, self._refused = loaded, text, None
                self._trouble = None
        self._said_link()
        self._publish_track()

    def asks(self) -> bool:
        """Ask the store for the current railroad's script, once, on the
        caller's own thread. Says whether the process has to end.

        The first ask is made before the link is opened, so that a connect
        replays the desired picture through the handlers it is going to run
        (`__main__`). After that it is `following` that asks.

        Nothing is waited for and nothing is retried here: a store that is
        not up yet is an ordinary state, and what this app does about it is
        run with no handlers and ask again (ADR-0015 d.4).
        """
        scripts = self._scripts
        if scripts is None:
            return False
        return self._took(_asked(scripts, self._railroad))

    async def following(self) -> None:
        """Ask again every `script_s`, until the text has changed.

        Returning is this app saying the process should end: a new text takes
        effect through a restart and never in place, so the railroad is stood
        down and compose brings it up on the new script (ADR-0015 d.3).

        **The request goes on a thread of its own and nothing else does.** A
        store that has accepted a connection and gone quiet would otherwise
        stop the poll and the drain for as long as it takes to time out, and
        the loop that drives the railroad waits for nothing but the railroad.
        What the answer is made of happens back here, on the loop, because the
        bus is the loop thread's — one binding of it is single-threaded by
        contract (`tc49.lib.bus`) and this app's own rows are published from
        whichever thread drains it.

        Where there is no store there is nothing to ask and this never comes
        back: what was loaded is what runs.
        """
        while True:
            await asyncio.sleep(self._script_s)
            scripts = self._scripts
            if scripts is None:
                continue
            said = await asyncio.to_thread(_asked, scripts, self._railroad)
            if self._took(said):
                return

    def _took(self, said: "Asked") -> bool:
        """What the store said, taken.

        A store that did not answer is said on the link row while there is no
        script, and changes nothing once one is loaded: the script goes on
        running and the row goes on saying what the station is doing
        (ADR-0015 d.4).
        """
        if said.away is not None:
            self._without(said.away)
            return False
        return self._read(said.text)

    def _read(self, text: str | None) -> bool:
        """What the store answered, taken: a first script loaded, a text that
        has changed reported as the end of this process, and anything else
        nothing at all.

        A railroad change that gives the same text, or no script both times,
        changes nothing — the comparison is the text and never the name
        (ADR-0015 d.3).
        """
        if self._script is not None:
            if text == self._text:
                return False
            self._changed = True
            return True
        if text is not None and text == self._refused:
            return False
        self.load(text)
        return False

    def _without(self, why: str) -> None:
        """A store that did not answer, said on the link row — while there is
        no script. Once one is loaded a fetch that fails changes nothing: the
        script goes on running and the row goes on saying what the station is
        doing (ADR-0015 d.4)."""
        if self._script is not None:
            return
        trouble = f"no script: {why}"
        if trouble == self._trouble:
            return
        _log.warning("%s", trouble)
        self._trouble = trouble
        self._said_link()
        self._publish_track()

    # -- the link: what the hardware reports ---------------------------------

    async def run(self) -> None:
        """Keep the link to the station, until cancelled."""
        backoff = self._first_backoff_s
        while True:
            try:
                reader, writer = await self._connect()
            except OSError as away:
                self._publish_link(False, f"connecting to {self._where}: {away}")
                self._publish_track()
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, self._max_backoff_s)
                continue
            spoke = await self._session(reader, writer)
            # Opening is not proof the station is there. A session that ended
            # without a word keeps the backoff it was reached with, so a port
            # that accepts and drops is not a hot loop.
            if spoke:
                backoff = self._first_backoff_s
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, self._max_backoff_s)

    async def shutdown(self) -> None:
        """Stand the railroad down: zero to every locomotive this app has
        commanded, then the track off.

        The zeros come first and are the same zeros a release sends, for the
        same reason: the station keeps a speed per locomotive and resumes it,
        so a slot left holding one is a train that rolls again the moment
        somebody powers the rails. Cutting the supply over a held speed only
        postpones the motion.

        Sent on whatever link is open and nothing at all where none is — a
        railroad this app cannot reach is one it was not driving — and
        awaited out, because the next thing to happen is the process ending
        and a buffer nobody flushed is a command nobody sent.
        """
        for addr in self._commanded:
            self._send(commands.traction(addr, 0.0))
        self._send(commands.track(OFF))
        writer = self._writer
        if writer is not None:
            with contextlib.suppress(OSError):
                await writer.drain()

    async def _session(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> bool:
        """One connection, from the desired state going out to the link
        going down.

        Says whether the station was answering when it ended, which is what
        the backoff is reset on. A session the poll timed out reads as one
        that heard nothing — the silence is what `_forget` already recorded —
        so a station that wedged and then dropped is retried on the same
        lengthening interval as a port that accepts and drops.
        """
        self._writer = writer
        for wanted in self._applied():
            self._act(wanted)
        polling = asyncio.create_task(self._poll())
        try:
            await self._listen(reader)
        finally:
            polling.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await polling
            self._writer = None
            spoke = self._answered
            self._forget()
            writer.close()
            with contextlib.suppress(OSError):
                await writer.wait_closed()
            self._publish_link(False, f"the link to {self._where} closed")
            self._publish_track()
        return spoke

    async def _listen(self, reader: asyncio.StreamReader) -> None:
        """Read the station until it stops talking to us."""
        buffered = b""
        try:
            while True:
                arrived = await reader.read(READ_SIZE)
                if not arrived:
                    return
                buffered, whole = replies.messages(buffered, arrived)
                for message in whole:
                    self._heard(message)
        except (ConnectionError, OSError):
            return

    async def _poll(self) -> None:
        """Ask the station what it is doing, for as long as the link lasts.

        The first question waits out the interval rather than going with the
        desired state: a connect applies that and nothing else, and a status
        the station volunteers on being commanded arrives sooner than a poll
        would anyway.

        One question and not two. A poll runs for as long as the link does, so
        anything sent here that a station acts on rather than answers is acted
        on for as long as the railroad is up — which is what a lock query was,
        on a station whose `!` opcode takes no suffix: an emergency stop every
        second, and a train that moved a few centimetres and stood
        (control#463).
        `<s>` asks and changes nothing, which is the property a polled command
        has to have.
        """
        while True:
            await asyncio.sleep(self._poll_s)
            self._lower_if_silent()
            self._send(commands.STATUS)

    def _lower_if_silent(self) -> None:
        """Lower the link where the station has gone quiet on us, which the
        poll is the natural place to notice: it is already the thing asking.

        A socket that stays open is not the station answering. `dccex-usb`
        holds its clients through an outage it thinks is brief and drops
        their bytes, and a station that is powered, enumerated and mute
        leaves the mirror nothing to report at all — so the far end noticing
        that ten questions went unanswered is the only thing that catches a
        wedged station (control ADR-0066).

        What goes is everything the station told us, the same `_forget` a
        link that closed runs: a reading nobody can take is not the last one
        taken. The session itself stays — this is an observation being published,
        not the transport being torn down — so an answer arriving afterwards
        raises the link by the one path that raises it, a message read.

        A station that has not answered *yet* is left alone: that link is
        already `down` and already says why.
        """
        last = self._last_heard
        if last is None:
            return
        silent = self._now() - last
        if silent < MISSED_POLLS * self._poll_s:
            return
        self._forget()
        self._publish_link(
            False,
            f"the station at {self._where} has not answered for {silent:g}s",
        )
        self._publish_track()

    def _heard(self, message: bytes) -> None:
        """One whole message from the station: the link is up, and the two
        facts this app reads may have moved. Everything else on the port is
        another client's conversation and is passed over.

        The link is the station having answered and never the parse: a
        message this app reads nothing out of — the banner among them, which
        this app reads no field off — raises it just the same.
        """
        told = replies.reply(message)
        if isinstance(told, replies.Power):
            if told.track:
                self._tracks[told.track] = told.on
            else:
                # The line naming no track is sent only when every one of
                # them is on, or none is, so it says the same of each.
                self._every = told.on
                self._tracks = {name: told.on for name in self._tracks}
        elif isinstance(told, replies.Lock):
            # A lock this app never sets and never lifts. It is read all the
            # same, because a station that has one and is put under it by
            # somebody's hand-held throttle is a railroad no train may move
            # over, and that is a fact about the supply whoever caused it.
            self._paused = told.locked
        self._answered = True
        self._last_heard = self._now()
        self._publish_link(True, f"connected to {self._where}")
        self._publish_track()
        self._reports(told)

    def _reports(
        self, told: replies.Power | replies.Lock | replies.Turnout | None
    ) -> None:
        """The script's handlers for what the station just reported, run after
        the fact.

        A report replaces nothing — the station has already done it — and
        fires on a **change**: the poll makes the station restate every
        track's power once a second, and a handler on every one of those
        answers would be a handler on the clock (ADR-0013 d.3).

        Power is the word the bus uses for it, and a turnout's position is
        the two words a point is commanded with, so a script compares against
        what it wrote rather than against a digit.
        """
        if isinstance(told, replies.Power):
            self._reported_by(script.ROW_POWER, told.track, ON if told.on else OFF)
        elif isinstance(told, replies.Turnout):
            self._reported_by(
                script.ROW_POINT,
                told.point,
                commands.THROWN if told.thrown else commands.CLOSED,
            )

    def _reported_by(self, row: str, address: str, value: str) -> None:
        """One report, held and — where it differs from the last one heard —
        handed to the handlers keyed on it."""
        if self._reported.get((row, address)) == value:
            return
        self._reported[(row, address)] = value
        event = REPORTED_EVENT[row]
        handlers = self._handlers(event, address)
        if handlers:
            self._ran(handlers, self._firing(event, address, None))

    def _forget(self) -> None:
        """Let go of everything the station told us, the link having gone.

        What cannot be read is not what was last read: a district that
        tripped while we were away, or a stop somebody cleared by hand, would
        otherwise stand as an observation nobody made. The reports a script
        reads go with them, so the first thing the station says on the next
        link is a change and a handler keyed on it runs — the station on the
        far end may be one that has just come up."""
        self._answered = False
        self._last_heard = None
        self._tracks.clear()
        self._every = None
        self._paused = False
        self._reported.clear()

    def _send(self, message: bytes) -> None:
        """One whole message to the station, or nothing at all because the
        link is down. Dropped and never queued: a command is honoured now or
        ignored, and the desired value is held for the next connect, which is
        where a picture is restored rather than a backlog replayed."""
        writer = self._writer
        if writer is not None:
            writer.write(message)

    # -- the bus: what the hardware is observed to do ------------------------

    def _observed(self) -> str:
        """The power this app can say it sees, folded from what the station
        has reported.

        `on` only where every track it named is on: the digit is `1` for a
        track that is fully on and `0` both for one that has tripped and for
        one that is powered but watching a rising current, so anything else
        is `off`. A station that has said nothing reads `off` too, which is
        the direction a state topic must fail in (control#181) — a supply
        that cannot be read is not one a train may move over.

        `stopped` is the station's own report of a lock, which this app does
        not command and so never reads back from a stop of its own: the
        one-shot it sends leaves nothing standing to observe, so a `stopped`
        this app was asked for shows here as `on` the moment the broadcast is
        out (control#463). What is left is a station that has a lock and has
        been put under it by another throttle, which is a supply no train may
        move over whoever caused it. It reaches here only over live rails, an
        emergency stop being every locomotive told to stand with the track
        still on.
        """
        if not self._answered:
            return OFF
        if self._tracks:
            powered = all(self._tracks.values())
        else:
            powered = self._every is True
        if not powered:
            return OFF
        return STOPPED if self._paused else ON

    def _unreachable(self) -> str | None:
        """Why the supply reads `off` where this app cannot reach the
        station, or None where the station is answering and the reading is
        the station's own.

        It is the link row's own words, said again on the supply, so a person
        reading why the railroad is dark needs no second row (control ADR-0059). A
        district that has tripped gets none: the station reported that and
        said nothing about why, and a reason this app invented would be worse
        than none (control ADR-0050).
        """
        if self._link is None or self._link[0]:
            return None
        return self._link[1]

    def _publish_track(self) -> None:
        """The supply, on a last-value topic and only when the fold moves —
        the word or the reason beside it: a state topic republishing what it
        already holds is noise on the trace and news to nobody. Published
        after the link, so the reason a frame carries is the current one."""
        said = (self._observed(), self._unreachable())
        if said == self._track:
            return
        self._track = said
        observed, why = said
        frame: Payload = {"power": observed}
        if why is not None:
            frame["reason"] = why
        self._bus.publish(DEVICE_TRACK, frame)

    def _publish_link(self, up: bool, detail: str) -> None:
        """What the station is doing, which is what the link row is: said
        again whenever it moves."""
        self._reached = (up, detail)
        self._said_link()

    def _said_link(self) -> None:
        """This app's link to the station, keyed by the id it was started
        with, with the script's trouble said beside it. Republished when the
        detail changes as well as the word: while an outage lasts the row
        goes on saying so, and *why* is what a person reads
        (control ADR-0050).

        The word is the **station** answering and nothing else, because that
        is what a link is (control ADR-0066): a script that will not load is
        not the station being away. It rides on the detail instead, which is
        where a person reading why the railroad will not come on reads it —
        in `control`'s UI and in this app's log, and not on a page of this
        repository's (ADR-0015, consequences).
        """
        up, detail = self._reached
        if self._trouble is not None:
            detail = f"{detail}; {self._trouble}"
        said = (up, detail)
        if said == self._link:
            return
        self._link = said
        frame: Payload = {"id": self._id, "link": UP if up else DOWN, "detail": detail}
        self._bus.publish(device_topic(DEVICE_LINK, self._id), frame)


def _asked(scripts: Scripts, railroad: str) -> Asked:
    """One ask of the store, and the only thing here that blocks.

    A module function and not a method, because what it may touch is what it
    is handed: it runs on a thread of its own and the app's state is the loop
    thread's (`DccEx.following`).

    A railroad nobody has named is nothing to ask about rather than a route
    with an empty name: a box that has chosen no railroad is an ordinary
    state of one (control ADR-0060, control#564).
    """
    if not railroad:
        return Asked(None, f"no railroad is named on {RAILROAD}")
    try:
        return Asked(scripts.text(railroad), None)
    except Unanswered as away:
        return Asked(None, str(away))


def _topic(row: str, address: str | None) -> str:
    """Where one desired value sits, from the script's word for its row and
    the address on it. A row with one thing in it — the railroad's power —
    has no address and no level under the topic."""
    topic = WANTED_BY_ROW[row]
    return f"{topic}/{address}" if address else topic


def _value(wanted: Wanted) -> object | None:
    """The value one desired frame states, as a script reads it: a position,
    an aspect, a speed, a function's bit, or the word the power is wanted in.

    The value and not the frame, and read with the library's own readers, so
    a handler compares against the same words the contract carries and never
    against a key of a payload (BUS.md, rule 4)."""
    row, payload = wanted.row, wanted.payload
    if row == WANTED_TRACTION:
        return desired_speed(payload)
    if row == WANTED_FUNCTION:
        return desired_function(payload)
    if row == WANTED_POINT:
        return desired_position(payload)
    if row == WANTED_SIGNAL:
        return desired_aspect(payload)
    return commanded_power(payload)


def _built(row: str, address: str, payload: Payload) -> bytes | None:
    """The message one desired value becomes, or None where it becomes none
    — a payload that cannot be read, or a value this hardware has no packet
    for. The track row answers the power alone: what a railroad wants around
    a power-on is its script's and not this value's.

    The row, the address and the payload rather than a `Wanted`, because a
    `Wanted` holds what this returns.
    """
    if row == WANTED_TRACTION:
        speed = desired_speed(payload)
        return None if speed is None else commands.traction(address, speed)
    if row == WANTED_FUNCTION:
        addr, number = address.split("/")
        value = desired_function(payload)
        return None if value is None else commands.function(addr, number, value)
    if row == WANTED_POINT:
        position = desired_position(payload)
        return None if position is None else commands.point(address, position)
    if row == WANTED_SIGNAL:
        aspect = desired_aspect(payload)
        return None if aspect is None else commands.signal(address, aspect)
    power = commanded_power(payload)
    return None if power is None else commands.track(power)
