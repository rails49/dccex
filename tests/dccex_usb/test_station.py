"""Tests at the mirror seam, with a pty standing in for the command station.

The app opens the pty's slave by name, exactly as it opens `/dev/dccex`, and
the test is the device on the master side. Nothing here needs a command
station: what is asserted is the mirror — framing, fan-out, and what a client
gets while the device is away — and none of that is DCC-EX (#217).

The suite has no asyncio plugin, so each test is a coroutine handed to
`asyncio.run`, and the injected log is what the test waits on: the app says
`serial open` when it has the device, which is the only moment from which a
client's message is expected to arrive.
"""

import asyncio
import os
import socket
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from dccex_usb.station import READ_SIZE, Device, DeviceGone, Station

SETTLE_S = 0.2
TIMEOUT_S = 5.0


class Pty:
    """A pty standing in for the device: the app opens `path`, the test is `master`."""

    def __init__(self) -> None:
        self.master, self._slave = os.openpty()
        self.path = os.ttyname(self._slave)
        os.set_blocking(self.master, False)
        self._open = True

    def close(self) -> None:
        """Pull the cable. Idempotent, so a test may do it before the fixture."""
        if not self._open:
            return
        self._open = False
        os.close(self.master)
        os.close(self._slave)


class Log:
    """The injected log, and the test's window onto what the app is doing."""

    def __init__(self) -> None:
        self.lines: list[str] = []
        self.times: list[float] = []
        self._appended = asyncio.Event()

    def __call__(self, line: str) -> None:
        self.lines.append(line)
        self.times.append(time.monotonic())
        self._appended.set()

    def said(self, prefix: str) -> list[float]:
        """When each line starting with `prefix` was said, in order."""
        return [
            at for at, line in zip(self.times, self.lines) if line.startswith(prefix)
        ]

    async def wait_for(self, prefix: str, timeout: float = TIMEOUT_S) -> str:
        deadline = time.monotonic() + timeout
        while True:
            self._appended.clear()
            for line in self.lines:
                if line.startswith(prefix):
                    return line
            left = deadline - time.monotonic()
            if left <= 0:
                raise AssertionError(f"no log line {prefix!r} in {self.lines}")
            await asyncio.wait_for(self._appended.wait(), left)

    async def wait_for_count(
        self, prefix: str, count: int, timeout: float = TIMEOUT_S
    ) -> None:
        """Wait until `prefix` has been said `count` times."""
        deadline = time.monotonic() + timeout
        while len(self.said(prefix)) < count:
            self._appended.clear()
            if len(self.said(prefix)) >= count:
                return
            left = deadline - time.monotonic()
            if left <= 0:
                raise AssertionError(
                    f"{prefix!r} said {len(self.said(prefix))} times, not {count},"
                    f" in {self.lines}"
                )
            await asyncio.wait_for(self._appended.wait(), left)


@pytest.fixture
def pty() -> Iterator[Pty]:
    device = Pty()
    yield device
    device.close()


BEHIND_BYTES = 4096

UNREACHABLE_BYTES = 1 << 24
"""A bound on a client no test reaches, for the tests about a client that has
stopped reading and is *not* to be cut off: what they are about is the other
paths a client leaves by, and the cut-off already handles this client."""

WEDGED_BYTES = 8 * 1024 * 1024
"""Enough said at a client that takes nothing to leave the app holding some.

The kernels either side take a megabyte or two of a stream nobody reads and
then stop; everything after that is the app's own buffer, which is what a
polite close waits to drain and never does. Several times the kernels' share,
because how much that is belongs to the machine the gate runs on."""

SHUTDOWN_S = 2.0
"""What bounded means for a shutdown here: long enough not to call a loaded
machine a hang, short enough not to call a hang slow."""

QUICK_BACKOFF_S = 0.005
PATIENT_BACKOFF_S = 0.2
"""A backoff a test can act inside: the grace is two of it, so a test that
has to speak to an away device before its clients are dropped asks for this
one and still finishes in under a second."""

PATIENT_GRACE_S = 2 * PATIENT_BACKOFF_S
"""The grace at that backoff: two reopens of it, which is what GRACE_REOPENS
counts."""


def station(
    device: str,
    log: Log,
    *,
    backoff_s: float = QUICK_BACKOFF_S,
    max_outstanding_bytes: int = BEHIND_BYTES,
) -> Station:
    """A station on an OS-chosen port, with outages measured in milliseconds.

    A client falls behind in kilobytes rather than the megabyte of the real
    bound, so a test can put one behind by not reading for a moment. The
    backoff is the grace as well — two reopens of it — so an outage is over,
    and the clients of one are gone, in milliseconds too.
    """
    return Station(
        device,
        0,
        log=log,
        first_backoff_s=backoff_s,
        max_backoff_s=4 * backoff_s,
        max_outstanding_bytes=max_outstanding_bytes,
    )


async def connect(app: Station) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    return await asyncio.open_connection("127.0.0.1", app.port)


async def connect_deaf(
    app: Station,
) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    """A client that will never be read from, and cannot take much unread.

    Its receive buffer is set small before it connects, so the kernels either
    side hold kilobytes rather than the megabytes they will size themselves
    up to on loopback. What the app sees is the same client either way — one
    that stops taking bytes — reached in a fraction of the traffic.
    """
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2048)
    sock.setblocking(False)
    await asyncio.get_running_loop().sock_connect(sock, ("127.0.0.1", app.port))
    return await asyncio.open_connection(sock=sock)


async def send(writer: asyncio.StreamWriter, data: bytes) -> None:
    writer.write(data)
    await writer.drain()


async def arriving(fd: int, count: int, timeout: float = TIMEOUT_S) -> bytes:
    """Read from the device side until `count` bytes are there, or time runs out."""
    got = b""
    deadline = time.monotonic() + timeout
    while len(got) < count and time.monotonic() < deadline:
        try:
            got += os.read(fd, 4096)
        except BlockingIOError:
            await asyncio.sleep(0.005)
    return got


async def nothing_arriving(fd: int) -> bytes:
    """What reaches the device side while nothing is supposed to."""
    await asyncio.sleep(SETTLE_S)
    try:
        return os.read(fd, 4096)
    except BlockingIOError:
        return b""


def open_fds() -> int:
    """How many descriptors this process holds."""
    return len(os.listdir("/dev/fd"))


class Talking:
    """The device saying more than a client can take, and a record of it.

    Every chunk names the offset it starts at, so what a client heard can be
    compared with what was said and a gap in the middle cannot pass for the
    whole stream.
    """

    def __init__(self, fd: int) -> None:
        self._fd = fd
        self.said = bytearray()

    async def run(self) -> None:
        while True:
            chunk = f"<p{len(self.said)}>".encode().ljust(64, b".")
            rest = memoryview(chunk)
            while rest:
                try:
                    written = os.write(self._fd, rest)
                except BlockingIOError:
                    await asyncio.sleep(0.001)
                    continue
                self.said += rest[:written]
                rest = rest[written:]
            await asyncio.sleep(0)


class Listening:
    """A client that keeps reading, and everything it has heard."""

    def __init__(self, reader: asyncio.StreamReader) -> None:
        self._reader = reader
        self.heard = bytearray()

    async def run(self) -> None:
        while True:
            arrived = await self._reader.read(READ_SIZE)
            if not arrived:
                return
            self.heard += arrived

    async def hears(self, count: int, timeout: float = TIMEOUT_S) -> None:
        deadline = time.monotonic() + timeout
        while len(self.heard) < count:
            if time.monotonic() > deadline:
                raise AssertionError(f"heard {len(self.heard)} bytes, not {count}")
            await asyncio.sleep(0.005)


async def released(held: int, timeout: float = TIMEOUT_S) -> int:
    """Wait for this process to be back down to `held` descriptors."""
    deadline = time.monotonic() + timeout
    while open_fds() > held and time.monotonic() < deadline:
        await asyncio.sleep(0.005)
    return open_fds()


async def wedge(pty: Pty, count: int = WEDGED_BYTES) -> None:
    """Say `count` bytes at a client that is taking none of them, and stop.

    What the app is left holding afterwards is the bytes it could not hand
    over, and the device is quiet again, so what happens next is the path
    under test rather than more traffic. Nothing reads what is said here, so
    it is bulk and not messages.
    """
    bulk = b"." * READ_SIZE
    said = 0
    while said < count:
        rest = memoryview(bulk)
        while rest:
            try:
                written = os.write(pty.master, rest)
            except BlockingIOError:
                await asyncio.sleep(0)
                continue
            said += written
            rest = rest[written:]


async def shut_down(app: Station) -> None:
    """Close the station, or say it did not rather than hang the suite."""
    await asyncio.wait_for(app.close(), SHUTDOWN_S)


def test_a_client_that_stops_reading_is_cut_off_and_its_bytes_released(
    pty: Pty,
) -> None:
    """The buffer for a client that takes nothing is not the railroad's to hold.

    Its descriptor going with it is what says the bytes went too: closing a
    connection waits for what is outstanding to be written, which for a
    client that never reads is forever, so a descriptor that is back is a
    buffer that was let go rather than one still waiting to drain.
    """

    async def scenario() -> None:
        log = Log()
        app = station(pty.path, log)
        await app.start()
        try:
            _, deaf = await connect_deaf(app)
            await log.wait_for("serial open")
            await asyncio.sleep(SETTLE_S)
            held = open_fds()
            device = asyncio.create_task(Talking(pty.master).run())
            try:
                line = await log.wait_for("client disconnected")
            finally:
                device.cancel()

            assert "too far behind" in line
            # The client's own socket is still open and still unread, so what
            # came back is the station's side of it.
            assert await released(held - 1) == held - 1
            deaf.close()
        finally:
            await app.close()

    asyncio.run(scenario())


def test_a_client_that_reads_hears_the_whole_stream_across_a_deaf_one(
    pty: Pty,
) -> None:
    """One client walking out of range costs the others nothing."""

    async def scenario() -> None:
        log = Log()
        app = station(pty.path, log)
        await app.start()
        try:
            reader, keeping_up = await connect(app)
            _, deaf = await connect_deaf(app)
            await log.wait_for("serial open")
            listening = Listening(reader)
            heard = asyncio.create_task(listening.run())
            talking = Talking(pty.master)
            device = asyncio.create_task(talking.run())
            try:
                assert "too far behind" in await log.wait_for("client disconnected")
            finally:
                device.cancel()
            await listening.hears(len(talking.said))

            assert bytes(listening.heard) == bytes(talking.said)
            # And the client that kept up was never the one cut off.
            assert len(log.said("client disconnected")) == 1

            heard.cancel()
            keeping_up.close()
            deaf.close()
        finally:
            await app.close()

    asyncio.run(scenario())


def test_two_clients_interleaved_produce_two_whole_messages(pty: Pty) -> None:
    async def scenario() -> None:
        log = Log()
        app = station(pty.path, log)
        await app.start()
        try:
            _, one = await connect(app)
            _, two = await connect(app)
            await log.wait_for("serial open")
            first, second = b"<t 3 50 1>", b"<a 12 1>"
            for at in range(max(len(first), len(second))):
                if at < len(first):
                    await send(one, first[at : at + 1])
                if at < len(second):
                    await send(two, second[at : at + 1])

            got = await arriving(pty.master, len(first) + len(second))

            assert got in (first + second, second + first)
        finally:
            await app.close()

    asyncio.run(scenario())


def test_a_serial_write_reaches_every_client(pty: Pty) -> None:
    async def scenario() -> None:
        log = Log()
        app = station(pty.path, log)
        await app.start()
        try:
            one, one_writer = await connect(app)
            two, two_writer = await connect(app)
            await log.wait_for("serial open")

            os.write(pty.master, b"<p1>")

            for client in (one, two):
                heard = await asyncio.wait_for(client.readexactly(4), TIMEOUT_S)
                assert heard == b"<p1>"
            one_writer.close()
            two_writer.close()
        finally:
            await app.close()

    asyncio.run(scenario())


def test_a_client_disconnecting_mid_message_leaves_the_device_untouched(
    pty: Pty,
) -> None:
    async def scenario() -> None:
        log = Log()
        app = station(pty.path, log)
        await app.start()
        try:
            _, writer = await connect(app)
            await log.wait_for("serial open")
            await send(writer, b"<t 3 50")

            writer.close()
            await log.wait_for("client disconnected")

            assert await nothing_arriving(pty.master) == b""
        finally:
            await app.close()

    asyncio.run(scenario())


def test_the_mirror_sends_the_device_nothing_a_client_did_not(pty: Pty) -> None:
    """Every byte the device is sent came from a client (ADR-0010).

    The readings on a page are made of what the station said, and on a box
    with no translator nothing asks the station to say anything — so the page
    polls, as a throttle does, and the mirror goes on originating nothing.
    The scenario is the app's whole life against a device that never goes
    away: the open, a client arriving, the station talking and being fanned
    out, a client typing, clients leaving, and the shutdown. The only bytes
    that ever reach the device are the one message a client sent.
    """

    async def scenario() -> None:
        log = Log()
        app = station(pty.path, log)
        await app.start()
        try:
            await log.wait_for("serial open")
            assert await nothing_arriving(pty.master) == b""

            reader, writer = await connect(app)
            os.write(pty.master, b"<iDCC-EX V-5.4.16 / ESP32 G-9db8d0e>")
            heard = await asyncio.wait_for(reader.readexactly(7), TIMEOUT_S)
            assert heard == b"<iDCC-E"
            assert await nothing_arriving(pty.master) == b""

            polled = b"<s>"
            await send(writer, polled)
            assert await arriving(pty.master, len(polled)) == polled

            writer.close()
            await log.wait_for("client disconnected")
            _, second = await connect(app)
            second.close()
            await log.wait_for_count("client disconnected", 2)
            assert await nothing_arriving(pty.master) == b""
        finally:
            await app.close()

        assert await nothing_arriving(pty.master) == b""

    asyncio.run(scenario())


def test_a_doubled_start_yields_one_message(pty: Pty) -> None:
    async def scenario() -> None:
        log = Log()
        app = station(pty.path, log)
        await app.start()
        try:
            _, writer = await connect(app)
            await log.wait_for("serial open")

            await send(writer, b"<<t 3 0 1>")

            assert await arriving(pty.master, len(b"<t 3 0 1>")) == b"<t 3 0 1>"
            assert await nothing_arriving(pty.master) == b""
        finally:
            await app.close()

    asyncio.run(scenario())


def test_what_a_client_sends_while_the_device_is_away_is_dropped(
    pty: Pty, tmp_path: Path
) -> None:
    """The device appears only after the client has spoken, and hears nothing of it.

    The client here connects to an outage already past its grace, whose
    clients are gone, so the grace it meets is the one its own arrival starts.
    What it meets meanwhile is the outage itself: its bytes dropped, because a
    command is honored now or ignored.
    """

    async def scenario() -> None:
        log = Log()
        absent = tmp_path / "dccex"
        app = station(str(absent), log)
        await app.start()
        try:
            _, early = await connect(app)
            await log.wait_for("client disconnected")
            early.close()

            _, writer = await connect(app)
            await send(writer, b"<t 3 50 1>")
            await log.wait_for("device away")

            absent.symlink_to(pty.path)
            await log.wait_for("serial open")

            assert await nothing_arriving(pty.master) == b""

            # And the client is still connected, so what it sends now arrives.
            await send(writer, b"<a 12 1>")
            assert await arriving(pty.master, len(b"<a 12 1>")) == b"<a 12 1>"
        finally:
            await app.close()

    asyncio.run(scenario())


class Flapping(Station):
    """A station whose device session ends the moment the device is open.

    A real one is a command station that answers the open and then says
    nothing — the end of file the mirror reads as the device going away
    again. The watcher's pacing is what is under test, not the mirror.
    """

    async def _mirror(self, device: Device) -> bool:
        await asyncio.sleep(0)
        return False


def test_a_device_that_will_not_configure_keeps_the_watcher_retrying(
    pty: Pty, tmp_path: Path
) -> None:
    """A path that opens but is no tty is an outage like any other, not the end.

    Setting the line discipline on it raises `termios.error`, which is not an
    `OSError`. The watcher survives it, holds no descriptor from the attempt,
    and is still there to take the device when it appears.
    """

    async def scenario() -> None:
        log = Log()
        not_a_tty = tmp_path / "dccex"
        not_a_tty.write_bytes(b"")
        app = station(str(not_a_tty), log)
        await app.start()
        try:
            _, writer = await connect(app)
            await send(writer, b"<t 3 50 1>")
            await log.wait_for("device away")
            # And once the grace has taken the client with it and that has
            # settled, so what is counted is the watcher's descriptors.
            await log.wait_for("client disconnected")
            await asyncio.sleep(SETTLE_S)

            held = open_fds()
            await asyncio.sleep(SETTLE_S)
            assert open_fds() == held

            not_a_tty.unlink()
            not_a_tty.symlink_to(pty.path)
            await log.wait_for("serial open")
        finally:
            await app.close()

    asyncio.run(scenario())


def test_a_session_that_ends_at_once_waits_before_reopening(pty: Pty) -> None:
    """A device that is open and gone again is not reopened in a hot loop."""

    async def scenario() -> None:
        log = Log()
        backoff = 0.1
        app = Flapping(pty.path, 0, log=log, first_backoff_s=backoff, max_backoff_s=0.2)
        await app.start()
        try:
            await log.wait_for_count("serial open", 2)

            assert log.said("serial open")[1] - log.said("serial closed")[0] >= backoff
        finally:
            await app.close()

    asyncio.run(scenario())


def test_the_dropped_notice_is_said_again_in_a_later_outage(
    pty: Pty, tmp_path: Path
) -> None:
    """Each outage says it once: the second one is news as much as the first."""

    async def scenario() -> None:
        log = Log()
        cable = tmp_path / "dccex"
        app = station(str(cable), log, backoff_s=PATIENT_BACKOFF_S)
        await app.start()
        try:
            # A grace the test stays inside: the first outage is recovered
            # before it ends and the second is spoken into, so the one client
            # is still there to speak into each of them.
            _, writer = await connect(app)
            await send(writer, b"<t 3 50 1>")
            await log.wait_for_count("device away", 1)

            cable.symlink_to(pty.path)
            await log.wait_for("serial open")
            cable.unlink()
            pty.close()
            await log.wait_for("serial closed")

            await send(writer, b"<a 12 1>")

            await log.wait_for_count("device away", 2)
        finally:
            await app.close()

    asyncio.run(scenario())


def test_the_device_is_let_go_for_the_block_and_taken_back_after(pty: Pty) -> None:
    """The handover a flash needs: nothing of the mirror's is on the port
    while the block runs, and the device is open again after it (ADR-0065).

    What a client sees inside it is the ordinary outage — what it sends
    dropped, and its connection closed once the grace passes — because for
    that while the device genuinely is away, and a flash lasts tens of
    seconds. The flash path drops its clients by the rule every outage drops
    them by and has no rule of its own (ADR-0066).
    """

    async def scenario() -> None:
        log = Log()
        app = station(pty.path, log, backoff_s=PATIENT_BACKOFF_S)
        await app.start()
        try:
            _, writer = await connect(app)
            await log.wait_for("serial open")

            async with app.released():
                assert not app.held
                assert log.said("serial closed"), "the device is still open"

                await send(writer, b"<t 3 50 1>")
                await log.wait_for("device away")
                assert await nothing_arriving(pty.master) == b""

                await log.wait_for("client disconnected")
                writer.close()

            await log.wait_for_count("serial open", 2)
            assert app.held
            _, after = await connect(app)
            await send(after, b"<a 12 1>")
            assert await arriving(pty.master, len(b"<a 12 1>")) == b"<a 12 1>"
        finally:
            await app.close()

    asyncio.run(scenario())


def test_a_device_away_past_the_grace_disconnects_every_client(
    tmp_path: Path,
) -> None:
    """The outage this app is the one to report: the station is switched off,
    the cable is out, or the flash is running, and the reopens do not recover.

    A client cannot tell an away device from a quiet one, so one held through
    an outage is a translator publishing `device/link: up` over a railroad
    that cannot move. The socket closing is the whole signal: the translator's
    session ends the way it already ends and the row goes `down` (ADR-0066).

    Both clients here are on the outage before its grace begins, and both
    leave on the one deadline: the grace is the outage's, not each client's.
    """

    async def scenario() -> None:
        log = Log()
        absent = tmp_path / "dccex"
        app = station(str(absent), log)
        await app.start()
        try:
            one, first = await connect(app)
            two, second = await connect(app)

            assert await asyncio.wait_for(one.read(READ_SIZE), TIMEOUT_S) == b""
            assert await asyncio.wait_for(two.read(READ_SIZE), TIMEOUT_S) == b""

            await log.wait_for_count("client disconnected", 2)
            first.close()
            second.close()
        finally:
            await app.close()

    asyncio.run(scenario())


def test_a_client_that_takes_nothing_leaves_when_the_grace_ends_too(
    pty: Pty, tmp_path: Path
) -> None:
    """The grace ends every client on the outage, reading or not.

    The socket closing is the whole signal that the device is away
    (ADR-0066), and a client that has stopped reading is the one that most
    needs telling — a sleeping laptop wakes to a session it thinks is live.
    Closing it politely waits for bytes it is not taking, so the signal
    never reaches it and it lingers on a port with no device behind it until
    the device comes back and the traffic that follows puts it far enough
    behind to be cut off. It is aborted instead, and the line saying how
    many clients the grace is ending counts one that it ends.
    """

    async def scenario() -> None:
        log = Log()
        cable = tmp_path / "dccex"
        cable.symlink_to(pty.path)
        app = station(str(cable), log, max_outstanding_bytes=UNREACHABLE_BYTES)
        await app.start()
        try:
            _, deaf = await connect_deaf(app)
            await log.wait_for("serial open")
            await wedge(pty)

            cable.unlink()
            pty.close()
            await log.wait_for("serial closed")

            assert "disconnecting 1 clients" in await log.wait_for("device still away")
            # And it went because the grace ended, not because it was cut
            # off: the bound on how far behind it may fall is out of reach.
            assert "too far behind" not in await log.wait_for("client disconnected")
            deaf.close()
        finally:
            await shut_down(app)

    asyncio.run(scenario())


def test_a_client_arriving_into_a_running_grace_leaves_with_it(
    tmp_path: Path,
) -> None:
    """The grace is the outage's, not each client's (ADR-0066).

    The late client here arrives half a grace into one already being waited
    out, and is disconnected on that deadline rather than on one of its own:
    it lives the remainder. A grace per client would keep it a full one past
    its arrival, which is what the margin below separates.
    """

    async def scenario() -> None:
        log = Log()
        absent = tmp_path / "dccex"
        app = station(str(absent), log, backoff_s=PATIENT_BACKOFF_S)
        await app.start()
        try:
            early, first = await connect(app)
            # The grace starts where this line is said, so the sleep under it
            # is measured from the grace and not from the connect.
            await log.wait_for("client connected")
            await asyncio.sleep(PATIENT_GRACE_S / 2)

            late, second = await connect(app)
            joined = time.monotonic()

            assert await asyncio.wait_for(late.read(READ_SIZE), TIMEOUT_S) == b""
            assert await asyncio.wait_for(early.read(READ_SIZE), TIMEOUT_S) == b""
            await log.wait_for_count("client disconnected", 2)

            lived = max(log.said("client disconnected")) - joined
            assert lived < 0.75 * PATIENT_GRACE_S, lived
            first.close()
            second.close()
        finally:
            await app.close()

    asyncio.run(scenario())


def test_a_device_back_inside_the_first_reopen_keeps_its_clients(
    pty: Pty, tmp_path: Path
) -> None:
    """What the grace is for: a blip costs no throttle a reconnect.

    The device goes and is back before the watcher has asked for it twice —
    a USB stutter, not a station switched off — and what a client notices is
    what it has always noticed, that a command sent meanwhile did nothing.
    """

    async def scenario() -> None:
        log = Log()
        cable = tmp_path / "dccex"
        cable.symlink_to(pty.path)
        app = station(str(cable), log, backoff_s=PATIENT_BACKOFF_S)
        await app.start()
        again = Pty()
        try:
            _, writer = await connect(app)
            await log.wait_for("serial open")

            cable.unlink()
            pty.close()
            await log.wait_for("serial closed")
            cable.symlink_to(again.path)
            await log.wait_for_count("serial open", 2)

            assert log.said("client disconnected") == []
            await send(writer, b"<a 12 1>")
            assert await arriving(again.master, len(b"<a 12 1>")) == b"<a 12 1>"
        finally:
            await app.close()
            again.close()

    asyncio.run(scenario())


def test_closing_returns_with_a_client_that_takes_nothing(pty: Pty) -> None:
    """Shutting the mirror down is not a wedged client's to hold up.

    A client that has stopped reading is holding bytes the app cannot hand
    over, and closing its stream politely is a wait for them to drain, which
    for this client never comes. Its handler would never return, the server
    waits for every handler, and the app would sit there until something
    killed it. It is aborted instead, the way `_cut_off` aborts.
    """

    async def scenario() -> None:
        log = Log()
        app = station(pty.path, log, max_outstanding_bytes=UNREACHABLE_BYTES)
        await app.start()
        try:
            _, deaf = await connect_deaf(app)
            await log.wait_for("serial open")
            await wedge(pty)

            await shut_down(app)

            # And it left by the shutdown rather than by the cut-off, which
            # the raised bound has put out of reach.
            assert "too far behind" not in await log.wait_for("client disconnected")
            deaf.close()
        finally:
            await shut_down(app)

    asyncio.run(scenario())


def test_the_device_is_let_go_though_a_client_takes_nothing(pty: Pty) -> None:
    """A client that stopped reading does not get to hold the cable.

    The watcher is stopped after the clients are, so a shutdown that waits
    on one of them to drain holds the device for the whole of that wait.
    What that costs in the field is the box taking a SIGTERM and the station
    still being held when the supervisor gives up on it.
    """

    async def scenario() -> None:
        log = Log()
        app = station(pty.path, log, max_outstanding_bytes=UNREACHABLE_BYTES)
        await app.start()
        try:
            _, deaf = await connect_deaf(app)
            await log.wait_for("serial open")
            await wedge(pty)
            held = open_fds()

            await shut_down(app)

            assert not app.held
            assert log.said("serial closed")
            # The three the app was holding: the device, the port it served
            # it on, and its end of the client's socket. The client's own
            # end is the test's and is still open and still unread.
            assert await released(held - 3) == held - 3
            deaf.close()
        finally:
            await shut_down(app)

    asyncio.run(scenario())


def test_a_client_that_leaves_with_bytes_it_never_took_is_aborted_too(
    pty: Pty,
) -> None:
    """The path every client leaves by, and the only one it walks itself.

    Half a close: the client shuts its write side, which is the handler's
    read returning nothing and the end of its loop, and it never takes the
    bytes the app is still holding for it — a throttle whose window went
    away with the station still talking at it. Closing its stream politely
    is a wait for those bytes to drain, which this client is not there to
    do, so the handler would never return, and a server that waits for
    every handler would never close. It is aborted instead, as at the three
    other places a client is dropped.
    """

    async def scenario() -> None:
        log = Log()
        app = station(pty.path, log, max_outstanding_bytes=UNREACHABLE_BYTES)
        await app.start()
        try:
            _, deaf = await connect_deaf(app)
            await log.wait_for("serial open")
            await wedge(pty)
            held = open_fds()

            deaf.write_eof()

            # It left by its own handler rather than by the cut-off, which
            # the raised bound has put out of reach.
            assert "too far behind" not in await log.wait_for("client disconnected")
            # The station's end of the socket is back while the client's own
            # is still open and still unread, so the bytes it was holding
            # went with it — which a polite close would still be waiting to
            # hand over.
            assert await released(held - 1) == held - 1
            # And the handler is not still running: the server does not
            # return while one is, and this client is off the set `close()`
            # aborts, so nothing after it would rescue a polite close here.
            await shut_down(app)
            deaf.close()
        finally:
            await shut_down(app)

    asyncio.run(scenario())


class Peeking(Station):
    """A station that hands out the device it holds, which a mirror does not.

    A test needs the device itself and not only the station's view of it:
    what it asks about a stranded write it has to go on asking after the
    handover has taken the device off the station, and `Station.held` says
    only that there is no device now. So the object is captured while it is
    open and questioned afterwards, which is also the only way to ask about
    the descriptor it let go.
    """

    @property
    def device(self) -> Device:
        assert self._open is not None, "the device is not open"
        return self._open


def parking(device: str, log: Log) -> Peeking:
    """A station whose grace is long enough to park a write inside."""
    return Peeking(
        device,
        0,
        log=log,
        first_backoff_s=PATIENT_BACKOFF_S,
        max_backoff_s=4 * PATIENT_BACKOFF_S,
    )


async def park_a_write(device: Device, writer: asyncio.StreamWriter) -> None:
    """Send whole messages until one of them is parked on the device.

    Ordinary messages and a handful of them, not one large one: a pty holds
    about a kilobyte unread and `framing.MAX_MESSAGE` is 1024, so a single
    big message is discarded by the framing before it is ever written and
    parks nothing. Nothing reads the device side in these tests, so once its
    buffer is full it stays full, and a write that is parked stays parked.
    """
    message = b"<" + b"t" * 998 + b">"
    deadline = time.monotonic() + TIMEOUT_S
    while not device.busy:
        if time.monotonic() > deadline:
            raise AssertionError("no write parked on the device")
        await send(writer, message * 4)
        await asyncio.sleep(0.005)
    # Busy, and still busy a moment later: a lock caught between two
    # messages is not a write waiting on a device that will never take more.
    await asyncio.sleep(SETTLE_S)
    assert device.busy, "the write went through rather than parking"


async def drained(fd: int) -> None:
    """Read the device side empty: what is there is the abandoned write's."""
    await asyncio.sleep(SETTLE_S)
    while True:
        try:
            if not os.read(fd, READ_SIZE):
                return
        except OSError:
            return


def nothing_registered(fd: int) -> bool:
    """Whether the loop has no writer on `fd`, which is what removing one says."""
    return asyncio.get_running_loop().remove_writer(fd) is False


def test_a_write_parked_on_the_device_is_let_go_with_it(pty: Pty) -> None:
    """The handover cannot strand a message that was being written.

    A client's message parked on a device taking no more held the write lock
    across an await that letting the device go never resolved: the descriptor
    was closed underneath the waiter and the selector dropped it silently, so
    that handler waited for ever holding the lock and every client's message
    after it waited behind that. The flash handover is the path this is on.

    What the message gets instead is the answer any message sent into an
    outage gets: it is dropped, the client stays connected, and the lock is
    free by the time the handover returns.
    """

    async def scenario() -> None:
        log = Log()
        app = parking(pty.path, log)
        await app.start()
        try:
            _, writer = await connect(app)
            await log.wait_for("serial open")
            device = app.device
            fd = device.number
            await park_a_write(device, writer)

            async with app.released():
                assert not device.busy, "the handover stranded the write"
                assert device.gone, "the handover left the device open"
                # And nothing of the mirror's is registered on the descriptor
                # it no longer owns: the number is the OS's to hand out
                # again, and a callback left on it is another owner's to lose.
                assert nothing_registered(fd)

            await log.wait_for_count("serial open", 2)
            await drained(pty.master)

            # And the mirror is forwarding again, for a client that was not
            # the one whose write was dropped.
            _, after = await connect(app)
            await send(after, b"<a 12 1>")
            assert await arriving(pty.master, len(b"<a 12 1>")) == b"<a 12 1>"
            writer.close()
            after.close()
        finally:
            await shut_down(app)

    asyncio.run(scenario())


def test_a_write_parked_on_the_device_is_let_go_when_the_cable_goes(
    pty: Pty, tmp_path: Path
) -> None:
    """The same for the ordinary outage: the cable out from under a write.

    This one pins the end state rather than reproducing the hang. A pty whose
    master is closed wakes the writer registered on its slave, so the parked
    write here fails on `EIO` and gives the lock back with the fix taken out
    as well as with it; the handover above is the regression test. What this
    holds is that the outage ends the same way — the lock free, nothing
    parked, nothing registered on the descriptor that has gone — and that a
    client's message reaches the device the watcher takes back.
    """

    async def scenario() -> None:
        log = Log()
        cable = tmp_path / "dccex"
        cable.symlink_to(pty.path)
        app = parking(str(cable), log)
        await app.start()
        back = Pty()
        try:
            _, writer = await connect(app)
            await log.wait_for("serial open")
            device = app.device
            fd = device.number
            await park_a_write(device, writer)

            cable.unlink()
            pty.close()
            await log.wait_for("device away")

            assert not device.busy, "the outage stranded the write"
            assert device.gone, "the outage left the device open"
            assert nothing_registered(fd)

            cable.symlink_to(back.path)
            await log.wait_for_count("serial open", 2)

            _, after = await connect(app)
            await send(after, b"<a 12 1>")
            assert await arriving(back.master, len(b"<a 12 1>")) == b"<a 12 1>"
            writer.close()
            after.close()
        finally:
            back.close()
            await shut_down(app)

    asyncio.run(scenario())


class Watching(Station):
    """A station that says whether a watcher is running, which a mirror does not.

    Nobody outside asks — the watcher is how the device is kept open and no
    caller has a question it answers — so the test reaches it from a subclass
    here rather than having the class publish it.
    """

    @property
    def watcher(self) -> asyncio.Task[None] | None:
        return self._watcher


def watched(device: str, log: Log) -> Watching:
    """A station that would take the device back at once, if it took it back.

    The backoff is the quick one and `_watch()` opens before it waits, so a
    watcher this test says should not exist has said `serial open` again
    within a settle if it does.
    """
    return Watching(
        device,
        0,
        log=log,
        first_backoff_s=QUICK_BACKOFF_S,
        max_backoff_s=4 * QUICK_BACKOFF_S,
    )


def test_a_handover_that_ends_on_a_closed_station_takes_no_device_back(
    pty: Pty,
) -> None:
    """A station closed while the device is let go does not take it back.

    Reachable on SIGTERM mid-flash: a flash in flight is shielded, so the
    supervising coroutine swallows the cancellation, cancels the mirror and
    lets `close()` run while the flash is still inside the handover. The
    handover's exit then started a fresh watcher, which reopens and holds the
    serial device of a station nobody is using. Nothing said it should not:
    the event loop's own task cleanup happened to cancel that watcher, which
    made a held device a leak instead, and the next change to teardown was
    free to turn it back.

    So the station knows it has been closed, and a handover that ends on a
    closed station leaves the device alone: no watcher, and the device not
    opened a second time.
    """

    async def scenario() -> None:
        log = Log()
        app = watched(pty.path, log)
        await app.start()
        try:
            await log.wait_for("serial open")

            async with app.released():
                assert not app.held, "the handover left the device open"
                await shut_down(app)

            assert app.watcher is None, "a closed station started a watcher"
            # And it stays that way: a watcher started here would have the
            # device back within a backoff, because opening is the first
            # thing it does.
            await asyncio.sleep(SETTLE_S)
            assert app.watcher is None, "a closed station started a watcher"
            assert not app.held, "the device was taken back by a closed station"
            assert len(log.said("serial open")) == 1, "the device was reopened"
        finally:
            await shut_down(app)

    asyncio.run(scenario())


class Woken(Device):
    """A device whose parked write can be woken the way the selector wakes it.

    Waking is `set_result` on the future the write is parked on, and it is
    all the selector does: the write does not resume until the loop gets to
    it, which is a turn later. A test that wants the moment in between has to
    make it, because the real selector only obliges when the device happens
    to find room in the same turn the device goes.
    """

    @property
    def parked(self) -> bool:
        return bool(self._waiters)

    def wake_parked(self) -> None:
        for ready in tuple(self._waiters):
            if not ready.done():
                ready.set_result(None)


def test_a_write_woken_as_the_device_goes_does_not_write_into_the_number(
    pty: Pty,
) -> None:
    """Being woken is not being owed the descriptor.

    A write parked on a full device is woken by the selector the moment the
    device has room. It does not resume there and then — that is a turn of
    the loop away — so a handover starting in between found a write already
    woken, and the teardown that asked `done()` before speaking to a waiter
    passed it over and closed the descriptor under it. What the write then
    saw was an ordinary wake: no exception had arrived, so it took the number
    for its own, unregistered a writer from it and wrote a client's command
    bytes into whatever the OS had handed it to next, while reporting the
    message sent.

    So what it was woken by decides nothing. It asks the device whether the
    descriptor is still the device's, and a device that has been let go says
    no however the wake arrived.
    """

    async def scenario() -> None:
        device = Woken.open(pty.path)
        fd = device.number
        message = b"<" + b"t" * 998 + b">"

        # Filled until one write parks, rather than in one write of a size
        # chosen here: how much a pty holds unread is the system's business
        # and a Linux one holds several times what a macOS one does. Nothing
        # reads the device side, so what goes in stays in and each write
        # brings the next closer to parking. They queue on the write lock,
        # so the one that parks is the only one on the device.
        writes: list[asyncio.Task[None]] = []
        deadline = time.monotonic() + TIMEOUT_S
        while not device.parked:
            if time.monotonic() > deadline:
                raise AssertionError("no write parked on the device")
            writes.append(asyncio.create_task(device.write(message * 4)))
            await asyncio.sleep(0.005)

        # The device has found room and the write is woken. Its turn has not
        # come, and the device goes before it does.
        device.wake_parked()
        device.let_go()

        ended = await asyncio.gather(*writes, return_exceptions=True)
        refused = [end for end in ended if isinstance(end, BaseException)]
        assert refused, "nothing was refused, so nothing was parked"
        assert all(isinstance(end, DeviceGone) for end in refused), refused
        assert device.gone
        assert not device.busy, "the woken write was left holding the device"
        assert nothing_registered(fd), "a writer was left on the descriptor"

    asyncio.run(scenario())


def test_letting_the_device_go_ends_the_read_side_too(pty: Pty) -> None:
    """Nothing survives `let_go`, the session's own wait included.

    The read side waits for the device to stop sending, and what notices that
    is the callback `let_go` has just taken off the loop. So the one wait
    nothing else can end is the one the device itself is holding: woken here,
    or parked for as long as the process lives.

    The mirror does not reach it — its watcher lets the device go only after
    the session has returned — which is the reason to hold it shut here. What
    the class says about `let_go` is that it is total, and a caller reading
    that is owed it on the path the mirror does not happen to take.
    """

    async def scenario() -> None:
        device = Device.open(pty.path)
        reading = asyncio.create_task(device.until_gone(lambda arrived: None))
        await asyncio.sleep(SETTLE_S)
        assert not reading.done(), "the session ended before the device went"

        device.let_go()

        spoke = await asyncio.wait_for(reading, TIMEOUT_S)
        assert not spoke, "the device was never read from"
        assert device.gone
        assert not device.busy

    asyncio.run(scenario())
