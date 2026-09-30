"""What pytest has to be told by name: the fixtures the translator's suites
take without importing them — a real `mosquitto` in `tests/brokers.py`, and
the fake store in `tests/stores.py`."""

pytest_plugins = ["tests.brokers", "tests.stores"]
