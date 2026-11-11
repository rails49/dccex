"""What pytest has to be told by name: the fixtures the translator's suites
take without importing them — a real `mosquitto` in `rails49_testing.broker`,
the clients on it in `tests/brokers.py`, and the fake store in
`tests/stores.py`."""

pytest_plugins = ["rails49_testing.broker", "tests.brokers", "tests.stores"]
