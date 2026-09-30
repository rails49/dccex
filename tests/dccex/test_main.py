"""The translator as its own process: what it takes for it to come up alone.

Against a real broker and a real listener on real sockets, because that is
what is under test — an app started against nothing, in whatever order the
machine brings the two up (control ADR-0059, decision 5). The station is reached by
**address** here rather than by the injected connection `test_translator.py`
drives: an address is what `--station` gives and opening it is what this
command line has to get right. Nothing needs hardware, which is the rule the
whole gate sits under.

The store is a fake of `control`'s routes on loopback (`tests/stores.py`) and
the railroad is named on the broker by a client standing in for `layout`,
because between them they decide which script this process runs — and a
script's text changing under it is one of the two ways this process ends
(ADR-0015 d.3).

The loop runs on a thread here and is ended with the event `serve` takes; in
the deployment it is the main thread, asyncio owns it, and a signal ends it.
What a test waits on is the station's end of the wire — a message arriving
there is the app having drained the broker's queue on the loop thread and
written to the socket.
"""

import socket
import threading
import time
from collections.abc import Iterator

import pytest
from tc49.lib.bus import Payload
from tc49.lib.mqtt import MqttBus

from dccex.__main__ import serve
from dccex.store import Scripts
from tests.brokers import Broker, drained, settle
from tests.ports import free_port
from tests.stores import Store

pytestmark = pytest.mark.broker

RAILROAD = "tc49/layout/state/railroad"
WANTED_TRACK = "tc49/layout/state/wanted/track"
WANTED_TRACTION = "tc49/layout/state/wanted/traction/10"
DEVICE_TRACK = "tc49/layout/state/device/track"
DEVICE_LINK = "tc49/layout/state/device/link"

TRACK_ON = b"<1>"
TRACK_OFF = b"<0>"
POLL = b"<s>"
HALF_SPEED_10 = b"<t 10 63 1>"
HALTED_10 = b"<t 10 0 1>"

TIMEOUT_S = 5.0

BACKOFF_S = 0.01
"""The retry the suite gives the app, where the deployment starts at half a
second and doubles to eight: a station that appears three lines after the app
went looking for it is what these tests wait on, and waiting out a deployed
backoff to see it would be waiting on nothing else."""

RETAINED_S = 0.5
"""How long the app waits for the broker's retained rows — the railroad, and
the desired picture — before it opens the link, where the deployment gives
each of them a second.

Room enough for the **railroad** row, which is the one with a consequence: an
app that opened its link before that row landed would have asked the store
for no railroad's script, and the power ON it then refuses is not replayed
when the script arrives a moment later (ADR-0013 d.6). The desired picture
wants none of this room here — everything is on loopback and already queued
by the time the subscription is acknowledged — and what the window costs a
test is what it spends rather than what it proves."""

SCRIPT_S = 0.05
"""How often the suite's app asks the store for its script, where the
deployment asks every few seconds: what a test waits on is a script applied
one line ago."""

SCRIPT = """\
@on("power")
def power(t):
    t.default()
    t.send("<= A LIMIT 3000>")
"""

LIMIT_A = b"<= A LIMIT 3000>"


class Station:
    """A command station's end of the port, on loopback.

    Bound when `opens()` is called and not before, so a test can have the app
    go looking for a mirror that is not up yet — the port is taken from the
    same place a broker's is, and held only by having been asked for.

    One connection, answered with a status line so that the app has heard the
    station *speak* — `device/link` goes `up` on an answer and not on an open
    socket — and everything it is sent kept for the test to read.
    """

    def __init__(self) -> None:
        self.port = free_port()
        self._heard = bytearray()
        self._lock = threading.Lock()
        self._listener: socket.socket | None = None

    def opens(self) -> None:
        listener = socket.socket()
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", self.port))
        listener.listen(1)
        self._listener = listener
        threading.Thread(target=self._serve, args=(listener,), daemon=True).start()

    def _serve(self, listener: socket.socket) -> None:
        try:
            connection, _ = listener.accept()
        except OSError:
            return  # closed before anything connected, which is a test ending
        with connection:
            try:
                connection.sendall(b"<p0>")  # answering: the rails are dark
                while True:
                    arrived = connection.recv(4096)
                    if not arrived:
                        return
                    with self._lock:
                        self._heard += arrived
            except OSError:
                return

    def heard(self) -> bytes:
        with self._lock:
            return bytes(self._heard)

    def waits_for(self, message: bytes, limit_s: float = TIMEOUT_S) -> bool:
        """Whether that message has arrived, waiting up to `limit_s` for it:
        the wire between the app writing and this end reading is a thread
        boundary, so arrival is a wait and never a given."""
        deadline = time.monotonic() + limit_s
        while message not in self.heard():
            if time.monotonic() > deadline:
                return False
            time.sleep(0.01)
        return True

    def close(self) -> None:
        if self._listener is not None:
            self._listener.close()


@pytest.fixture
def station() -> Iterator[Station]:
    serving = Station()
    try:
        yield serving
    finally:
        serving.close()


class App:
    """The translator running as `python -m dccex` runs it, on a thread
    so the test can watch the bus and the port while it is up.

    Its client is made when it starts and not before, so a test can stop the
    broker first and have the app go looking for one that is not there.
    """

    def __init__(
        self,
        broker: Broker,
        station: Station,
        store: Store | None = None,
        id: str = "dccex",
    ) -> None:
        self.id = id
        self._broker = broker
        self._station = station
        self._store = store
        self._bus: MqttBus | None = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.up = threading.Event()
        self.said_railroad = ""

    def start(self) -> None:
        self._bus = MqttBus(port=self._broker.port)
        self._thread = threading.Thread(
            target=serve,
            args=(self._bus, ("127.0.0.1", self._station.port), self._stop),
            kwargs={
                "scripts": None if self._store is None else Scripts(self._store.url),
                "id": self.id,
                "period_s": 0.01,
                "retained_s": RETAINED_S,
                "script_s": SCRIPT_S,
                "first_backoff_s": BACKOFF_S,
                "max_backoff_s": BACKOFF_S,
                "log": self._log,
            },
            daemon=True,
        )
        self._thread.start()

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=10)
        if self._bus is not None:
            self._bus.close()

    def _log(self, line: str) -> None:
        """The app's log, dropped except for the two lines a test reads: the
        railroad it came up on, whose script it asked for, and that it is on
        the broker and looping. What the log says is for a person watching a
        container; the suite asserts on the bus and on the wire."""
        if line.startswith("railroad "):
            self.said_railroad = line.removeprefix("railroad ").strip("'")
        if line.startswith("up as"):
            self.up.set()


@pytest.fixture
def app(broker: Broker, station: Station, store: Store) -> Iterator[App]:
    running = App(broker, station, store)
    try:
        yield running
    finally:
        running.stop()


def watching(broker: Broker) -> tuple[MqttBus, list[tuple[str, Payload]]]:
    """Another client of the same broker, and everything it hears: the app is
    only visible where anything else on the railroad sees it."""
    bus = MqttBus(port=broker.port)
    assert bus.wait_connected(), "the witness never reached the broker"
    heard: list[tuple[str, Payload]] = []
    bus.subscribe("tc49/#", lambda topic, payload: heard.append((topic, payload)))
    return bus, heard


def rows(heard: list[tuple[str, Payload]], topic: str) -> list[Payload]:
    """What arrived on one topic, in the order it arrived."""
    return [payload for said, payload in heard if said == topic]


def wanting(broker: Broker) -> MqttBus:
    """A client publishing the rows `layout` owns. Another process here,
    which is what the broker makes of the seam #289 states in one: nothing
    says who published, and nothing here asks (rule 4)."""
    bus = MqttBus(port=broker.port)
    assert bus.wait_connected(), "the writer never reached the broker"
    return bus


def test_a_cold_start_publishes_the_apps_own_rows(
    broker: Broker, station: Station, app: App
) -> None:
    """Against an empty broker with no station on the other end: the two rows
    this app opens with, waiting for whoever subscribes next (control ADR-0059).

    The link it cannot make, keyed by the id it was started with (decision 7),
    and a supply that is off carrying that same sentence as its reason — a
    person reading why the railroad is dark reads it off the supply rather
    than off a second row. What cannot be read may not be called good.
    """
    witness, heard = watching(broker)
    app.start()

    link = f"{DEVICE_LINK}/{app.id}"
    assert drained(witness, lambda: rows(heard, DEVICE_TRACK) != []), "it said nothing"
    assert rows(heard, link)[-1]["link"] == "down"
    assert rows(heard, link)[-1]["id"] == app.id
    assert rows(heard, DEVICE_TRACK)[-1]["power"] == "off"
    assert rows(heard, DEVICE_TRACK)[-1]["reason"] != ""
    assert app.running, "the app stopped on its own"
    witness.close()


def test_its_link_row_is_keyed_by_the_id_it_was_started_with(
    broker: Broker, station: Station
) -> None:
    """`--id` is the whole of what a second translator on one railroad needs:
    the row is keyed by it, so the second's `up` does not erase the first's
    `down` (control ADR-0059, decision 7). A value and not a contract — it appears in
    no drawing and no list of ours."""
    named = App(broker, station, id="north-yard")
    witness, heard = watching(broker)
    try:
        named.start()
        assert drained(
            witness, lambda: rows(heard, f"{DEVICE_LINK}/north-yard") != []
        ), "nothing was published under the id it was given"
        assert rows(heard, f"{DEVICE_LINK}/dccex") == []
    finally:
        named.stop()
        witness.close()


def test_it_applies_the_desired_state_it_finds_on_the_broker(
    broker: Broker, station: Station, store: Store, app: App
) -> None:
    """The loop is what makes the app an app, and this is the whole path:
    `layout`'s retained rows are on the broker before this process exists,
    the client's network thread queues them, the drain hands them to the
    asyncio loop, and the loop writes them to the station.

    The power is not among them. The rails stay as the station reports them
    and come back when a person presses ON, which is the press below
    (ADR-0013 d.6).
    """
    store.opens()
    hand = wanting(broker)
    hand.publish(RAILROAD, {"name": "bench"})
    hand.publish(WANTED_TRACTION, {"addr": "10", "speed": 0.5})
    hand.publish(WANTED_TRACK, {"power": "on"})
    station.opens()
    app.start()

    assert station.waits_for(HALF_SPEED_10), "the locomotive was never commanded"
    assert TRACK_ON not in station.heard(), "the power was replayed"

    hand.publish(WANTED_TRACK, {"power": "on"})

    assert station.waits_for(TRACK_ON), "the press never reached the station"
    assert app.running, "the app stopped on its own"
    hand.close()


def test_it_comes_up_against_a_station_that_is_not_there_yet(
    broker: Broker, station: Station, app: App
) -> None:
    """The order nothing forbids: no `depends_on` anywhere, so the app is
    started before the mirror it drives and retries rather than exiting, as
    the apps that read documents retry the store (control ADR-0059, decision 5).

    A desired value that arrives while the link is down is remembered and
    applied on the connect, which is the same thing that happens to the
    retained one at startup. The power is the exception and is not replayed
    at all (ADR-0013 d.6).
    """
    witness, heard = watching(broker)
    app.start()
    assert app.up.wait(10), "it never came up"
    hand = wanting(broker)
    hand.publish(WANTED_TRACTION, {"addr": "10", "speed": 0.5})
    assert drained(
        witness, lambda: rows(heard, f"{DEVICE_LINK}/{app.id}") != []
    ), "it never said anything about the link it could not make"
    assert rows(heard, f"{DEVICE_LINK}/{app.id}")[-1]["link"] == "down"

    station.opens()

    assert station.waits_for(HALF_SPEED_10), "the link was never made"
    assert drained(
        witness, lambda: rows(heard, f"{DEVICE_LINK}/{app.id}")[-1]["link"] == "up"
    ), "the link came up and the row did not say so"
    hand.close()
    witness.close()


def test_it_comes_up_against_a_broker_that_is_not_there_yet(
    broker: Broker, station: Station, app: App
) -> None:
    """The other order nothing forbids. The two opening rows are publishes,
    and a publish made to a broker that is not there is dropped rather than
    queued (control ADR-0050), so the app waits for the broker before it is built at
    all — and the station is not touched meanwhile."""
    broker.stop()
    station.opens()
    app.start()
    assert not app.up.wait(1), "it said it was up with no broker to be up on"
    assert app.running, "the app gave up on a broker that was not up yet"
    assert station.heard() == b"", "it drove the station with nowhere to report it"

    assert broker.start()

    # Reconnected on the client's own backoff, whose first step is a second.
    assert app.up.wait(30), "it never came up once the broker was there"
    witness, heard = watching(broker)
    assert drained(
        witness, lambda: rows(heard, f"{DEVICE_LINK}/{app.id}") != []
    ), "it never published its own rows"
    witness.close()


def test_it_stands_the_railroad_down_on_its_way_out(
    broker: Broker, station: Station, store: Store, app: App
) -> None:
    """The process ending is not by itself an instruction to the railroad: the
    station goes on running whatever it was last told, so every locomotive this
    app has commanded is sent zero and only then is the track cut.

    The zeros come first because the station keeps a speed per locomotive and
    resumes it, so cutting the supply over a held speed only postpones the
    motion.
    """
    store.opens()
    hand = wanting(broker)
    hand.publish(RAILROAD, {"name": "bench"})
    hand.publish(WANTED_TRACTION, {"addr": "10", "speed": 0.5})
    station.opens()
    app.start()
    assert station.waits_for(HALF_SPEED_10), "the locomotive was never commanded"

    app.stop()

    assert station.waits_for(TRACK_OFF), "the rails were left live"
    heard = station.heard()
    assert heard.index(HALTED_10) < heard.index(TRACK_OFF), "cut over a held speed"
    hand.close()


def test_a_desired_value_it_cannot_read_leaves_it_running(
    broker: Broker, station: Station, app: App
) -> None:
    """A frame claiming to be a desired value is one more thing anyone can
    publish, and on the broker whoever publishes it is another process: a
    translator that raised on one would be taken down from outside
    (BUS.md, rule 4, #289).

    Each is dropped whole — not remembered either, so a connect does not
    replay something that sent nothing when it arrived — and the honest value
    after them still reaches the station.

    Published one after another while the app is up, rather than left on the
    broker: a state topic holds the last value, so three retained frames on
    one row would be one frame by the time this process subscribed.
    """
    witness, _ = watching(broker)
    station.opens()
    app.start()
    assert station.waits_for(POLL), "the link was never made"

    hand = wanting(broker)
    for payload in (
        {"addr": "10"},  # a locomotive and no speed
        {"addr": "10", "speed": "fast"},
        {"addr": "10", "speed": True},  # a boolean is not a speed
    ):
        hand.publish(WANTED_TRACTION, payload)
    settle(witness)
    assert b"<t 10" not in station.heard(), "something unreadable was commanded"

    hand.publish(WANTED_TRACTION, {"addr": "10", "speed": 0.5})

    assert station.waits_for(HALF_SPEED_10), "the honest value was dropped too"
    assert app.running, "a frame from another process took the translator down"
    hand.close()
    witness.close()


def test_it_runs_the_script_the_store_has_for_the_running_railroad(
    broker: Broker, station: Station, store: Store, app: App
) -> None:
    """The whole path of a script: the railroad named on the broker before
    this process exists, the text fetched off the store's face, and the
    handler standing in for the command a desired value makes (ADR-0015
    d.2)."""
    store.holds("bench", SCRIPT)
    store.opens()
    hand = wanting(broker)
    hand.publish(RAILROAD, {"name": "bench"})
    station.opens()
    app.start()
    assert app.up.wait(TIMEOUT_S), "it never came up"
    assert app.said_railroad == "bench", "it came up on no railroad"
    assert station.waits_for(POLL), "the link was never made"

    hand.publish(WANTED_TRACK, {"power": "on"})

    assert station.waits_for(LIMIT_A), "the handler never ran"
    heard = station.heard()
    assert heard.index(TRACK_ON) < heard.index(LIMIT_A), "the default came second"
    assert app.running, "the app stopped on its own"
    hand.close()


def test_a_new_script_text_stands_the_railroad_down_and_ends_the_process(
    broker: Broker, station: Station, store: Store, app: App
) -> None:
    """A script applied on the page while the railroad runs: this process
    exits, and the exit stands the railroad down as every exit does, so the
    new script takes effect from power off at the next ON (ADR-0015 d.3).
    Bringing it up again is compose's."""
    store.holds("bench", SCRIPT)
    store.opens()
    hand = wanting(broker)
    hand.publish(RAILROAD, {"name": "bench"})
    station.opens()
    app.start()
    assert app.up.wait(TIMEOUT_S), "it never came up"
    assert app.said_railroad == "bench", "it came up on no railroad"
    assert station.waits_for(POLL), "the link was never made"
    hand.publish(WANTED_TRACK, {"power": "on"})
    assert station.waits_for(LIMIT_A), "the handler never ran"

    store.holds("bench", SCRIPT.replace("3000", "2500"))

    assert station.waits_for(TRACK_OFF), "the railroad was left live"
    deadline = time.monotonic() + TIMEOUT_S
    while app.running and time.monotonic() < deadline:
        time.sleep(0.01)
    assert not app.running, "the process went on running the old script"
    hand.close()


def test_a_railroad_that_gives_the_same_text_leaves_it_running(
    broker: Broker, station: Station, store: Store, app: App
) -> None:
    """The comparison is the text and never the name, so a railroad loaded
    under this app that has the same script leaves the process running and
    its rows as they were (ADR-0015 d.3)."""
    store.holds("bench", SCRIPT)
    store.holds("yard", SCRIPT)
    store.opens()
    witness, heard = watching(broker)
    hand = wanting(broker)
    hand.publish(RAILROAD, {"name": "bench"})
    station.opens()
    app.start()
    assert app.up.wait(TIMEOUT_S), "it never came up"
    assert drained(
        witness,
        lambda: rows(heard, f"{DEVICE_LINK}/{app.id}")[-1:] != []
        and rows(heard, f"{DEVICE_LINK}/{app.id}")[-1]["link"] == "up",
    ), "the link never came up"
    said = len(rows(heard, f"{DEVICE_LINK}/{app.id}"))

    hand.publish(RAILROAD, {"name": "yard"})
    settle(witness, seconds=4 * SCRIPT_S)

    assert app.running, "the process ended on a script that had not changed"
    assert TRACK_OFF not in station.heard(), "the railroad was stood down"
    assert len(rows(heard, f"{DEVICE_LINK}/{app.id}")) == said, "the row moved"
    hand.close()
    witness.close()
