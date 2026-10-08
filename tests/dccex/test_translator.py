"""The translator over one connection, with a socket pair standing in for the
command station.

The connection is injected, so the test holds the station's end of every
attempt the app makes and nothing here needs hardware: the gate is green on a
machine with nothing plugged in, which is the acceptance criterion the rest
of them sit under (#289). What is asserted is the seam — the bytes that go
out, and the two rows that come back on the bus.

The suite has no asyncio plugin, so each test is a coroutine handed to
`asyncio.run`, and what a test waits on is the station's end of the wire: a
message arriving there is the app having acted.
"""

import asyncio
import contextlib
import logging
import socket
import time
from collections.abc import AsyncGenerator, Callable

import pytest
from tc49.lib.bus import InProcessBus, Payload
from tc49.lib.clock import Clock
from tc49.lib.loading import RAILROAD

from dccex import sample
from dccex.store import Scripts
from dccex.translator import DccEx
from tests.stores import Store

TIMEOUT_S = 5.0
QUIET_S = 0.05

# Far longer than any test runs, so a poll never lands in the middle of what
# a test is asserting. The tests about polling set their own.
NEVER_S = 3600.0

# A poll period short enough that many of them land inside `QUIET_S`, used
# where what a test is timing is the silence and not the cadence: the clock
# the silence is measured against is the test's own, so how long ten
# intervals take to elapse is not this machine's scheduler's to decide.
FAST_POLL_S = 0.005

TRACK = "tc49/layout/state/wanted/track"
TRACTION = "tc49/layout/state/wanted/traction"
POINT = "tc49/layout/state/wanted/point"
SIGNAL = "tc49/layout/state/wanted/signal"
FUNCTION = "tc49/layout/state/wanted/function"

DEVICE_TRACK = "tc49/layout/state/device/track"
DEVICE_LINK = "tc49/layout/state/device/link/dccex"
DEVICE_POINT = "tc49/layout/state/device/point"


class Station:
    """The command station's end of one connection."""

    def __init__(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        self._reader = reader
        self._writer = writer

    async def heard(self, count: int = 1) -> list[bytes]:
        """The next `count` whole messages the app sent, in order."""
        return [
            await asyncio.wait_for(self._reader.readuntil(b">"), TIMEOUT_S)
            for _ in range(count)
        ]

    async def heard_nothing_more(self) -> None:
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(self._reader.read(1), QUIET_S)

    def says(self, *messages: bytes) -> None:
        for message in messages:
            self._writer.write(message)

    def hangs_up(self) -> None:
        self._writer.close()


class Port:
    """Where the app connects: one socket pair per attempt, the station's end
    of each kept so the test can drive it."""

    def __init__(self) -> None:
        self.attempts: list[Station] = []
        self._opened = asyncio.Event()

    async def connect(self) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        app_side, station_side = socket.socketpair()
        reader, writer = await asyncio.open_connection(sock=station_side)
        end = await asyncio.open_connection(sock=app_side)
        # Announced with nothing left to await, so the app runs on from here
        # to the read it waits at before the test wakes: what a test does
        # next is publish, and the link has to be up by then.
        self.attempts.append(Station(reader, writer))
        self._opened.set()
        return end

    async def opened(self, count: int = 1) -> Station:
        """The station's end of the `count`-th attempt, waiting for it."""
        while len(self.attempts) < count:
            self._opened.clear()
            if len(self.attempts) >= count:
                break
            await asyncio.wait_for(self._opened.wait(), TIMEOUT_S)
        return self.attempts[count - 1]


class Tap:
    """Everything published, in delivery order: the trace, as a test reads it."""

    def __init__(self, bus: InProcessBus) -> None:
        self.seen: list[tuple[str, Payload]] = []
        bus.subscribe("tc49/#", self._on_anything)

    def _on_anything(self, topic: str, payload: Payload) -> None:
        self.seen.append((topic, payload))

    def values(self, topic: str) -> list[Payload]:
        return [payload for seen, payload in self.seen if seen == topic]

    def topics(self) -> set[str]:
        return {topic for topic, _ in self.seen}


@contextlib.asynccontextmanager
async def running(
    bus: InProcessBus,
    port: Port,
    poll_s: float = NEVER_S,
    backoff_s: float = 0.005,
    text: str = "",
    no_script: bool = False,
    now: Callable[[], float] = time.monotonic,
) -> AsyncGenerator[DccEx]:
    """The app, constructed on the bus and keeping its link, until the test
    is done with it.

    The script is loaded from `text` and never off a store: loading takes the
    text, which is what lets a test hand over three lines (ADR-0015 d.2). The
    empty text is a railroad whose store has no script for it — an empty
    script, and every desired value sending what this app sends with none.
    `no_script` is the other state, a railroad whose script this app has not
    got at all, which is the one where power ON is refused (d.4).
    """
    app = DccEx(
        bus,
        connect=port.connect,
        now=now,
        poll_s=poll_s,
        first_backoff_s=backoff_s,
        max_backoff_s=backoff_s * 4,
    )
    if not no_script:
        app.load(text)
    bus.drain()
    keeping = asyncio.create_task(app.run())
    try:
        yield app
    finally:
        keeping.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await keeping


def bus_and_tap() -> tuple[InProcessBus, Tap]:
    bus = InProcessBus(Clock())
    return bus, Tap(bus)


def wanted(bus: InProcessBus, topic: str, address: str, payload: Payload) -> None:
    """One desired value, on the topic its address puts it on."""
    bus.publish(f"{topic}/{address}" if address else topic, payload)


# -- what a connection is handed -----------------------------------------


def test_the_retained_desired_state_is_applied_on_connect() -> None:
    asyncio.run(_retained_desired_state_is_applied_on_connect())


async def _retained_desired_state_is_applied_on_connect() -> None:
    """Three retained values waiting, and connecting sends exactly those
    three: the desired values are the whole picture, so there is no handshake
    and no session state to agree first."""
    bus, _ = bus_and_tap()
    wanted(bus, TRACTION, "460", {"addr": "460", "speed": 0.5})
    wanted(bus, POINT, "5", {"addr": "5", "position": "thrown"})
    wanted(bus, SIGNAL, "40", {"addr": "40", "aspect": "clear"})
    port = Port()
    async with running(bus, port):
        station = await port.opened()
        assert await station.heard(3) == [b"<t 460 63 1>", b"<a 2 0 1>", b"<A 40 2>"]
        await station.heard_nothing_more()


def test_the_power_is_not_in_what_a_connection_is_handed() -> None:
    asyncio.run(_power_is_not_in_what_a_connection_is_handed())


async def _power_is_not_in_what_a_connection_is_handed() -> None:
    """Every desired value but the power, which is the one a connect does
    not carry out: the rails stay as the station reports them and come back
    when a person presses ON (ADR-0013 d.6)."""
    bus, _ = bus_and_tap()
    wanted(bus, POINT, "5", {"addr": "5", "position": "closed"})
    wanted(bus, TRACK, "", {"power": "on"})
    port = Port()
    async with running(bus, port):
        station = await port.opened()
        assert await station.heard(1) == [b"<a 2 0 0>"]
        await station.heard_nothing_more()


def test_a_value_that_arrives_while_the_link_is_down_waits_for_it() -> None:
    asyncio.run(_value_that_arrives_while_the_link_is_down_waits_for_it())


async def _value_that_arrives_while_the_link_is_down_waits_for_it() -> None:
    """A command is honoured now or ignored, and the desired value is what
    survives: it is applied on the next connect, the way the retained value
    is at startup."""
    bus, _ = bus_and_tap()
    port = Port()
    app = DccEx(bus, connect=port.connect, poll_s=NEVER_S)
    bus.drain()
    wanted(bus, TRACTION, "3", {"addr": "3", "speed": -1.0})
    bus.drain()
    keeping = asyncio.create_task(app.run())
    try:
        station = await port.opened()
        assert await station.heard(1) == [b"<t 3 126 0>"]
    finally:
        keeping.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await keeping


# -- what this app answers for -------------------------------------------


def test_every_point_address_is_acted_on() -> None:
    asyncio.run(_every_point_address_is_acted_on())


async def _every_point_address_is_acted_on() -> None:
    """An address names no system (control ADR-0059): it is the string the drawing
    carries and the hardware answers to, so `5` is a turnout this station
    throws and there is no level in front of it to look at."""
    bus, _ = bus_and_tap()
    wanted(bus, POINT, "5", {"addr": "5", "position": "thrown"})
    wanted(bus, SIGNAL, "40", {"addr": "40", "aspect": "clear"})
    port = Port()
    async with running(bus, port):
        station = await port.opened()
        assert await station.heard(2) == [b"<a 2 0 1>", b"<A 40 2>"]
        await station.heard_nothing_more()


def test_an_address_this_station_has_no_packet_for_sends_nothing() -> None:
    asyncio.run(_address_this_station_has_no_packet_for_sends_nothing())


async def _address_this_station_has_no_packet_for_sends_nothing() -> None:
    """No ownership table: the app acts on every address it hears and the
    packet is where one it cannot express falls away, so an address nothing
    answers to does no harm, as a packet nobody picks up does."""
    bus, _ = bus_and_tap()
    wanted(bus, POINT, "LT3", {"addr": "LT3", "position": "thrown"})
    port = Port()
    async with running(bus, port):
        station = await port.opened()
        await station.heard_nothing_more()


def test_a_traction_address_is_bare_and_is_this_apps() -> None:
    asyncio.run(_traction_address_is_bare_and_is_this_apps())


async def _traction_address_is_bare_and_is_this_apps() -> None:
    """A decoder answers to the number it was programmed with whoever sends
    the packet, so every bare address is acted on — and one of two levels is
    a function's, the decoder and the function number, and not a traction
    address at all."""
    bus, _ = bus_and_tap()
    wanted(bus, TRACTION, "3/2", {"addr": "3/2", "speed": 1.0})
    wanted(bus, FUNCTION, "3/2", {"addr": "3", "function": "2", "value": True})
    port = Port()
    async with running(bus, port):
        station = await port.opened()
        assert await station.heard(1) == [b"<F 3 2 1>"]
        await station.heard_nothing_more()


def test_a_frame_that_cannot_be_read_is_dropped() -> None:
    asyncio.run(_frame_that_cannot_be_read_is_dropped())


async def _frame_that_cannot_be_read_is_dropped() -> None:
    """This app answers nothing, so a frame it cannot read is dropped and
    raises nothing — and is not remembered either, so a connect does not
    replay something that sent nothing when it arrived."""
    bus, _ = bus_and_tap()
    port = Port()
    async with running(bus, port):
        station = await port.opened()
        wanted(bus, TRACTION, "3", {"addr": "3", "speed": "fast"})
        wanted(bus, TRACTION, "4", {"addr": "4", "speed": True})
        wanted(bus, POINT, "5", {"addr": "5"})
        wanted(bus, TRACK, "", {"power": "maybe"})
        bus.drain()
        await station.heard_nothing_more()


# -- the stop, and clearing it -------------------------------------------


def test_a_stop_is_one_message_and_an_on_after_it_is_another() -> None:
    asyncio.run(_stop_is_one_message_and_an_on_after_it_is_another())


async def _stop_is_one_message_and_an_on_after_it_is_another() -> None:
    """The one-shot holds nothing, so there is nothing to undo: the stop is
    the broadcast alone and the `on` behind it is the track-on alone. No
    zeros and no release — every locomotive is already standing at its slot's
    stop, and what moves one again is the next thing that commands it (#463).
    """
    bus, _ = bus_and_tap()
    port = Port()
    async with running(bus, port):
        station = await port.opened()
        wanted(bus, TRACTION, "3", {"addr": "3", "speed": 0.5})
        wanted(bus, TRACTION, "7", {"addr": "7", "speed": -0.25})
        bus.drain()
        assert await station.heard(2) == [b"<t 3 63 1>", b"<t 7 32 0>"]

        wanted(bus, TRACK, "", {"power": "stopped"})
        bus.drain()
        assert await station.heard(1) == [b"<!>"]

        wanted(bus, TRACK, "", {"power": "on"})
        bus.drain()
        assert await station.heard(1) == [b"<1>"]
        await station.heard_nothing_more()


def test_an_on_does_not_lift_a_lock_the_station_reports() -> None:
    asyncio.run(_an_on_does_not_lift_a_lock_the_station_reports())


async def _an_on_does_not_lift_a_lock_the_station_reports() -> None:
    """A station with a lock of its own, put under it by somebody's hand-held
    throttle: this app commands no lock and so lifts none. The stop is theirs
    to clear, and the `on` is the track-on and nothing more."""
    bus, _ = bus_and_tap()
    port = Port()
    async with running(bus, port):
        station = await port.opened()
        wanted(bus, TRACTION, "3", {"addr": "3", "speed": 0.5})
        bus.drain()
        assert await station.heard(1) == [b"<t 3 63 1>"]

        station.says(b"<!PAUSED>")
        await asyncio.sleep(QUIET_S)

        wanted(bus, TRACK, "", {"power": "on"})
        bus.drain()
        assert await station.heard(1) == [b"<1>"]
        await station.heard_nothing_more()


# -- the script -----------------------------------------------------------

LIMITS = """\
@on("power")
def power(t):
    t.default()
    for district, ma in {"A": 3000, "B": 1500}.items():
        t.send(f"<JG {district} {ma}>")
"""

SENT = [b"<JG A 3000>", b"<JG B 1500>"]

REVERSER = """\
@on("point", "12")
def point_12(t):
    t.default()
    t.send("<= D MAIN_INV>" if t.desired("point", "12") == "thrown" else "<= D MAIN>")
"""

INSTEAD = """\
@on("signal", "40")
def signal_40(t):
    t.send("<A 5 2>")
"""

UNSAID = """\
@on("signal", "40")
def signal_40(t):
    t.send(f"<= D {t.desired('point', '9')}>")
"""

RAISES = """\
@on("point", "5")
def point_5(t):
    raise RuntimeError("the reversing loop is not wired yet")
"""

RAISES_AFTER = """\
@on("point", "5")
def point_5(t):
    t.default()
    raise RuntimeError("the reversing loop is not wired yet")
"""

WATCHES = """\
@on("reported_power")
def rails(t):
    t.send("<A 9 2>" if t.reported("power") == "on" else "<A 9 0>")


@on("reported_point", "12")
def thrown_by_hand(t):
    t.send("<= D MAIN_INV>" if t.reported("point", "12") == "thrown" else "<= D MAIN>")
"""


def test_a_handler_sends_the_railroads_own_commands_after_the_default() -> None:
    asyncio.run(_handler_sends_the_railroads_own_commands_after_the_default())


async def _handler_sends_the_railroads_own_commands_after_the_default() -> None:
    """The power-on a railroad really wants: the track-on command this app
    would have sent, and then the district limits nothing on the bus has a
    word for. `default()` sends the first, where the handler asked for it."""
    bus, _ = bus_and_tap()
    port = Port()
    async with running(bus, port, text=LIMITS):
        station = await port.opened()
        wanted(bus, TRACK, "", {"power": "on"})
        bus.drain()
        assert await station.heard(3) == [b"<1>"] + SENT
        await station.heard_nothing_more()


def test_every_on_runs_the_power_handler() -> None:
    asyncio.run(_every_on_runs_the_power_handler())


async def _every_on_runs_the_power_handler() -> None:
    """Not a transition: two ONs over rails that are already live run the
    handler twice, because what a handler sets is a level and it sets
    everything it depends on each time (ADR-0013 d.5, d.7)."""
    bus, _ = bus_and_tap()
    port = Port()
    async with running(bus, port, text=LIMITS):
        station = await port.opened()
        wanted(bus, TRACK, "", {"power": "on"})
        bus.drain()
        assert await station.heard(3) == [b"<1>"] + SENT

        wanted(bus, TRACK, "", {"power": "on"})
        bus.drain()
        assert await station.heard(3) == [b"<1>"] + SENT
        await station.heard_nothing_more()


def test_the_power_handler_runs_on_the_off_and_on_the_stop_as_well() -> None:
    asyncio.run(_power_handler_runs_on_the_off_and_on_the_stop_as_well())


async def _power_handler_runs_on_the_off_and_on_the_stop_as_well() -> None:
    """The event is the desired value being applied, whichever word it
    carries; there is no transition kept here. A handler that wants only the
    ON reads `t.desired("power")` and says so itself."""
    bus, _ = bus_and_tap()
    port = Port()
    async with running(bus, port, text=LIMITS):
        station = await port.opened()
        wanted(bus, TRACK, "", {"power": "off"})
        bus.drain()
        assert await station.heard(3) == [b"<0>"] + SENT

        wanted(bus, TRACK, "", {"power": "stopped"})
        bus.drain()
        assert await station.heard(3) == [b"<!>"] + SENT


def test_a_handler_replaces_the_command_it_stands_in_for() -> None:
    asyncio.run(_handler_replaces_the_command_it_stands_in_for())


async def _handler_replaces_the_command_it_stands_in_for() -> None:
    """A handler that does not call `default()` is the whole of what the
    value sends: this railroad's signal 40 is a head at address 5, and the
    aspect this app would have sent never goes out (ADR-0013 d.2)."""
    bus, _ = bus_and_tap()
    port = Port()
    async with running(bus, port, text=INSTEAD):
        station = await port.opened()
        wanted(bus, SIGNAL, "40", {"addr": "40", "aspect": "clear"})
        bus.drain()
        assert await station.heard(1) == [b"<A 5 2>"]
        await station.heard_nothing_more()


def test_a_handler_reads_the_desired_picture() -> None:
    asyncio.run(_handler_reads_the_desired_picture())


async def _handler_reads_the_desired_picture() -> None:
    """What a handler sets, it sets from the desired values and never from
    what an earlier handler sent (ADR-0013 d.5). The value that fired is in
    the picture by the time the handler runs, so a point handler reads the
    position it is being asked for."""
    bus, _ = bus_and_tap()
    port = Port()
    async with running(bus, port, text=REVERSER):
        station = await port.opened()
        wanted(bus, POINT, "12", {"addr": "12", "position": "thrown"})
        bus.drain()
        assert await station.heard(2) == [b"<a 3 3 1>", b"<= D MAIN_INV>"]

        wanted(bus, POINT, "12", {"addr": "12", "position": "closed"})
        bus.drain()
        assert await station.heard(2) == [b"<a 3 3 0>", b"<= D MAIN>"]


def test_a_desired_value_the_bus_has_not_given_reads_none() -> None:
    asyncio.run(_desired_value_the_bus_has_not_given_reads_none())


async def _desired_value_the_bus_has_not_given_reads_none() -> None:
    """A turnout nobody has thrown: the picture says so rather than standing
    in a default of its own (ADR-0013 d.4)."""
    bus, _ = bus_and_tap()
    port = Port()
    async with running(bus, port, text=UNSAID):
        station = await port.opened()
        wanted(bus, SIGNAL, "40", {"addr": "40", "aspect": "clear"})
        bus.drain()
        assert await station.heard(1) == [b"<= D None>"]


def test_with_no_script_the_byte_stream_is_what_it_was() -> None:
    asyncio.run(_with_no_script_the_byte_stream_is_what_it_was())


async def _with_no_script_the_byte_stream_is_what_it_was() -> None:
    """A railroad with no script in the store runs the defaults, which is
    what this app sent before there were scripts (ADR-0015 d.4)."""
    bus, _ = bus_and_tap()
    port = Port()
    async with running(bus, port):
        station = await port.opened()
        wanted(bus, TRACK, "", {"power": "on"})
        wanted(bus, POINT, "5", {"addr": "5", "position": "thrown"})
        bus.drain()
        assert await station.heard(2) == [b"<1>", b"<a 2 0 1>"]
        await station.heard_nothing_more()


def test_a_handler_that_raises_is_logged_and_the_default_sent(
    caplog: pytest.LogCaptureFixture,
) -> None:
    asyncio.run(_handler_that_raises_is_logged_and_the_default_sent(caplog))


async def _handler_that_raises_is_logged_and_the_default_sent(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A handler is a person's Python and anything at all comes out of it.
    The value is applied anyway — the turnout the layout asked for is thrown
    — and whoever has to fix the script reads the log (ADR-0013 d.8)."""
    bus, _ = bus_and_tap()
    port = Port()
    with caplog.at_level(logging.ERROR):
        async with running(bus, port, text=RAISES):
            station = await port.opened()
            wanted(bus, POINT, "5", {"addr": "5", "position": "thrown"})
            bus.drain()
            assert await station.heard(1) == [b"<a 2 0 1>"]
            await station.heard_nothing_more()
    assert "point_5" in caplog.text
    assert "not wired yet" in caplog.text


def test_a_handler_that_raises_after_the_default_does_not_send_it_twice(
    caplog: pytest.LogCaptureFixture,
) -> None:
    asyncio.run(_handler_that_raises_after_the_default_does_not_send_it_twice(caplog))


async def _handler_that_raises_after_the_default_does_not_send_it_twice(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The default runs behind a raising handler **unless the handler had
    called it**: one desired value is one packet on the rails."""
    bus, _ = bus_and_tap()
    port = Port()
    with caplog.at_level(logging.ERROR):
        async with running(bus, port, text=RAISES_AFTER):
            station = await port.opened()
            wanted(bus, POINT, "5", {"addr": "5", "position": "thrown"})
            bus.drain()
            assert await station.heard(1) == [b"<a 2 0 1>"]
            await station.heard_nothing_more()
    assert "point_5" in caplog.text


def test_a_connect_replays_every_other_value_through_its_handler() -> None:
    asyncio.run(_connect_replays_every_other_value_through_its_handler())


async def _connect_replays_every_other_value_through_its_handler() -> None:
    """A connect is the same path as a value arriving live: the turnout
    replays, its handler runs, and the retained power is left alone
    (ADR-0013 d.6)."""
    bus, _ = bus_and_tap()
    wanted(bus, TRACK, "", {"power": "on"})
    wanted(bus, POINT, "12", {"addr": "12", "position": "thrown"})
    port = Port()
    async with running(bus, port, text=REVERSER):
        station = await port.opened()
        assert await station.heard(2) == [b"<a 3 3 1>", b"<= D MAIN_INV>"]
        await station.heard_nothing_more()


def test_a_report_handler_runs_after_the_fact_and_only_on_a_change() -> None:
    asyncio.run(_report_handler_runs_after_the_fact_and_only_on_a_change())


async def _report_handler_runs_after_the_fact_and_only_on_a_change() -> None:
    """The poll makes the station restate every track's power once a second,
    so a report handler that ran on every answer would be a handler on the
    clock. It fires where the value differs from the last one heard, and
    replaces nothing: there is no command of this app's to stand in for
    (ADR-0013 d.3)."""
    bus, _ = bus_and_tap()
    port = Port()
    async with running(bus, port, text=WATCHES):
        station = await port.opened()
        station.says(b"<p1>")
        assert await station.heard(1) == [b"<A 9 2>"]

        station.says(b"<p1>", b"<p1>")
        await station.heard_nothing_more()

        station.says(b"<p0>")
        assert await station.heard(1) == [b"<A 9 0>"]


def test_a_turnout_the_station_reports_is_an_event() -> None:
    asyncio.run(_turnout_the_station_reports_is_an_event())


async def _turnout_the_station_reports_is_an_event() -> None:
    """A throw from JMRI or a hand-held throttle reaches a railroad's own
    commands only this way, after the station has acted. The id is the
    station's own and the position is the word a point is commanded with."""
    bus, _ = bus_and_tap()
    port = Port()
    async with running(bus, port, text=WATCHES):
        station = await port.opened()
        station.says(b"<H 12 1>")
        assert await station.heard(1) == [b"<= D MAIN_INV>"]

        station.says(b"<H 12 1>")
        await station.heard_nothing_more()

        station.says(b"<H 12 0>")
        assert await station.heard(1) == [b"<= D MAIN>"]


def test_a_report_this_app_does_not_read_fires_nothing() -> None:
    asyncio.run(_report_this_app_does_not_read_fires_nothing())


async def _report_this_app_does_not_read_fires_nothing() -> None:
    """Most of the traffic on the port is another client's conversation, and
    power and turnouts are the two things a script can be keyed on. The
    banner, a slot's speed and a `<H>` line of another shape go unread."""
    bus, _ = bus_and_tap()
    port = Port()
    async with running(bus, port, text=WATCHES):
        station = await port.opened()
        station.says(b"<l 3 1 191 0>", b"<iDCC-EX V-5.6.4 / ESP32>", b"<H 12>")
        await station.heard_nothing_more()


def test_the_reports_a_script_reads_go_with_the_link() -> None:
    asyncio.run(_reports_a_script_reads_go_with_the_link())


async def _reports_a_script_reads_go_with_the_link() -> None:
    """A reading nobody can take is not the last one taken, so the station on
    the far end of the next link is heard afresh and the handler keyed on
    what it says runs."""
    bus, _ = bus_and_tap()
    port = Port()
    async with running(bus, port, text=WATCHES):
        first = await port.opened()
        first.says(b"<p1>")
        assert await first.heard(1) == [b"<A 9 2>"]

        first.hangs_up()
        second = await port.opened(2)
        second.says(b"<p1>")
        assert await second.heard(1) == [b"<A 9 2>"]


# -- the station as this app has not set it (ADR-0018) -------------------

SETS_UP = """\
@on("start")
def configure(t):
    t.default()
    t.send("<= D MAIN>")
"""

READY = b"<* LCD3:Ready *>"


def test_start_runs_on_connect_before_the_replay() -> None:
    asyncio.run(_start_runs_on_connect_before_the_replay())


async def _start_runs_on_connect_before_the_replay() -> None:
    """A point handler may set a district's mode, so it runs after `start`
    sets them all (ADR-0018 d.3). `start` has no default: `t.default()` in
    it sends nothing (d.4). The power is not replayed."""
    bus, _ = bus_and_tap()
    wanted(bus, TRACK, "", {"power": "on"})
    wanted(bus, POINT, "12", {"addr": "12", "position": "thrown"})
    port = Port()
    async with running(bus, port, text=SETS_UP + "\n\n" + REVERSER):
        station = await port.opened()
        assert await station.heard(3) == [
            b"<= D MAIN>",
            b"<a 3 3 1>",
            b"<= D MAIN_INV>",
        ]
        await station.heard_nothing_more()


def test_a_restart_runs_start_and_the_replay_again() -> None:
    asyncio.run(_restart_runs_start_and_the_replay_again())


async def _restart_runs_start_and_the_replay_again() -> None:
    """A reset can be shorter than the ten polls that lower the link, so the
    station's own last boot line is what says it restarted (ADR-0018 d.2).
    What follows is what a connect does (d.3)."""
    bus, _ = bus_and_tap()
    wanted(bus, TRACK, "", {"power": "on"})
    wanted(bus, POINT, "12", {"addr": "12", "position": "thrown"})
    port = Port()
    async with running(bus, port, text=SETS_UP + "\n\n" + REVERSER):
        station = await port.opened()
        await station.heard(3)

        station.says(READY)
        assert await station.heard(3) == [
            b"<= D MAIN>",
            b"<a 3 3 1>",
            b"<= D MAIN_INV>",
        ]
        await station.heard_nothing_more()


# -- the sample script ----------------------------------------------------

SAMPLE_START = [
    b"<= A MAIN>",
    b"<= B PROG>",
    b"<= C MAIN_AUTO>",
    b"<= D MAIN_AUTO>",
    b"<JG A 300>",
    b"<JG B 250>",
    b"<JG C 1500>",
    b"<JG D 1500>",
]


def test_the_sample_sets_the_tracks_up_and_power_on_is_the_default() -> None:
    asyncio.run(_sample_sets_the_tracks_up_and_power_on_is_the_default())


async def _sample_sets_the_tracks_up_and_power_on_is_the_default() -> None:
    """The sample is the interface and the documentation both, so what it
    sends is asserted as bytes: this installation's four track modes and
    four district limits at `start`, and the track-on command alone at ON
    (ADR-0018 d.6)."""
    bus, _ = bus_and_tap()
    port = Port()
    async with running(bus, port, text=sample.TEXT):
        station = await port.opened()
        assert await station.heard(8) == SAMPLE_START
        await station.heard_nothing_more()

        wanted(bus, TRACK, "", {"power": "on"})
        bus.drain()
        assert await station.heard(1) == [b"<1>"]
        await station.heard_nothing_more()


def test_the_sample_reverses_the_district_behind_point_12() -> None:
    asyncio.run(_sample_reverses_the_district_behind_point_12())


async def _sample_reverses_the_district_behind_point_12() -> None:
    """The turnout throws and the track behind it is inverted with it. A
    mode change cuts the track's power, so with the railroad's power on the
    handler turns that track back on; with it off it does not."""
    bus, _ = bus_and_tap()
    port = Port()
    async with running(bus, port, text=sample.TEXT):
        station = await port.opened()
        await station.heard(8)

        wanted(bus, POINT, "12", {"addr": "12", "position": "thrown"})
        bus.drain()
        assert await station.heard(3) == [
            b"<a 3 3 1>",
            b"<= D MAIN_AUTO>",
            b"<= D INV>",
        ]
        await station.heard_nothing_more()

        wanted(bus, TRACK, "", {"power": "on"})
        bus.drain()
        await station.heard(1)

        wanted(bus, POINT, "12", {"addr": "12", "position": "closed"})
        bus.drain()
        assert await station.heard(3) == [
            b"<a 3 3 0>",
            b"<= D MAIN_AUTO>",
            b"<1 D>",
        ]
        await station.heard_nothing_more()


# -- a railroad with no script this app could load ------------------------


def test_with_no_script_loaded_power_on_is_refused(
    caplog: pytest.LogCaptureFixture,
) -> None:
    asyncio.run(_with_no_script_loaded_power_on_is_refused(caplog))


async def _with_no_script_loaded_power_on_is_refused(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Track modes and current limits are the script's, so a railroad whose
    script this app has not got is one whose rails may not be made live. The
    OFF, the stop and the speeds are carried out — each of them is a thing a
    railroad is only made safer by (ADR-0015 d.4)."""
    bus, _ = bus_and_tap()
    port = Port()
    with caplog.at_level(logging.WARNING):
        async with running(bus, port, no_script=True):
            station = await port.opened()
            wanted(bus, TRACK, "", {"power": "on"})
            bus.drain()
            await station.heard_nothing_more()

            wanted(bus, TRACTION, "3", {"addr": "3", "speed": 0.5})
            wanted(bus, TRACK, "", {"power": "stopped"})
            wanted(bus, TRACK, "", {"power": "off"})
            bus.drain()
            assert await station.heard(3) == [b"<t 3 63 1>", b"<!>", b"<0>"]
    assert "power ON refused" in caplog.text


def test_a_script_that_does_not_load_says_why_on_the_link_row() -> None:
    """A load error shows on the link row and in this app's log, and not on a
    page of this repository's (ADR-0015, consequences). The word on the row is
    still the station's: a script that will not load is not the station being
    away."""
    bus, tap = bus_and_tap()
    app = DccEx(bus)
    app.load("1 / 0\n")
    bus.drain()
    said = tap.values(DEVICE_LINK)[-1]
    assert said["link"] == "down"
    assert "does not load" in said["detail"]
    assert "division by zero" in said["detail"]
    assert tap.values(DEVICE_TRACK)[-1]["reason"] == said["detail"]

    app.load(LIMITS)
    bus.drain()
    assert "does not load" not in tap.values(DEVICE_LINK)[-1]["detail"]


# -- asking the store -----------------------------------------------------


def asking(bus: InProcessBus, store: Store) -> DccEx:
    """The app with a store to ask and no link open: what `asks()` is under
    test on. The station is another suite's, and a script is asked for
    before a link is opened anyway."""
    app = DccEx(bus, scripts=Scripts(store.url, timeout_s=1.0))
    bus.drain()
    return app


def named(bus: InProcessBus, railroad: str) -> None:
    """The railroad this broker runs, as `layout` names it."""
    bus.publish(RAILROAD, {"name": railroad})
    bus.drain()


def test_the_railroad_the_bus_names_is_the_script_that_is_asked_for(
    store: Store,
) -> None:
    """The translator follows the railroad row for one thing: which script is
    its own (ADR-0015 d.2)."""
    store.holds("bench", LIMITS)
    store.opens()
    bus, _ = bus_and_tap()
    app = asking(bus, store)
    named(bus, "bench")

    assert app.asks() is False
    assert app.railroad == "bench"
    assert store.asked == ["bench"]


def test_a_script_that_does_not_load_says_so_again_when_the_store_is_back(
    store: Store,
) -> None:
    """A store that goes away and comes back with the same text that would
    not load: the row says the script does not load, not that the store is
    away."""
    store.holds("bench", "1 / 0\n")
    store.opens()
    bus, tap = bus_and_tap()
    app = asking(bus, store)
    named(bus, "bench")
    assert app.asks() is False

    store.closes()
    assert app.asks() is False
    bus.drain()
    assert "does not load" not in tap.values(DEVICE_LINK)[-1]["detail"]

    store.opens()
    assert app.asks() is False
    bus.drain()
    assert "does not load" in tap.values(DEVICE_LINK)[-1]["detail"]


def test_a_new_script_text_ends_the_process(store: Store) -> None:
    """A script applied on the page is a document that changed under a
    running translator. It exits, standing the railroad down as every exit
    does, and compose brings it up on the new text (ADR-0015 d.3)."""
    store.holds("bench", LIMITS)
    store.opens()
    bus, _ = bus_and_tap()
    app = asking(bus, store)
    named(bus, "bench")
    assert app.asks() is False

    store.holds("bench", INSTEAD)

    assert app.asks() is True
    assert app.changed is True


def test_a_railroad_change_that_gives_the_same_text_changes_nothing(
    store: Store,
) -> None:
    """The comparison is the text and never the name: two railroads with the
    same script leave the process running and its rows as they were."""
    store.holds("bench", LIMITS)
    store.holds("yard", LIMITS)
    store.opens()
    bus, _ = bus_and_tap()
    app = asking(bus, store)
    named(bus, "bench")
    assert app.asks() is False

    named(bus, "yard")

    assert app.asks() is False
    assert app.changed is False


def test_two_railroads_with_no_script_change_nothing(store: Store) -> None:
    """`404` both times is no change, and the defaults go on being sent."""
    store.opens()
    bus, _ = bus_and_tap()
    app = asking(bus, store)
    named(bus, "bench")
    assert app.asks() is False

    named(bus, "yard")

    assert app.asks() is False
    assert app.changed is False


def test_a_store_that_stops_answering_leaves_the_script_running(
    store: Store,
) -> None:
    """Once a script is loaded a fetch that fails changes nothing: the script
    keeps running and the link row goes on saying what the station is doing
    (ADR-0015 d.4)."""
    store.holds("bench", LIMITS)
    store.opens()
    bus, tap = bus_and_tap()
    app = asking(bus, store)
    named(bus, "bench")
    assert app.asks() is False
    bus.drain()
    said = tap.values(DEVICE_LINK)[-1]["detail"]

    store.closes()

    assert app.asks() is False
    assert app.changed is False
    bus.drain()
    assert tap.values(DEVICE_LINK)[-1]["detail"] == said


def test_a_store_that_has_not_answered_says_why_on_the_link_row(
    store: Store,
) -> None:
    """A store that is not up yet is an ordinary state of a box, and what
    this app does about it is come up with no handlers, say why, and ask
    again (ADR-0015 d.4)."""
    bus, tap = bus_and_tap()
    app = asking(bus, store)
    named(bus, "bench")

    assert app.asks() is False
    bus.drain()
    said = tap.values(DEVICE_LINK)[-1]
    assert "no script" in said["detail"]
    assert store.url in said["detail"]

    store.holds("bench", LIMITS)
    store.opens()

    assert app.asks() is False
    bus.drain()
    assert "no script" not in tap.values(DEVICE_LINK)[-1]["detail"]


def test_with_no_railroad_named_there_is_no_script_to_ask_for(
    store: Store,
) -> None:
    """A box that has chosen no railroad is an ordinary state (control
    ADR-0060, #564). The store is not asked, and the row says what is
    missing."""
    store.opens()
    bus, tap = bus_and_tap()
    app = asking(bus, store)

    assert app.asks() is False
    bus.drain()
    assert "no railroad" in tap.values(DEVICE_LINK)[-1]["detail"]
    assert store.asked == []


# -- what the hardware reports -------------------------------------------


def test_the_link_is_down_before_anything_is_connected() -> None:
    """A client joining now is served a value rather than left to read one
    out of an absence, and what is true is that nothing has been reached."""
    bus, tap = bus_and_tap()
    DccEx(bus)
    bus.drain()
    assert [value["link"] for value in tap.values(DEVICE_LINK)] == ["down"]
    assert [value["power"] for value in tap.values(DEVICE_TRACK)] == ["off"]


def test_the_link_row_is_keyed_by_the_id_the_app_is_started_with() -> None:
    """The id is whatever the publisher calls itself and appears in no
    drawing and no list of ours, so two of these on one railroad each keep
    their own row and neither erases the other (control ADR-0059). The package's name
    is the default and a value, not a contract."""
    bus, tap = bus_and_tap()
    DccEx(bus, id="shed")
    bus.drain()
    said = tap.values("tc49/layout/state/device/link/shed")
    assert [value["link"] for value in said] == ["down"]
    assert [value["id"] for value in said] == ["shed"]
    assert not tap.values(DEVICE_LINK)


def test_the_supply_says_why_it_is_off_while_the_station_is_unreachable() -> None:
    asyncio.run(_supply_says_why_it_is_off_while_the_station_is_unreachable())


async def _supply_says_why_it_is_off_while_the_station_is_unreachable() -> None:
    """The link row's own words, said again on the supply, so a person
    reading why the railroad is dark reads it off the supply itself rather
    than off a second row (control ADR-0059). The reason goes when the station
    answers: what the row says then is the station's own word."""
    bus, tap = bus_and_tap()
    port = Port()
    async with running(bus, port):
        bus.drain()
        dark = tap.values(DEVICE_TRACK)[-1]
        assert dark["power"] == "off"
        assert dark["reason"] == tap.values(DEVICE_LINK)[-1]["detail"]

        station = await port.opened()
        station.says(b"<p1>")
        await asyncio.sleep(QUIET_S)
        bus.drain()
        lit = tap.values(DEVICE_TRACK)[-1]
        assert lit["power"] == "on"
        assert "reason" not in lit


def test_a_dropped_link_is_published_and_so_is_the_reconnect() -> None:
    asyncio.run(_dropped_link_is_published_and_so_is_the_reconnect())


async def _dropped_link_is_published_and_so_is_the_reconnect() -> None:
    bus, tap = bus_and_tap()
    port = Port()
    async with running(bus, port):
        first = await port.opened()
        first.says(b"<p1>")
        await asyncio.sleep(QUIET_S)
        bus.drain()
        assert [value["link"] for value in tap.values(DEVICE_LINK)] == ["down", "up"]

        first.hangs_up()
        second = await port.opened(2)
        bus.drain()
        assert [value["link"] for value in tap.values(DEVICE_LINK)] == [
            "down",
            "up",
            "down",
        ]

        second.says(b"<p1>")
        await asyncio.sleep(QUIET_S)
        bus.drain()
        assert [value["link"] for value in tap.values(DEVICE_LINK)][-1] == "up"


def test_the_link_is_up_only_once_the_station_has_answered() -> None:
    asyncio.run(_link_is_up_only_once_the_station_has_answered())


async def _link_is_up_only_once_the_station_has_answered() -> None:
    """An open socket is not a command station. `station` accepts a client
    with the serial device unplugged, and a link nobody has answered on is
    not one a view may call good."""
    bus, tap = bus_and_tap()
    port = Port()
    async with running(bus, port):
        await port.opened()
        await asyncio.sleep(QUIET_S)
        bus.drain()
        assert [value["link"] for value in tap.values(DEVICE_LINK)] == ["down"]


def test_the_banner_raises_the_link_and_rides_on_it_no_further() -> None:
    asyncio.run(_banner_raises_the_link_and_rides_on_it_no_further())


async def _banner_raises_the_link_and_rides_on_it_no_further() -> None:
    """The banner is what the poll asks for and what the link is made of: the
    station spoke, so the link is `up`. What it names of the firmware on the
    box goes no further than this app — the row carries the link and the
    reason and nothing about a build, a microcontroller's flash not being
    the railroad's business (#567).
    """
    bus, tap = bus_and_tap()
    port = Port()
    async with running(bus, port):
        station = await port.opened()
        station.says(
            b"<iDCC-EX V-5.6.4 / ESP32 / EXCSB1_WITH_EX8874 G-v5.6.4-rails49.1>"
        )
        await asyncio.sleep(QUIET_S)
        bus.drain()
        said = tap.values(DEVICE_LINK)
        assert [value["link"] for value in said] == ["down", "up"]
        assert set(said[-1]) == {"at", "id", "link", "detail"}


def test_an_answer_this_app_cannot_parse_is_still_the_station_answering() -> None:
    asyncio.run(_answer_this_app_cannot_parse_is_still_the_station_answering())


async def _answer_this_app_cannot_parse_is_still_the_station_answering() -> None:
    """A message this app reads nothing out of is not a link failure: the
    link is made of the station having answered and never of the parse, so a
    banner of a shape this app does not recognise raises it just the same."""
    bus, tap = bus_and_tap()
    port = Port()
    async with running(bus, port):
        station = await port.opened()
        station.says(b"<iDCC-EX V-5.6.4 / ESP32>")
        await asyncio.sleep(QUIET_S)
        bus.drain()
        said = tap.values(DEVICE_LINK)
        assert [value["link"] for value in said] == ["down", "up"]


# -- a district the station cut itself (ADR-0016) -------------------------

OVERLOAD_A = (
    b"<* TRACK A POWER OVERLOAD 3120mA (max 3000mA) detected after    2ms."
    b" Pause   40ms *>"
)
OVERLOAD_B = (
    b"<* TRACK B POWER OVERLOAD 3120mA (max 3000mA) detected after    2ms."
    b" Pause   40ms *>"
)
RESTORE_B = b"<* TRACK B POWER RESTORE (after   40ms) *>"
NORMAL_B = b"<* TRACK B NORMAL (after 20ms/40ms) 180mA *>"
ALERT_B = b"<* TRACK B ALERT  2900mA *>"


async def supply(
    station: Station, bus: InProcessBus, tap: Tap, *said: bytes
) -> list[Payload]:
    """Every `device/track` frame so far, once the station has said `said`,
    without its timestamp."""
    station.says(*said)
    await asyncio.sleep(QUIET_S)
    bus.drain()
    return [
        {key: value for key, value in frame.items() if key != "at"}
        for frame in tap.values(DEVICE_TRACK)
    ]


def test_a_district_that_trips_leaves_the_others_on() -> None:
    asyncio.run(_district_that_trips_leaves_the_others_on())


async def _district_that_trips_leaves_the_others_on() -> None:
    bus, tap = bus_and_tap()
    port = Port()
    async with running(bus, port):
        station = await port.opened()
        await supply(station, bus, tap, b"<p1 A>", b"<p1 B>")
        said = await supply(station, bus, tap, OVERLOAD_B, b"<p0 B>")
        assert said[-1] == {"power": "on", "reason": "district B tripped"}


def test_every_district_tripped_reads_off() -> None:
    asyncio.run(_every_district_tripped_reads_off())


async def _every_district_tripped_reads_off() -> None:
    bus, tap = bus_and_tap()
    port = Port()
    async with running(bus, port):
        station = await port.opened()
        await supply(station, bus, tap, b"<p1 A>", b"<p1 B>")
        said = await supply(
            station, bus, tap, OVERLOAD_A, OVERLOAD_B, b"<p0 A>", b"<p0 B>"
        )
        assert said[-1] == {"power": "off", "reason": "districts A, B tripped"}


def test_normal_ends_a_trip() -> None:
    asyncio.run(_normal_ends_a_trip())


async def _normal_ends_a_trip() -> None:
    bus, tap = bus_and_tap()
    port = Port()
    async with running(bus, port):
        station = await port.opened()
        await supply(station, bus, tap, b"<p1 A>", b"<p1 B>", OVERLOAD_B, b"<p0 B>")
        said = await supply(station, bus, tap, NORMAL_B, b"<p1 B>")
        assert said[-1] == {"power": "on"}


def test_a_district_the_station_says_is_on_is_no_longer_tripped() -> None:
    asyncio.run(_district_the_station_says_is_on_is_no_longer_tripped())


async def _district_the_station_says_is_on_is_no_longer_tripped() -> None:
    """Another throttle turns the power off and on: the district goes back to
    ON with no `NORMAL`, and the station prints `1` only for a district that
    is on."""
    bus, tap = bus_and_tap()
    port = Port()
    async with running(bus, port):
        station = await port.opened()
        await supply(station, bus, tap, b"<p1 A>", b"<p1 B>", OVERLOAD_B, b"<p0 B>")
        said = await supply(station, bus, tap, b"<p0>", b"<p1 B>", b"<p1 A>")
        assert said[-1] == {"power": "on"}


def test_the_line_naming_no_track_ends_every_trip_when_on() -> None:
    asyncio.run(_line_naming_no_track_ends_every_trip_when_on())


async def _line_naming_no_track_ends_every_trip_when_on() -> None:
    bus, tap = bus_and_tap()
    port = Port()
    async with running(bus, port):
        station = await port.opened()
        await supply(station, bus, tap, b"<p1 A>", b"<p1 B>", OVERLOAD_B, b"<p0 B>")
        said = await supply(station, bus, tap, b"<p1>")
        assert said[-1] == {"power": "on"}


def test_a_commanded_off_ends_every_trip() -> None:
    asyncio.run(_commanded_off_ends_every_trip())


async def _commanded_off_ends_every_trip() -> None:
    bus, tap = bus_and_tap()
    port = Port()
    async with running(bus, port):
        station = await port.opened()
        await supply(station, bus, tap, b"<p1 A>", b"<p1 B>", OVERLOAD_B, b"<p0 B>")
        wanted(bus, TRACK, "", {"power": "off"})
        bus.drain()
        said = await supply(station, bus, tap, b"<p0>")
        assert said[-1] == {"power": "off"}


def test_a_lost_link_says_the_link_and_not_the_trip() -> None:
    asyncio.run(_lost_link_says_the_link_and_not_the_trip())


async def _lost_link_says_the_link_and_not_the_trip() -> None:
    bus, tap = bus_and_tap()
    port = Port()
    async with running(bus, port):
        station = await port.opened()
        await supply(station, bus, tap, b"<p1 A>", b"<p1 B>", OVERLOAD_B, b"<p0 B>")
        station.hangs_up()
        await port.opened(2)
        bus.drain()
        said = tap.values(DEVICE_TRACK)[-1]
        assert said["power"] == "off"
        assert "tripped" not in said["reason"]


def test_a_dead_short_retrying_publishes_once() -> None:
    asyncio.run(_dead_short_retrying_publishes_once())


async def _dead_short_retrying_publishes_once() -> None:
    bus, tap = bus_and_tap()
    port = Port()
    async with running(bus, port):
        station = await port.opened()
        before = len(await supply(station, bus, tap, b"<p1 A>", b"<p1 B>"))
        said = await supply(
            station,
            bus,
            tap,
            OVERLOAD_B,
            b"<p0 B>",
            RESTORE_B,
            OVERLOAD_B,
            b"<p0 B>",
            RESTORE_B,
            OVERLOAD_B,
        )
        assert said[before:] == [{"power": "on", "reason": "district B tripped"}]


def test_an_alert_district_reads_powered() -> None:
    asyncio.run(_alert_district_reads_powered())


async def _alert_district_reads_powered() -> None:
    """The `<s>` digit is `0` for a district the station is watching for a
    rising current, which is still powered (ADR-0016 d.4)."""
    bus, tap = bus_and_tap()
    port = Port()
    async with running(bus, port):
        station = await port.opened()
        await supply(station, bus, tap, b"<p1 A>", b"<p1 B>")
        said = await supply(station, bus, tap, ALERT_B, b"<p0 B>")
        assert said[-1] == {"power": "on"}


def test_districts_that_are_off_leave_the_supply_on() -> None:
    asyncio.run(_districts_that_are_off_leave_the_supply_on())


async def _districts_that_are_off_leave_the_supply_on() -> None:
    """A district nobody uses is off and says nothing about the rest: the
    supply is `on` while one district is (ADR-0016 d.5, amended)."""
    bus, tap = bus_and_tap()
    port = Port()
    async with running(bus, port):
        station = await port.opened()
        said = await supply(
            station, bus, tap, b"<p1 A>", b"<p1 B>", b"<p0 C>", b"<p0 D>"
        )
        assert said[-1] == {"power": "on"}


def test_every_district_off_reads_off() -> None:
    asyncio.run(_every_district_off_reads_off())


async def _every_district_off_reads_off() -> None:
    bus, tap = bus_and_tap()
    port = Port()
    async with running(bus, port):
        station = await port.opened()
        await supply(station, bus, tap, b"<p1 A>", b"<p0 B>")
        said = await supply(station, bus, tap, b"<p0 A>")
        assert said[-1] == {"power": "off"}


def test_a_trip_beside_an_unused_district_leaves_the_supply_on() -> None:
    asyncio.run(_trip_beside_an_unused_district_leaves_the_supply_on())


async def _trip_beside_an_unused_district_leaves_the_supply_on() -> None:
    """The bench on 2026-10-01: A and B on, C and D unused, A shorted."""
    bus, tap = bus_and_tap()
    port = Port()
    async with running(bus, port):
        station = await port.opened()
        await supply(station, bus, tap, b"<p1 A>", b"<p1 B>", b"<p0 C>", b"<p0 D>")
        said = await supply(station, bus, tap, OVERLOAD_A, b"<p0 A>")
        assert said[-1] == {"power": "on", "reason": "district A tripped"}


def test_the_lock_the_station_reports_reads_stopped() -> None:
    asyncio.run(_lock_the_station_reports_reads_stopped())


async def _lock_the_station_reports_reads_stopped() -> None:
    """`stopped` reaches the bus from what the station says and never from
    having commanded it: a railroad that read back its own command would be
    an echo and not an observation.

    So a stop this app sends leaves the supply reading `on`, the one-shot
    holding nothing for a station to report, and the only `stopped` there is
    is a lock some other throttle set on a station that has one (#463, #464).
    """
    bus, tap = bus_and_tap()
    port = Port()
    async with running(bus, port):
        station = await port.opened()
        station.says(b"<p1>")
        await asyncio.sleep(QUIET_S)
        bus.drain()
        assert [value["power"] for value in tap.values(DEVICE_TRACK)] == ["off", "on"]

        wanted(bus, TRACK, "", {"power": "stopped"})
        bus.drain()
        assert await station.heard(1) == [b"<!>"]
        await asyncio.sleep(QUIET_S)
        bus.drain()
        assert [value["power"] for value in tap.values(DEVICE_TRACK)] == ["off", "on"]

        station.says(b"<!PAUSED>")
        await asyncio.sleep(QUIET_S)
        bus.drain()
        assert [value["power"] for value in tap.values(DEVICE_TRACK)][-1] == "stopped"


def test_a_dropped_link_takes_the_power_reading_with_it() -> None:
    asyncio.run(_dropped_link_takes_the_power_reading_with_it())


async def _dropped_link_takes_the_power_reading_with_it() -> None:
    """What cannot be read is not what was last read: a district that tripped
    while the link was down would otherwise stand as an observation nobody
    made."""
    bus, tap = bus_and_tap()
    port = Port()
    async with running(bus, port):
        station = await port.opened()
        station.says(b"<p1>")
        await asyncio.sleep(QUIET_S)
        bus.drain()
        assert [value["power"] for value in tap.values(DEVICE_TRACK)][-1] == "on"

        station.hangs_up()
        await port.opened(2)
        bus.drain()
        assert [value["power"] for value in tap.values(DEVICE_TRACK)][-1] == "off"


def test_no_position_is_ever_observed() -> None:
    asyncio.run(_no_position_is_ever_observed())


async def _no_position_is_ever_observed() -> None:
    """This railroad's turnouts have no feedback and the station's answer to
    a throw is one it faked, so the row stays empty however many turnouts are
    thrown: a faked observation is worse than silence."""
    bus, tap = bus_and_tap()
    port = Port()
    async with running(bus, port):
        station = await port.opened()
        wanted(bus, POINT, "5", {"addr": "5", "position": "thrown"})
        bus.drain()
        assert await station.heard(1) == [b"<a 2 0 1>"]
        station.says(b"<H 1 1>", b"<p1>")
        await asyncio.sleep(QUIET_S)
        bus.drain()
    assert not [topic for topic in tap.topics() if topic.startswith(DEVICE_POINT)]
    assert tap.topics() >= {DEVICE_TRACK, DEVICE_LINK}


# -- the poll -------------------------------------------------------------


def test_the_poll_asks_for_the_status_and_asks_for_nothing_else() -> None:
    asyncio.run(_poll_asks_for_the_status_and_asks_for_nothing_else())


async def _poll_asks_for_the_status_and_asks_for_nothing_else() -> None:
    """The status because an overload is not broadcast, and **nothing more**.

    A poll runs for as long as the link does, so a command in it that a
    station acts on rather than answers is acted on for as long as the
    railroad is up. That is what a lock query was here: on a station whose
    `!` opcode takes no suffix it read as the emergency stop itself, and a
    train driven from any throttle moved for one poll interval and stood
    (#463).

    So the assertion is the whole of what a poll sends and not its first
    line. What this cannot check is what a station makes of those bytes —
    the fake below answers the documents, and the firmware is what read them
    differently — which is why the drive-and-wait step in
    `docs/dccex/README.md` is the check that catches the next one of these.
    """
    bus, _ = bus_and_tap()
    port = Port()
    async with running(bus, port, poll_s=0.01):
        station = await port.opened()
        assert await station.heard(1) == [b"<s>"]
        assert await station.heard(1) == [b"<s>"]
        assert await station.heard(1) == [b"<s>"]


def test_a_station_that_stops_answering_lowers_the_link() -> None:
    asyncio.run(_station_that_stops_answering_lowers_the_link())


async def _station_that_stops_answering_lowers_the_link() -> None:
    """The link is the station answering, not the socket being open.

    `dccex-usb` holds its clients through an outage and drops their bytes,
    and a wedged station leaves the mirror nothing to report at all, so the
    session goes on and nothing closes. Ten unanswered polls are what says
    the station is gone, and the supply says it too: `layout` folds a link
    it has heard say `down` to `state/power: off`, which is the point of the
    row (control ADR-0066).
    """
    bus, tap = bus_and_tap()
    port = Port()
    clock = [0.0]
    async with running(bus, port, poll_s=FAST_POLL_S, now=lambda: clock[0]):
        station = await port.opened()
        station.says(b"<p1>")
        await asyncio.sleep(QUIET_S)
        bus.drain()
        assert [value["link"] for value in tap.values(DEVICE_LINK)] == ["down", "up"]

        clock[0] = 10 * FAST_POLL_S
        await asyncio.sleep(QUIET_S)
        bus.drain()
        gone = tap.values(DEVICE_LINK)[-1]
        assert gone["link"] == "down"
        assert "has not answered" in gone["detail"]
        assert "0.05s" in gone["detail"]

        dark = tap.values(DEVICE_TRACK)[-1]
        assert dark["power"] == "off"
        assert dark["reason"] == gone["detail"]


def test_a_station_answering_inside_the_window_keeps_the_link_up() -> None:
    asyncio.run(_station_answering_inside_the_window_keeps_the_link_up())


async def _station_answering_inside_the_window_keeps_the_link_up() -> None:
    """The number has teeth — a `down` takes the railroad's power with it —
    so an answer at the last interval before the threshold is an answer, and
    the window starts again from it."""
    bus, tap = bus_and_tap()
    port = Port()
    clock = [0.0]
    async with running(bus, port, poll_s=FAST_POLL_S, now=lambda: clock[0]):
        station = await port.opened()
        station.says(b"<p1>")
        await asyncio.sleep(QUIET_S)

        clock[0] = 9 * FAST_POLL_S
        await asyncio.sleep(QUIET_S)
        station.says(b"<p1>")
        await asyncio.sleep(QUIET_S)

        clock[0] = 18 * FAST_POLL_S
        await asyncio.sleep(QUIET_S)
        bus.drain()
        assert [value["link"] for value in tap.values(DEVICE_LINK)] == ["down", "up"]


def test_a_station_that_answers_again_raises_the_link() -> None:
    asyncio.run(_station_that_answers_again_raises_the_link())


async def _station_that_answers_again_raises_the_link() -> None:
    """Nothing was torn down, so nothing has to be rebuilt: the message that
    comes back raises the link by the path every message raises it."""
    bus, tap = bus_and_tap()
    port = Port()
    clock = [0.0]
    async with running(bus, port, poll_s=FAST_POLL_S, now=lambda: clock[0]):
        station = await port.opened()
        station.says(b"<p1>")
        await asyncio.sleep(QUIET_S)

        clock[0] = 10 * FAST_POLL_S
        await asyncio.sleep(QUIET_S)
        bus.drain()
        assert tap.values(DEVICE_LINK)[-1]["link"] == "down"

        station.says(
            b"<iDCC-EX V-5.6.4 / ESP32 / EXCSB1_WITH_EX8874 G-v5.6.4-rails49.1>"
        )
        await asyncio.sleep(QUIET_S)
        bus.drain()
        assert tap.values(DEVICE_LINK)[-1]["link"] == "up"


def test_a_station_that_has_never_answered_is_not_lowered_again() -> None:
    asyncio.run(_station_that_has_never_answered_is_not_lowered_again())


async def _station_that_has_never_answered_is_not_lowered_again() -> None:
    """A socket that opened onto silence is already `down`, and says why in
    its own words. There is nothing for the poll to notice and no second
    reason to publish over the first."""
    bus, tap = bus_and_tap()
    port = Port()
    clock = [0.0]
    async with running(bus, port, poll_s=FAST_POLL_S, now=lambda: clock[0]):
        await port.opened()
        clock[0] = 100 * FAST_POLL_S
        await asyncio.sleep(QUIET_S)
        bus.drain()
        assert [value["link"] for value in tap.values(DEVICE_LINK)] == ["down"]
        assert "has not answered" not in tap.values(DEVICE_LINK)[-1]["detail"]


# -- standing the railroad down -------------------------------------------


def test_a_clean_exit_zeroes_every_locomotive_and_switches_the_track_off() -> None:
    asyncio.run(_clean_exit_zeroes_every_locomotive_and_switches_the_track_off())


async def _clean_exit_zeroes_every_locomotive_and_switches_the_track_off() -> None:
    """The process ending is not by itself an instruction to the railroad, so
    the exit is one: zero to every locomotive commanded, in the order they
    were, and only then the power (#314). Cutting the supply first would
    leave the speeds in the station's slots for the next power-on to
    resume."""
    bus, _ = bus_and_tap()
    port = Port()
    async with running(bus, port) as app:
        station = await port.opened()
        wanted(bus, TRACK, "", {"power": "on"})
        wanted(bus, TRACTION, "10", {"addr": "10", "speed": 0.5})
        wanted(bus, TRACTION, "11", {"addr": "11", "speed": -1.0})
        bus.drain()
        assert await station.heard(3) == [b"<1>", b"<t 10 63 1>", b"<t 11 126 0>"]

        await app.shutdown()
        assert await station.heard(3) == [b"<t 10 0 1>", b"<t 11 0 1>", b"<0>"]


def test_standing_down_a_railroad_that_was_never_reached_sends_nothing() -> None:
    asyncio.run(_standing_down_a_railroad_that_was_never_reached_sends_nothing())


async def _standing_down_a_railroad_that_was_never_reached_sends_nothing() -> None:
    """A station the link never opened to is one this app was not driving.
    `_send` drops rather than queues, so the exit is silent rather than a
    backlog waiting for a connection that is not coming."""
    bus, _ = bus_and_tap()
    app = DccEx(bus, connect=Port().connect)
    bus.drain()
    await app.shutdown()  # no link, no writer, and nothing raised
