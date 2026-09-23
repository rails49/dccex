"""The mirror as a process: the command line it is started with, and what the
entrypoint does when the mirror ends.

`mirroring` is the loop `python -m dccex_usb` runs — the mirror on a task of
its own, watched for as long as the process is up — and what is asserted here
is its side of that arrangement: a mirror that cannot serve ends the process
rather than leaving it up with no TCP port and no device (#526). A box whose
2560 is already taken, or whose command station is not enumerated yet, depends
on the exit: `restart: unless-stopped` is what tries again.

The parser is the part of `__main__.py` that arrived with no tests behind it:
the rest of the package came across as a copy and brought `control`'s. What is
asserted of it is the device and the port it is started with, the releases URL
it falls back to, and the two arguments the bus took with it (ADR-0001 d.1).
Those two are absent only for as long as nobody adds them back, which is what
the refusals are here to notice.

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

from dccex_usb.__main__ import command_line, mirroring
from dccex_usb.face import PORT as FACE_PORT
from dccex_usb.face import Face, Server
from dccex_usb.firmware import RELEASES, Flasher
from dccex_usb.station import HOST, Station

DEVICE = "/dev/dccex-that-is-not-there"
PORT = 2560
PERIOD_S = 0.01
TIMEOUT_S = 5.0
TURNS = 3
"""Turns of the loop a test waits out before it ends one: enough that the loop
is going round rather than having gone once."""


STARTED = ("--device", DEVICE, "--port", str(PORT))
"""The whole of what the deployment says, which every one of these adds to or
leaves alone."""

ELSEWHERE = "https://api.example.invalid/repos/someone-else/CommandStation-EX/releases"
"""A releases URL that is not the default, so naming it proves the flag is
read rather than that both spellings happen to agree. Nothing fetches it, and
the TLD is one that resolves nowhere in case that ever stops being true."""


def test_the_device_and_the_port_are_what_the_mirror_is_started_with() -> None:
    args = command_line().parse_args(STARTED)

    assert args.device == DEVICE
    assert args.port == PORT


def test_releases_are_read_from_this_installation_s_fork_by_default() -> None:
    """The constant and not the literal: the parser's default and the
    firmware module's source are one URL, and a test that spelled it out
    again would let them drift apart quietly."""
    args = command_line().parse_args(STARTED)

    assert args.firmware_releases == RELEASES


def test_another_source_of_releases_can_be_named() -> None:
    args = command_line().parse_args([*STARTED, "--firmware-releases", ELSEWHERE])

    assert args.firmware_releases == ELSEWHERE


def test_the_face_is_served_on_a_port_of_its_own_by_default() -> None:
    """A port that is not the mirror's: 2560 carries the station's own
    conversation, and the door reaches the face on this one."""
    args = command_line().parse_args(STARTED)

    assert args.face_port == FACE_PORT
    assert args.face_port != args.port


def test_another_port_for_the_face_can_be_named() -> None:
    args = command_line().parse_args([*STARTED, "--face-port", str(FACE_PORT + 1)])

    assert args.face_port == FACE_PORT + 1


@pytest.mark.parametrize(
    "gone, value", [("--broker", "mqtt://broker:1883"), ("--id", "dccex-usb")]
)
def test_the_arguments_that_went_with_the_bus_are_refused(
    gone: str, value: str
) -> None:
    """A broker to dial and a name to key a refusal row by were what started
    this app in `control`, and both went with the bus (ADR-0001 d.1). Nothing
    stops them being added back except this: a deployment still passing either
    is told rather than obeyed.

    The parser is asked directly, so the refusal is a `SystemExit` caught
    here — no subprocess, and this process goes on. What is asserted after it
    is that the parser has no such argument, and not what it printed: the
    usage line names every option the parser does know, so a flag re-added
    without a value of its own would turn the value away, print the word, and
    satisfy a test that read stderr.
    """
    parser = command_line()

    with pytest.raises(SystemExit) as refused:
        parser.parse_args([*STARTED, gone, value])

    assert refused.value.code != 0
    assert gone.removeprefix("--") not in parser.parse_args(STARTED)


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


async def unreachable(url: str) -> bytes:
    """What fetches a URL here, and never does: nothing in the gate reaches a
    release API, and nothing in this file asks the face what a source
    carries."""
    raise AssertionError(f"the gate reached {url}")


def served(port: int = 0) -> Server:
    """The face on an OS-chosen port, which is what the loop is handed."""
    return Server(Face(fetch=unreachable), port, log=lambda line: None)


class Unserved(Server):
    """A face that cannot serve: `start()` raises where binding a port that
    something else already has raises."""

    def __init__(self) -> None:
        super().__init__(Face(fetch=unreachable), FACE_PORT, log=lambda line: None)

    async def start(self) -> None:
        raise OSError(errno.EADDRINUSE, "address already in use")


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
            mirroring(station, quiet(station), served(), stop, PERIOD_S)
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
            mirroring(station, quiet(station), served(), stop, PERIOD_S)
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
        looping = asyncio.create_task(
            mirroring(station, flasher, served(), stop, PERIOD_S)
        )
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


def test_the_face_is_served_while_the_mirror_is() -> None:
    """The face is up for as long as the app is, and the port goes back when
    the app ends: it is one more thing in the process that holds the device,
    and a port left bound by an app that has stopped is what the next start
    of it cannot get past (#526)."""

    async def serving() -> int:
        station = Endless()
        face = served()
        stop = threading.Event()
        looping = asyncio.create_task(
            mirroring(station, quiet(station), face, stop, PERIOD_S)
        )
        await asyncio.sleep(TURNS * PERIOD_S)
        port = face.port
        _, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.close()
        await writer.wait_closed()
        stop.set()
        await looping
        return port

    port = asyncio.run(asyncio.wait_for(serving(), TIMEOUT_S))
    with socket.socket() as free:
        free.bind((HOST, port))  # nothing holds it, so the next start gets it


def test_a_face_that_cannot_serve_ends_the_loop() -> None:
    """The mirror's own rule, applied to the face: an app whose face nobody
    can reach is not an app the UI has, so it ends rather than staying up
    half served, and `restart: unless-stopped` gets its turn."""

    async def refused() -> Endless:
        station = Endless()
        stop = threading.Event()
        looping = asyncio.create_task(
            mirroring(station, quiet(station), Unserved(), stop, PERIOD_S)
        )
        ended, _ = await asyncio.wait({looping}, timeout=TIMEOUT_S)
        assert ended, "the loop went round with no face behind it"
        await looping
        return station

    with pytest.raises(OSError) as carried:
        asyncio.run(refused())
    assert carried.value.errno == errno.EADDRINUSE
