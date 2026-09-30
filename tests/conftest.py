"""What pytest has to be told by name: the `broker` fixture in `tests/brokers.py`,
which the translator's suites take without importing it."""

pytest_plugins = ["tests.brokers"]
