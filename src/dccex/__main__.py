"""`python -m dccex` — the translator as a process of its own.

Every app comes up alone (control ADR-0059, decision 5). Started against an empty
broker with nothing else running, no store answering and no command station on
the other end of the port, this connects, publishes its own two retained rows
— the railroad dark and the station unreached — and stays up, retrying the
mirror and the store on backoffs of their own; it exits on a signal, and on a
script's text changing under it (ADR-0015 d.3). Nothing here is ordered by
anything else coming up first, which is why compose carries no `depends_on`.

**A store, and no railroad on the command line.** This app reads one
document, the **script** its railroad's own station commands are written in
(ADR-0015), and which railroad that is comes off
`tc49/layout/state/railroad` rather than off a flag: the other five processes
are told which railroad they run, and this one follows the row because the
station it holds is the same station whichever railroad is loaded on it. So
the flags are where the broker is, where the store is, where the mirror is,
and the one value that is this deployment's rather than the railroad's:

- `--station <host:port>`, where the `dccex-usb` mirror serves the command
  station (rails49/dccex). Not the USB device: this app is one client of
  that port beside JMRI and the hand-held throttles.
- `--store <url>`, where the store serves the documents, which is the one
  route this app reads: `GET /scripts/<railroad>` (rails49/control#586). A
  store that is not answering is a railroad this app carries out OFF, STOP
  and speeds for and refuses power ON, saying why on its link row, and it
  keeps asking (ADR-0015 d.4).
- `--id`, the name its link row is keyed by (control#368, decision 7),
  defaulting to the package's. A value and not a contract: it appears in no
  drawing, no configuration and no list of ours, and it is a key only because
  one railroad may have several participants and the second's `up` would
  otherwise erase the first's `down`.

Neither the drain period nor the poll nor the backoff is a flag — nothing
outside this process has an opinion about how often it takes what the broker's
network thread left waiting, and what the station is asked and how often a
lost link is retried are the translator's own (translator.py).

**The id names the broker's client too**, `tc49-<id>`, where the other apps
name themselves after the package. This is the one app a railroad may run
twice — two stations, two translators, decision 7 — and two clients sharing
one client id take turns disconnecting each other on the broker for as long as
both are up.

**A railroad loaded under it rebuilds nothing here.** The other five apps
follow `tc49/layout/state/railroad` and rebuild on the railroad it names
(control ADR-0060); this one owns no row keyed by a railroad — the link it
has and the supply it reports are the command station's, and the station is
still the same station. What the row does decide is which railroad's script
is asked for, and a script whose text differs from the running one ends this
process rather than being loaded in place (ADR-0015 d.3).

The startup order is `lib/startup.py`'s. The broker first, then `DccEx` on it,
the constructor stating this app's two opening rows — `device/link/<id>: down`
and a dark `device/track` carrying why. Then **the row that names the
railroad**, waited for by name because there is one of it, and the script
asked for once on this thread: a store that has not answered leaves this app
with no handlers, which is a state it comes up in and says on its link row
rather than one it waits out (ADR-0015 d.4). **No rows of a previous process
to adopt**, and none of this app's own to read back: the two it owns are
stated by the constructor. Last the *desired* picture, which is `layout`'s to
write and the broker's to retain, waited for **before the link is opened** so
that the whole of it is held when the first connection is handed it — and
after the script, so that what a connect replays goes out through the
handlers that are going to run (control#333, control ADR-0054).

Then the loop: `DccEx.run()` keeping the link, `DccEx.following()` asking the
store for the script, and a drain beside them.

**asyncio owns this process.** `DccEx._send` writes to an
`asyncio.StreamWriter` from inside a bus subscriber, so whichever thread
drains the bus is the thread that writes to the station. With the loop owning
the process every subscriber runs on the loop thread and that write is already
where it belongs; the MQTT client's callback only appends to a queue on its
own network thread, and the drain here is what hands those frames to the loop
(lib/mqtt.py). A daemon thread under a synchronous owner would mean
marshalling a cross-thread write that does not exist today.

The railroad is stood down before the process ends, on the signal, on the
stop, and on a new script: zero to every locomotive this app has commanded
and then the track off, because the station goes on running whatever it was
last told and an exit over a rolling locomotive leaves it rolling. It comes
**before** the link is let go — cancelling `DccEx.run` closes the writer, and
zeros sent after that have nowhere to go. A new script takes effect from power
off at the next ON for exactly this reason: the exit that loads it stands the
railroad down like any other (ADR-0015 d.3).

`DccEx` is handed a `Bus` and nothing else in the package changes: which
binding it got is this file's business, and a desired value that cannot be
read is dropped exactly as it was in one process (control#289, BUS.md rule 4)
— under MQTT whoever published it is another container, and a bug there must
not take the thing that drives the railroad down with it.
"""

import asyncio
import contextlib
import signal
import sys
import threading
from collections.abc import Callable

from tc49.lib.loading import RAILROAD
from tc49.lib.mqtt import MqttBus, address
from tc49.lib.startup import (
    PERIOD_S,
    RETAINED_S,
    command_line,
    connected,
    retained,
)

from dccex.store import Scripts
from dccex.translator import (
    FIRST_BACKOFF_S,
    ID,
    MAX_BACKOFF_S,
    SCRIPT_S,
    DccEx,
)

CLIENT_PREFIX = "tc49-"
"""What this app calls itself to the broker, in front of its id, so the log
names a translator rather than a random string and two of them on one railroad
are two clients. Nothing in the contract reads it: a topic has one writing
role and no payload says who published (BUS.md, rule 4)."""

STATION_EXAMPLE = "host.docker.internal:2560"
"""What a station address looks like, for the help and for a refusal. The
`dccex-usb` mirror serves the command station on 2560 and is a stack of its
own on the box (rails49/dccex), so what a box with a station plugged into it
names is a host and not a service beside this one."""


def to_stderr(line: str) -> None:
    """The log: what is being waited for, and what came up. `lib` says its own
    piece under its own prefix (`mqtt:`), and the link to the station is said
    on the bus rather than here — `device/link` is where a participant that
    cannot reach its hardware reports it (control ADR-0050)."""
    print(f"dccex: {line}", file=sys.stderr, flush=True)


def serve(
    bus: MqttBus,
    station: tuple[str, int],
    stop: threading.Event,
    scripts: Scripts | None = None,
    id: str = ID,
    period_s: float = PERIOD_S,
    retained_s: float = RETAINED_S,
    script_s: float = SCRIPT_S,
    first_backoff_s: float = FIRST_BACKOFF_S,
    max_backoff_s: float = MAX_BACKOFF_S,
    log: Callable[[str], None] = to_stderr,
) -> None:
    """The app, and the asyncio loop it runs in.

    `stop` is how a caller that is not a signal ends the loop, which is the
    suite. The deployment sets it never: a signal raises where the process
    happens to be — in the loop, or in the wait above it — and `main` lets
    that out.

    The two backoffs and the script's cadence are the translator's own and are
    here for the suite, which has a station appear on a port seconds after the
    app went looking for it, and a script applied while it watches, and no
    reason to wait out a deployed retry to see either.

    It comes back where the loop ended: on the stop, or on a script whose text
    has changed, which is a restart and is said on the way out.
    """
    if not connected(bus, stop, log):
        return
    host, port = station
    app = DccEx(
        bus,
        host,
        port,
        id=id,
        scripts=scripts,
        script_s=script_s,
        first_backoff_s=first_backoff_s,
        max_backoff_s=max_backoff_s,
    )
    _railroad(bus, stop, retained_s)
    app.asks()
    log(f"railroad '{app.railroad}'")
    _retained(bus, stop, retained_s)
    log(f"up as '{id}' on {host}:{port}, draining every {period_s}s")
    asyncio.run(_driving(app, bus, stop, period_s))
    if app.changed:
        log("the script changed: the railroad is down and this process is ending")


def _railroad(bus: MqttBus, stop: threading.Event, timeout_s: float) -> None:
    """Wait for the row that names the railroad, and deliver it, before the
    script it decides is asked for.

    Waited for **by name**, which `lib/startup.py` can do here where the
    desired picture below leaves it nothing to name: there is one railroad row
    and this comes back the instant it lands. A broker holding none is a
    railroad nobody has chosen, which is an ordinary state of a box — this app
    comes up with no script, says so, and asks again when the row names one
    (control ADR-0060, control#564).
    """
    retained(bus, RAILROAD, stop, timeout_s)
    bus.drain()


def _retained(bus: MqttBus, stop: threading.Event, timeout_s: float) -> None:
    """Give the broker its moment to hand over the desired rows it holds, and
    deliver them, before anything opens a link they could go out over.

    The window is waited out **whole**, for the reason `lib/startup.py` gives
    a wait with nothing to name: what is being waited for is a row per address
    `layout` has written to, and this app holds no list of which. A second on
    the way up, once, against a locomotive commanded ahead of the power it
    needs.

    Delivered here on this thread, which is the one thread there is until
    `asyncio.run` starts: `DccEx` remembers a desired value and acts on it
    only where a writer is open, so what arrives now is held whole and applied
    — the power excepted — by the first connection.

    One drain and not a loop of them, because a drain delivers what is waiting
    when it starts and the window is what the waiting was for.
    """
    stop.wait(timeout_s)
    bus.drain()


async def _driving(
    app: DccEx, bus: MqttBus, stop: threading.Event, period_s: float
) -> None:
    """The link, the script and the drain, on the one loop, until the process
    ends.

    Ctrl-C arrives here as a cancellation, `asyncio.run` cancelling the task
    it is waiting on, so the stand-down is in a `finally` and the interrupt
    goes on out to `main`. It is the same `finally` the stop event reaches,
    and the same one a new script reaches: a railroad left driving is left
    driving however the process was ended.

    `following` coming back is the third way out. It ends this loop rather
    than raising, because a new script is an ordinary thing to happen to a
    running railroad and not a fault (ADR-0015 d.3); what a fault in it does
    is come out of the `await` below, where nothing swallows it.
    """
    link = asyncio.create_task(app.run())
    watching = asyncio.create_task(app.following())
    try:
        while not stop.is_set() and not watching.done():
            bus.drain()
            await asyncio.sleep(period_s)
    finally:
        await app.shutdown()
        for task in (link, watching):
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task


def main() -> None:
    parser = command_line(
        prog="python -m dccex",
        description="Run the dccex translator against a broker: the device"
        " vocabulary turned into a command station's own language.",
        railroad=False,
    )
    parser.add_argument(
        "--station",
        required=True,
        metavar="HOST:PORT",
        help=f"where dccex-usb serves the command station, e.g."
        f" {STATION_EXAMPLE}; retried until it answers",
    )
    parser.add_argument(
        "--id",
        default=ID,
        help=f"what this translator calls itself on its link row,"
        f" '{ID}' by default",
    )
    args = parser.parse_args()
    try:
        host, port = address(args.broker)
    except ValueError as refused:
        parser.error(str(refused))
    try:
        # The same parse as the broker's, so the subtlety in it — a bracketed
        # IPv6 host keeps its colons and loses its brackets (control#335) —
        # lives in one place. The refusal is written here instead, because
        # what a person mistyped was a station and `lib` would tell them
        # about a broker.
        station = address(args.station)
    except ValueError:
        parser.error(
            f"'{args.station}' is not a station address — write it"
            f" <host>:<port>, e.g. {STATION_EXAMPLE}"
        )
    # A signal is what ends this app, and SIGTERM is the one a container is
    # stopped with: given SIGINT's own handler it raises where the process
    # stands, so a wait for a broker that never comes up ends on it too, and
    # the railroad is stood down on the way out either way.
    signal.signal(signal.SIGTERM, signal.default_int_handler)
    to_stderr(
        f"broker {host}:{port}, station {station[0]}:{station[1]},"
        f" store {args.store}"
    )
    bus = MqttBus(host, port, client_id=f"{CLIENT_PREFIX}{args.id}")
    try:
        with contextlib.suppress(KeyboardInterrupt):
            serve(bus, station, threading.Event(), Scripts(args.store), args.id)
    finally:
        bus.close()


if __name__ == "__main__":
    main()
