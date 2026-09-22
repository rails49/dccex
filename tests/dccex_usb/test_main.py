"""The mirror as a process: what the entrypoint does when the mirror ends.

`mirroring` is the loop `python -m dccex_usb` runs — the mirror on a task of
its own, watched for as long as the process is up — and what is asserted here
is its side of that arrangement: a mirror that cannot serve ends the process
rather than leaving it up with no TCP port and no device (#526). A box whose
2560 is already taken, or whose command station is not enumerated yet, depends
on the exit: `restart: unless-stopped` is what tries again.

The bus that was drained beside the mirror is gone with the rest of it
(ADR-0001), so the loop's only business is the mirror and the flash in flight.
There is no device here and no broker. The station is a stand-in whose `run()`
the test writes, because what is under test is the entrypoint's observation of
a mirror rather than the mirror — that is `test_station.py`'s — and the flash
ordering the teardown owes a half-written station is `test_firmware.py`'s.
"""

import asyncio
import errno
import socket
import subprocess
import sys
import threading

import pytest

from dccex_usb.__main__ import mirroring
from dccex_usb.firmware import Flasher
from dccex_usb.station import HOST, Station

DEVICE = "/dev/dccex-that-is-not-there"
PORT = 2560
PERIOD_S = 0.01
TIMEOUT_S = 5.0
TURNS = 3
"""Turns of the loop a test waits out before it ends one: enough that the loop
is going round rather than having gone once."""


class Failing(Station):
    """A mirror that cannot serve: `run()` raises where binding the port on a
    box that already has something on it raises."""

    def __init__(self) -> None:
        super().__init__(DEVICE, PORT)

    async def run(self) -> None:
        raise OSError(errno.EADDRINUSE, "address already in use")


class Endless(Station):
    """A mirror that serves until it is cancelled, which is the live one."""

    def __init__(self) -> None:
        super().__init__(DEVICE, PORT)
        self.cancelled = False

    async def run(self) -> None:
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            self.cancelled = True
            raise


class Settling(Flasher):
    """A flasher with a flash in flight: `settled()` says when the teardown
    reached it, and comes back only once the test lets the flash finish."""

    def __init__(self, device: Station) -> None:
        super().__init__(device, log=lambda line: None)
        self.reached = asyncio.Event()
        self.let_go = asyncio.Event()

    async def settled(self) -> None:
        self.reached.set()
        await self.let_go.wait()


def quiet(device: Station) -> Flasher:
    """The real flasher with nothing in flight, which is every moment but a
    flash: nothing can ask it for one until the face does (#12)."""
    return Flasher(device, log=lambda line: None)


def test_a_mirror_that_cannot_serve_ends_the_loop() -> None:
    """The port is taken, so `run()` raises at once and there is no mirror to
    watch. Before #526 the task's failure was never looked at and the loop
    went round forever: a live process with no TCP server, no device and
    nothing logged, which `restart: unless-stopped` cannot help."""

    async def refused() -> None:
        station = Failing()
        stop = threading.Event()  # the deployment sets it never, and nor does this
        looping = asyncio.create_task(
            mirroring(station, quiet(station), stop, PERIOD_S)
        )
        # Waited on rather than cancelled after: a loop cancelled from outside
        # carries the failure out anyway, and what is asserted is that nothing
        # outside had to.
        ended, _ = await asyncio.wait({looping}, timeout=TIMEOUT_S)
        assert ended, "the loop went round with no mirror behind it"
        await looping

    with pytest.raises(OSError) as carried:
        asyncio.run(refused())
    assert carried.value.errno == errno.EADDRINUSE


def test_a_mirror_that_serves_is_watched_until_stop() -> None:
    """The live arrangement: the loop goes round on its period for as long as
    the mirror is up, and `stop` — the suite's way out, where the deployment's
    is a signal — is what ends it."""

    async def serving() -> Endless:
        station = Endless()
        stop = threading.Event()
        looping = asyncio.create_task(
            mirroring(station, quiet(station), stop, PERIOD_S)
        )
        await asyncio.sleep(TURNS * PERIOD_S)
        assert not looping.done(), "the loop ended with the mirror still serving"
        stop.set()
        await looping
        return station

    station = asyncio.run(asyncio.wait_for(serving(), TIMEOUT_S))
    assert station.cancelled, "the mirror was left running behind the loop"


def test_a_flash_in_flight_is_waited_out_before_the_mirror_is_cancelled() -> None:
    """The one thing the teardown is for: the mirror gives the device back
    when the flash is done with it, so ending in the middle of one leaves the
    station half written (ADR-0065)."""

    async def flashing() -> Endless:
        station = Endless()
        flasher = Settling(station)
        stop = threading.Event()
        looping = asyncio.create_task(mirroring(station, flasher, stop, PERIOD_S))
        await asyncio.sleep(TURNS * PERIOD_S)
        stop.set()
        await flasher.reached.wait()
        assert not station.cancelled, "the mirror went while the flash was writing"
        flasher.let_go.set()
        await looping
        return station

    assert asyncio.run(asyncio.wait_for(flashing(), TIMEOUT_S)).cancelled


def test_a_port_already_in_use_exits_non_zero() -> None:
    """The whole of it as the container runs it. What the box does with the
    exit is the deploy's business; what this app owes it is a process that is
    gone and a reason on stderr (ADR-0050).

    The port is held on `HOST` and not on loopback, which is what the app asks
    for: asyncio binds with `SO_REUSEADDR`, and BSD lets a wildcard bind walk
    past a socket on `127.0.0.1` when it is set — so on a Mac the mirror came
    up beside the holder and this test waited out its timeout instead.
    """
    with socket.socket() as taken:
        taken.bind((HOST, 0))
        taken.listen()
        port = int(taken.getsockname()[1])
        with socket.socket() as probe:
            # The holder really holds it, asked the way the app asks. A
            # platform that answered otherwise would leave the mirror up and
            # this test waiting on a process that is not going to end.
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            with pytest.raises(OSError):
                probe.bind((HOST, port))
        ran = subprocess.run(
            [
                sys.executable,
                "-m",
                "dccex_usb",
                "--device",
                DEVICE,
                "--port",
                str(port),
            ],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_S * 4,
            check=False,  # the non-zero exit is the assertion, not a failure here
        )

    assert ran.returncode != 0
    assert "address already in use" in ran.stderr.lower()
