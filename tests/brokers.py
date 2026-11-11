"""Helpers for the suites that test against a real `mosquitto`, on a bus.

`Broker` and the `broker` fixture are `rails49_testing.broker`'s, loaded in
`tests/conftest.py`. What is here takes an `MqttBus`, which that package does
not know about.
"""

import time
from collections.abc import Callable, Iterator

import pytest
from rails49_testing.broker import Broker, until
from tc49.lib.mqtt import MqttBus


def drained(bus: MqttBus, predicate: Callable[[], bool], timeout: float = 5.0) -> bool:
    """Drain until the test's condition holds, or give up. Draining is the
    only thing that delivers, so waiting for a delivery means draining."""

    def once() -> bool:
        bus.drain()
        return predicate()

    return until(once, timeout)


def settle(bus: MqttBus, seconds: float = 0.5) -> None:
    """Long enough that anything the broker was going to send has arrived and
    been drained. What it takes to assert a negative."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        bus.drain()
        time.sleep(0.01)


@pytest.fixture
def buses(broker: Broker) -> Iterator[Callable[[], MqttBus]]:
    """Make a client on this test's broker, connected before it comes back.
    Every one is closed when the test ends, whatever it did with them."""
    made: list[MqttBus] = []

    def make() -> MqttBus:
        bus = MqttBus(port=broker.port)
        assert bus.wait_connected(), "client never reached the broker"
        made.append(bus)
        return bus

    try:
        yield make
    finally:
        for bus in made:
            bus.close()
