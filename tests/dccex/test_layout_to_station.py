"""A person's power ON, from `layout` through the broker to the station.

The translator's suites drive it with desired rows a test writes itself. This
one has `control`'s layout interface write them, as it does on the box, so
the seam between the two repositories is under test here: `tc49` is a
dependency (ADR-0014 d.2), and a pin that moved `layout`'s rows out from under
the translator goes red here rather than on the railroad.

The layout interface is built in-process on its own client of the broker and
drained on a thread, which is what `python -m tc49.layout` does once it has a
railroad. Its command line waits for a store first, and the store is not
what is under test.
"""

import threading
from collections.abc import Iterator

import pytest
from tc49.layout import LayoutInterface
from tc49.lib.clock import Clock
from tc49.lib.layout import Layout
from tc49.lib.mqtt import MqttBus
from tc49.lib.roster import Roster

from tests.brokers import Broker
from tests.dccex.test_main import App, Station

pytestmark = pytest.mark.broker

POWER_WANTED = "tc49/layout/power_wanted"


def railroad() -> Layout:
    """One block and nothing else: power is the railroad's as a whole."""
    return Layout.from_document(
        {
            "layout": "bench",
            "units": "mm",
            "blocks": {"main": {"length": 1000}},
            "connections": {},
        }
    )


class Interface:
    """`layout` on its own client, drained on a thread until the test ends."""

    def __init__(self, broker: Broker) -> None:
        self.bus = MqttBus(port=broker.port)
        assert self.bus.wait_connected(), "layout never reached the broker"
        clock = Clock()
        self._app = LayoutInterface(self.bus, railroad(), Roster("bench", {}), clock)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        while not self._stop.is_set():
            self._app.settle()
            self.bus.drain()
            self._stop.wait(0.01)

    def close(self) -> None:
        self._stop.set()
        self._thread.join(timeout=5)
        self.bus.close()


@pytest.fixture
def layout(broker: Broker) -> Iterator[Interface]:
    running = Interface(broker)
    try:
        yield running
    finally:
        running.close()


@pytest.fixture
def station() -> Iterator[Station]:
    serving = Station()
    try:
        yield serving
    finally:
        serving.close()


@pytest.fixture
def app(broker: Broker, station: Station) -> Iterator[App]:
    running = App(broker, station)
    try:
        yield running
    finally:
        running.stop()


def test_a_power_on_asked_of_layout_reaches_the_station(
    broker: Broker, station: Station, layout: Interface, app: App
) -> None:
    station.opens()
    app.start()
    assert app.up.wait(5), "the translator never came up"

    hand = MqttBus(port=broker.port)
    assert hand.wait_connected(), "the hand never reached the broker"
    try:
        hand.publish(POWER_WANTED, {"power": "on"})
        assert station.waits_for(b"<1>"), f"the station heard {station.heard()!r}"
    finally:
        hand.close()
