"""Where the page reaches the bus, and the one row it reads off it.

The **band** asks `layout` for power (ADR-0017): a press publishes
`tc49/layout/power_wanted` and the button reads `tc49/layout/state/power`, so
the page is a client of `control`'s broker as well as of the mirror's **face**
(the organisation's ADR-0002).

**What a payload means is run** — `reported` is a pure function of the bytes
and the gate puts them through it (`tests/ui/test_readings.py`) — and **what
the connection does is driven**, against a broker with nothing behind it
(`ui/test/bus.test.ts`). What is left is read off the source, because what is
left is the connection: an `mqtt` client, a reconnect and `window.location`,
and the gate has no broker and no browser to exercise one with. It is the same
division `tests/ui/test_stream.py` has with the stream, and the first claim is
the same claim: no host and no port is written into the page, so the one thing
this module may name is a prefix on the page's own origin.
"""

from tests.ui.test_look import UI
from tests.ui.test_stream import code, modules, quoted

#: The connection: where the broker is, what is subscribed to, and what a
#: press publishes.
BUS = UI / "src" / "bus.ts"

#: The readings, where a payload is read.
READINGS = UI / "src" / "readings.js"

#: The page's two configurations: what the box serves, and what a laptop runs.
VITE = UI / "vite.config.ts"

#: The prefix the broker answers under on the page's own origin, which the door
#: strips before the broker sees a request (ADR-0017 d.5). Written out here
#: rather than read off the module that spells it, for the reason `ROUTE` is
#: written out in `tests/ui/test_compose_serves.py`: a check that took what it
#: asserts from the file it is checking would pass on whatever that file said.
PREFIX = "/mqtt"

#: The row the band reads, and the row a press writes. `control`'s, named in
#: full: the page subscribes to one row of a railroad rather than to a
#: railroad.
STATE = "tc49/layout/state/power"
WANTED = "tc49/layout/power_wanted"

#: Where a development server sends the prefix, which is the broker's own port
#: on the machine somebody is working on. There is no door on a laptop, so this
#: stands in for one; it is in nothing the box serves.
LOCAL = "ws://127.0.0.1:9001"


def test_the_broker_is_on_the_pages_own_origin_through_the_one_address_rule() -> None:
    """The page is served over the box's door and cannot dial 9001 on the
    layout box, so the broker is a prefix on this origin and the door routes it
    (ADR-0017 d.5, ADR-0004 d.2).

    The address is `socketAt`'s, which is the one rule the page has about where
    a socket is and is run rather than read (`tests/ui/test_stream.py`): a
    second rule here would be a second answer to how this page reaches
    anything.
    """
    source = BUS.read_text()
    assert f'MQTT_PATH = "{PREFIX}"' in source, "the page spells no broker prefix"
    assert (
        "connect(socketAt(window.location, MQTT_PATH)" in source
    ), "the bus builds an address of its own"


def test_the_prefix_is_spelt_once_on_the_page() -> None:
    """One answer to where the broker is. A second spelling and the day the
    door's route moves only one of them would follow (`face.ts`,
    `tests/ui/test_stream.py`)."""
    for name, module in modules().items():
        written = quoted(module).count(PREFIX)
        assert written == (
            1 if name == BUS.name else 0
        ), f"{name} spells the broker's prefix {written} times"


def test_the_page_holds_one_connection_to_the_broker() -> None:
    """One, in the module that is the connection.

    A pane or a component that opened one of its own would be a second client
    of `control`'s broker for one page, which is the rule the **stream** is
    held to for the mirror's port (`tests/ui/test_stream.py`, ADR-0007 d.2).
    """
    for name, module in modules().items():
        opened = code(module).count("connect(")
        assert opened == (
            1 if name == BUS.name else 0
        ), f"{name} opens {opened} connections of its own"


def test_the_page_subscribes_to_the_power_row_and_to_nothing_else() -> None:
    """One row, and it is the one the button reads (ADR-0017 d.2).

    What a railroad is doing is `control`'s UI next door; the one thing this
    page needs of the bus is whether the rails are hot and a way to ask for
    them, so a second subscription would be this page reading a railroad.
    """
    source = code(BUS.read_text())
    assert f'POWER_STATE = "{STATE}"' in source, "the page reads no power row"
    assert source.count("subscribe(") == 1, "the page subscribes to a second row"
    assert "subscribe(POWER_STATE" in source, "the page subscribes to something else"


def test_a_press_publishes_the_wanted_row_at_qos_0_and_not_retained() -> None:
    """The row a browser may write, as `control`'s band writes it (ADR-0017
    d.1, `control`'s `docs/BUS.md`).

    Not retained: it is a request and not a state, and a retained one would be
    answered again by every `layout` that started afterwards. One publish, so
    a press is one ask — the colour the button wears is the state row that
    follows, or nothing where `layout` dropped the ask (ADR-0017 d.4).
    """
    source = code(BUS.read_text())
    assert f'POWER_WANTED = "{WANTED}"' in source, "the page asks for nothing"
    assert source.count("publish(") == 1, "the page publishes a second row"
    assert "publish(POWER_WANTED" in source, "the press publishes something else"
    assert "qos: 0" in source and "retain: false" in source, "the ask is retained"


def test_the_bus_reads_no_payload_of_its_own() -> None:
    """What `layout` reported is the readings module's — a pure function of the
    bytes, run with the payloads that matter (`tests/ui/test_readings.py`,
    ADR-0009 d.3) — and the connection is this module's.

    A connection that read the payload itself would draw the same reading until
    the two answers parted, so the driven check cannot see this one and the
    source can.
    """
    assert 'from "./readings.js"' in BUS.read_text(), "the bus reads a payload itself"
    assert "export function reported(" in READINGS.read_text(), "nothing reads one"


def test_the_bus_dials_the_broker_again_by_itself() -> None:
    """Everything that ends a connection is something that ends — an outage,
    the broker restarting, the door going down — and a band that stayed
    disabled until somebody reloaded the page would ask an operator to reload
    it for a network that was out for ten seconds (`REOPEN_MS`,
    `stream.ts`)."""
    source = code(BUS.read_text())
    assert "RECONNECT_MS = 2000" in source, "the bus waits nothing out"
    assert "reconnectPeriod: RECONNECT_MS" in source, "the bus dials once"


def test_a_development_server_stands_in_for_the_door() -> None:
    """There is no door on a laptop, so the page's development server routes
    the prefix to the broker's own port and strips it, as the door does
    (`compose.box.yaml`, ADR-0017 d.5).

    It is the server's and is in nothing the box serves: the image is nginx
    over what `vite build` produced, and a proxy is not part of a build
    (`deploy/ui.Dockerfile`).
    """
    served = VITE.read_text()
    assert f'"{PREFIX}": {{' in served, "the development server routes no broker"
    assert f'target: "{LOCAL}"' in served, "it does not name the broker's port"
    assert "ws: true" in served, "the proxy does not carry a socket"
    assert f'replace(/^\\{PREFIX}/, "")' in served, "the prefix is not stripped"
