"""The command station's serial device, mirrored on a TCP port.

The command station is reached over USB only and one process can own the
device, so that process is this app and everything else is a client of the
port it serves (ADR-0043): the translator, JMRI, hand-held throttles. They
coexist, and DecoderPro keeps working with every app of ours down.

It is a mirror, not a protocol. Every byte read from the device is written to
every connected client unchanged, because one serial stream cannot say who
asked — a reply to one client and a broadcast to all look alike on it. The
only reading it does is `<` and `>`, and only the other way: a client's bytes
are held until its message is whole and then written in one write, so two
clients never interleave a command (framing.py). A client that goes away
mid-message takes its partial message with it.

**It originates nothing.** Every byte the device is sent came from a client —
not from opening the device, reopening it, shutting down, a client arriving, or
a timer, because there is none (ADR-0010). The readings on a page are made of
what the station said, and what asks the station to say it is the page, on its
own schedule, as a throttle would.

**A client that has stopped reading is cut off.** The fan-out is a write per
client with nobody waiting on it, so a client that never takes its bytes — a
sleeping laptop, a throttle whose Wi-Fi dropped — has them buffered for it
without limit until the process dies of it and every other client loses the
command station too. Once more than `MAX_OUTSTANDING_BYTES` is outstanding to
one, its connection is closed and the log says why. Not a bounded buffer that
discards: this direction is unframed, so dropping from the middle hands the
client half a message it reads as garbage, and not silence either: a peer that
has gone is reported rather than absorbed (ADR-0050). It may reconnect and
pick the live conversation up.

**While the device is away a client's messages are dropped**, not queued. A
command is honored now or ignored: a queue that flushes on reconnect is a
train that moves minutes after someone asked for it. Reopening the device is
this app's own business — it goes away when the command station is switched
off — so it retries with backoff, and a client notices only that what it
sent meanwhile did nothing. A message already being written when the device
goes is dropped the same way and at once: whatever is parked on the descriptor
is woken before it is closed, and a write that wakes asks the device whether
the number is still the device's rather than reading an answer into how it was
woken — so none is left parked for ever, and none writes into a number the OS
has handed to somebody else. Every way the device can fail to be there is the
same outage — a path that is not there, one that will not take the line
discipline, one that is gone again the moment it is open — and the watcher
outlives all of them.

**An outage that outlasts the grace takes the clients with it.** A client
cannot tell an away device from a quiet one, and this port has no way to
tell it: the socket closing is the whole signal, and it is the one that ends
the translator's session and lowers `device/link` (ADR-0066). So a device
still away two reopens in has every connected client disconnected. The
connection is aborted rather than closed politely — here, at the cut-off,
when the app itself is shutting down, and in the handler every client leaves
by however it came to go, which are the four places one is let go of:
closing waits for what is outstanding to reach the client first, so for the
client that has stopped reading the signal never arrives and the wait never
ends. The handler's is the abort a client that was reading meets, and it
costs that client nothing, or the tail of one fan-out it had not taken on
its way out. Inside the grace nothing changes — a blip the first reopen
recovers costs no throttle a reconnect, which is what the grace is for. The
grace is the outage's and not each client's: one that connects while an
outage is being waited out leaves with the rest, however briefly it has been
there, and one that connects after an outage has already taken its clients
starts the next grace and gets all of it.

There is no client limit beyond the OS's and no authentication: the LAN is
the trust boundary (ADR-0042), and the port is published to it by the
container. The server binds every interface for the same reason.

**The device is let go on demand and taken back after**, which is `released()`
and the one thing here that is not the mirror's own business: writing the
station's flash means owning the port, and the process holding it is the only
one that can hand it over (ADR-0065). What is done with it meanwhile is
`firmware.py`'s; this class still speaks no bus topic and reads no payload.
"""

import asyncio
import contextlib
import os
import sys
import termios
from collections.abc import AsyncGenerator, Callable
from typing import Self

from dccex_usb.framing import frame

# Every interface: the container publishes the port and JMRI reaches it by
# the service name, so what limits the reach is the LAN, not a bind address
# (ADR-0042). One socket rather than one per address family, so the port the
# OS chooses when asked for 0 is one port.
HOST = "0.0.0.0"

BAUD = termios.B115200
READ_SIZE = 4096

# Every way the device can be away. `termios.error` is not an `OSError`, and
# it is what a line-discipline call raises: unplugging the node between the
# open and that call reports ENODEV as one, and a path that is no tty raises
# it every time. Both are the device not being there, not the end of the app.
DEVICE_AWAY = (OSError, termios.error)

FIRST_BACKOFF_S = 0.5
MAX_BACKOFF_S = 8.0

# How long a client waits on an away device before it is disconnected, in
# reopens at the first backoff: about a second, past the first retry and far
# inside a flash. Counted off the backoff rather than kept as a number of its
# own, so there is one number here and not two that can drift apart
# (ADR-0066).
GRACE_REOPENS = 2

# How far behind a client may fall before it is cut off. The device speaks at
# 115200 baud, so this is a minute and a half of everything it has to say: a
# client that has taken none of it in that long is not reading at all, and the
# alternative to disconnecting it is buffering for it until the process dies.
MAX_OUTSTANDING_BYTES = 1 << 20


class DeviceGone(OSError):
    """The device a write was parked on was let go before it could finish.

    This module's own, and it does not leave it: a write raises it, and
    `_to_device` catches it where it already catches the device going away
    mid-message, because that is what this is. An `OSError` for that reason,
    and not a cancellation — cancelling the write would take the client's
    handler with it and disconnect a client that has done nothing wrong.
    """


def to_stderr(line: str) -> None:
    """The default log: connects, disconnects and the device, and nothing else."""
    print(line, file=sys.stderr, flush=True)


def configure(fd: int) -> None:
    """115200 8N1, raw: no echo, no line editing, no flow control.

    The whole line configuration is set rather than adjusted, so the device
    behaves the same however the last program that held it left the port.
    """
    cc = termios.tcgetattr(fd)[6]
    cc[termios.VMIN] = 1
    cc[termios.VTIME] = 0
    iflag = termios.IGNPAR
    oflag = 0
    cflag = termios.CS8 | termios.CLOCAL | termios.CREAD
    lflag = 0
    termios.tcsetattr(fd, termios.TCSANOW, [iflag, oflag, cflag, lflag, BAUD, BAUD, cc])


class Device:
    """The device open on `path`, and everything that depends on it being open.

    One descriptor, one of these, one lifetime: `open` makes it, `let_go`
    ends it, and it never opens again. Ownership is therefore a fact that can
    be read — `gone` — rather than a timing argument that has to be won. What
    is parked on the device asks this object whether the descriptor is still
    its own, and is told, however it came to be woken.

    The descriptor does not leave. Every `os.read`, `os.write`, `os.close`
    and every registration on the event loop is in here, so the question of
    whether the number is still ours is asked in the one place that knows the
    answer. A caller holds the device, not the number, and a device that has
    been let go refuses rather than writing into whatever the OS handed the
    number to next.
    """

    def __init__(self, path: str, fd: int) -> None:
        self._path = path
        self._fd: int | None = fd
        self._loop = asyncio.get_running_loop()
        # One writer at a time, so a message that takes more than one write
        # is still the only thing between the device and the previous `>`.
        self._writing = asyncio.Lock()
        # What is parked on the device having room for more. Held here
        # because letting the descriptor go is what they have to be woken
        # for, and this is what lets it go.
        self._waiters: set[asyncio.Future[None]] = set()
        # And the read side's wait, for the same reason: it ends when the
        # device stops sending, and being let go is one of the ways.
        self._gone: asyncio.Future[None] | None = None

    @classmethod
    def open(cls, path: str) -> Self:
        """Open the device raw at 115200 8N1, or raise because it is away.

        What it raises for an absent path and for one that will not take the
        line discipline is `DEVICE_AWAY`, because to the watcher they are the
        same outage.
        """
        fd = os.open(path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        try:
            configure(fd)
            # Constructing is inside too: it asks for the running loop, which
            # off one raises, and a descriptor nothing came back holding is a
            # descriptor nothing can close.
            return cls(path, fd)
        except BaseException:
            os.close(fd)
            raise

    @property
    def gone(self) -> bool:
        """Whether the descriptor has been let go, which is for good."""
        return self._fd is None

    @property
    def number(self) -> int:
        """The descriptor, to ask the event loop about — not to operate on.

        Held out for one reason: what `let_go` promises about a descriptor it
        has closed can only be checked against the number it had, and by then
        this device has forgotten it. Reading it is safe. Writing to it,
        closing it or registering on it from out here is the thing this class
        exists to make impossible, and one that has been let go raises rather
        than handing a number back.
        """
        if self._fd is None:
            raise self._was_let_go()
        return self._fd

    @property
    def busy(self) -> bool:
        """Whether a message is on its way to the device or parked on it.

        What `let_go` leaves is nothing parked, which is the thing that can
        wait for ever. The write itself gives the lock back as it unwinds, a
        turn of the loop later, so this is still true the moment `let_go`
        returns and false once the write has had its turn.
        """
        return self._writing.locked() or bool(self._waiters)

    async def write(self, data: bytes) -> None:
        """Write every byte, waiting for the device when it takes no more.

        One message at a time, so two clients never interleave a command.

        Raises `DeviceGone` if the device is let go first — while this was
        waiting its turn, or parked on the device having room. The rest of
        the message is not written, because there is nothing to write it to.
        """
        async with self._writing:
            rest = memoryview(data)
            while rest:
                fd = self._fd
                if fd is None:
                    raise self._was_let_go()
                try:
                    written = os.write(fd, rest)
                except BlockingIOError:
                    await self._writable(fd)
                    continue
                rest = rest[written:]

    async def until_gone(self, arrived: Callable[[bytes], None]) -> bool:
        """Hand every byte the device sends to `arrived`, until it goes away.

        Says whether the device spoke at all, which is what tells a session
        that ended from a device that was never really there.
        """
        fd = self._fd
        if fd is None:
            raise self._was_let_go()
        gone: asyncio.Future[None] = self._loop.create_future()
        self._gone = gone
        spoke = False

        def readable() -> None:
            nonlocal spoke
            try:
                sent = os.read(fd, READ_SIZE)
            except BlockingIOError:
                return
            except OSError:
                sent = b""
            if not sent:
                if not gone.done():
                    gone.set_result(None)
                return
            spoke = True
            arrived(sent)

        self._loop.add_reader(fd, readable)
        try:
            await gone
        finally:
            self._gone = None
            if self._fd is not None:
                self._loop.remove_reader(fd)
        return spoke

    def let_go(self) -> None:
        """Give the descriptor up, for good. Total, and safe to repeat.

        Ours stops being true first and the rest follows from it: the
        registrations come off while the number is still this device's, then
        everything parked on it is woken — the writes, and the read side's
        wait for the device to stop sending — then it is closed. After this
        returns nothing of this app's is on that descriptor and nothing is
        parked on it. What was woken unwinds a turn later, which is when
        `busy` goes false.

        What is woken is not told anything. It reads `gone` for itself, which
        is the one answer and the one place that gives it: waking a waiter
        does not resume it, so a write the selector woke a moment before this
        ran has its turn still to come, and it has to find the same answer as
        one woken here. Told by what arrived instead, it would find nothing
        wrong and go on to write into a number the OS had handed on.
        """
        fd, self._fd = self._fd, None
        if fd is None:
            return
        self._loop.remove_writer(fd)
        self._loop.remove_reader(fd)
        waiters, self._waiters = self._waiters, set()
        for ready in waiters:
            if not ready.done():
                ready.set_result(None)
        # The read side too. Its wait ends when the device stops sending,
        # which the callback that has just come off the loop is what notices:
        # nothing would notice this one, and the session would never end.
        if self._gone is not None and not self._gone.done():
            self._gone.set_result(None)
        os.close(fd)

    async def _writable(self, fd: int) -> None:
        """Wait for the device to take more, or for it to be let go.

        A descriptor that is closed is dropped from the selector without a
        word, so a wait nobody wakes is a wait that never ends: this joins
        `_waiters`, where `let_go` can reach it.
        """
        ready: asyncio.Future[None] = self._loop.create_future()

        def wake() -> None:
            if not ready.done():
                ready.set_result(None)

        self._loop.add_writer(fd, wake)
        self._waiters.add(ready)
        try:
            await ready
        finally:
            self._waiters.discard(ready)
            # Only while it is still ours: `let_go` takes the registration
            # off before it closes, and by now the number may be somebody
            # else's — removing a writer from it would unregister theirs.
            if self._fd is not None:
                self._loop.remove_writer(fd)
        if self._fd is None:
            raise self._was_let_go()

    def _was_let_go(self) -> DeviceGone:
        return DeviceGone(f"the device {self._path} was let go")


class Station:
    """The serial device on `device`, served on `port`.

    `run()` is the whole process. Tests drive the same thing through the
    `start()` / `close()` split, ask `port` which port the OS chose, and pass
    their own `log`, backoff bounds and bound on a client so an outage is over
    in milliseconds and a client falls behind in kilobytes.
    """

    def __init__(
        self,
        device: str,
        port: int,
        *,
        log: Callable[[str], None] = to_stderr,
        first_backoff_s: float = FIRST_BACKOFF_S,
        max_backoff_s: float = MAX_BACKOFF_S,
        max_outstanding_bytes: int = MAX_OUTSTANDING_BYTES,
    ) -> None:
        self._device = device
        self._port = port
        self._log = log
        self._first_backoff_s = first_backoff_s
        self._max_backoff_s = max_backoff_s
        self._max_outstanding_bytes = max_outstanding_bytes
        self._clients: set[asyncio.StreamWriter] = set()
        self._behind: set[asyncio.StreamWriter] = set()
        self._open: Device | None = None
        self._dropped = False
        self._grace: asyncio.Task[None] | None = None
        self._server: asyncio.Server | None = None
        self._watcher: asyncio.Task[None] | None = None
        # Whether `close()` has run, which is the one thing a handover asks
        # before it takes the device back. A field of its own rather than
        # `self._server is None`, which is also true of a station that was
        # never started: a field that means two things while reading as
        # though it meant one is what this is here to rule out.
        self._closed = False

    async def run(self) -> None:
        """Serve until cancelled — the whole of `python -m dccex_usb`."""
        await self.start()
        try:
            await self.serve_forever()
        finally:
            await self.close()

    async def start(self) -> None:
        """Bind the port and start watching for the device."""
        self._server = await asyncio.start_server(self._client, HOST, self._port)
        self._watcher = asyncio.create_task(self._watch())

    @property
    def port(self) -> int:
        """The port being served: the one the OS chose, when asked for 0."""
        return int(self._serving().sockets[0].getsockname()[1])

    @property
    def path(self) -> str:
        """The device this mirror was started on — the one a flash writes."""
        return self._device

    @property
    def held(self) -> bool:
        """Whether the device is open at this moment.

        The station is away for as long as it takes to come back — it is
        switched off, or the cable is out — and the mirror answers by
        dropping what clients send rather than by ending. What asks is a
        flash: writing a station that is not there is a refusal, and this is
        the question already being answered every time a client's message
        arrives.
        """
        return self._open is not None

    @contextlib.asynccontextmanager
    async def released(self) -> AsyncGenerator[None]:
        """Let the device go for the duration of the block, and take it back.

        The device is **closed before the block runs** and is reopened by the
        existing path after it, however the block ended: two openers fight
        over the line discipline and the reset lines, so a flash needs the
        mirror off the port entirely (ADR-0065).

        What clients see is an outage like any other — what they send is
        dropped, the app says so once (ADR-0050), and the grace disconnects
        them because a flash lasts tens of seconds — since for the length of
        it the device genuinely is away. The grace hangs off the device
        being closed rather than off the watcher, so this path needs no rule
        of its own. Taking it back is the watcher started again, so a station
        that is still rebooting is waited for on the ordinary backoff rather
        than specially.

        **A handover that ends on a closed station takes nothing back.**
        `close()` can run while the block is still going — a signal mid-flash
        cancels the mirror, and the flash it is inside is shielded from that
        cancellation — and a watcher started then reopens and holds the device
        of a station nobody is using. What kept that from being a held device
        was the event loop's own task cleanup cancelling the watcher on its
        way out, which nothing states and no change to teardown has to keep.
        """
        await self._stop_watching()
        try:
            yield
        finally:
            if not self._closed:
                self._watcher = asyncio.create_task(self._watch())

    async def serve_forever(self) -> None:
        await self._serving().serve_forever()

    async def close(self) -> None:
        """Stop serving, drop the clients and let the device go, for good.

        Closed is written down first and nothing here takes it back: this
        returns across several awaits, and a handover that finishes inside
        any of them has to find a station that is closed rather than one
        that is halfway through closing.
        """
        self._closed = True
        server, self._server = self._server, None
        if server is not None:
            server.close()
        # Aborted, and before waiting on the server: closing waits for what
        # is outstanding to reach a client, which for one that has stopped
        # reading is never, and the server does not return while a handler is
        # still running. Shutting down is `_cut_off`'s case — the bytes are
        # going nowhere — so it is `_cut_off`'s answer.
        for writer in tuple(self._clients):
            writer.transport.abort()
        if server is not None:
            await server.wait_closed()
        await self._stop_watching()
        self._stop_grace()

    async def _stop_watching(self) -> None:
        """End the watcher and come back with the device closed.

        Awaited rather than cancelled and left: the watcher closes the
        descriptor on its way out, so waiting for it is what makes "the
        device is let go" true by the time this returns — which is the
        ordering a flash depends on.
        """
        watcher, self._watcher = self._watcher, None
        if watcher is not None:
            watcher.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await watcher

    async def _client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """One connected client: its bytes framed, its partial message its own."""
        peer = writer.get_extra_info("peername")
        self._clients.add(writer)
        self._log(f"client connected {peer}")
        self._start_grace()
        partial = b""
        try:
            while True:
                arrived = await reader.read(READ_SIZE)
                if not arrived:
                    break
                partial, messages = frame(partial, arrived)
                for message in messages:
                    await self._to_device(message)
        except ConnectionError:
            pass
        finally:
            self._clients.discard(writer)
            cut_off = writer in self._behind
            self._behind.discard(writer)
            why = " too far behind" if cut_off else ""
            self._log(f"client disconnected {peer}{why}")
            # Aborted for the same reason, and waited for after: a handler
            # that waits on a client that is not reading is a handler the
            # server's `wait_closed()` waits on in its turn, and an abort is
            # the one wait that ends. What it costs is bytes a client that
            # has gone, or is being dropped, was never going to read.
            writer.transport.abort()
            with contextlib.suppress(ConnectionError):
                await writer.wait_closed()

    async def _to_device(self, message: bytes) -> None:
        """Write one whole message, or drop it because the device is away.

        The device is held rather than its descriptor number, so a message
        that waits its turn and finds the device let go meanwhile is refused
        by the device itself: there is no number here to re-identify, and
        none to write into by mistake once it has been handed on.
        """
        device = self._open
        if device is None:
            self._drop()
            return
        try:
            await device.write(message)
        except OSError:
            # The device went away mid-message — unplugged, or let go for a
            # flash, which wakes a parked write with `DeviceGone` rather than
            # leaving it on a descriptor being closed. The read side sees the
            # same thing and the watcher reopens it; this message is dropped
            # like anything else sent into an outage.
            self._drop()

    def _cut_off(self, writer: asyncio.StreamWriter) -> None:
        """Drop a client that has stopped reading, and its outstanding bytes with it.

        Aborted rather than closed, because closing waits for what is
        outstanding to reach the client and what got it here is a client that
        takes nothing: that wait is the very buffer being released. Its
        handler wakes on the abort and is where the disconnect is logged, so
        one client leaves by one path however it went.
        """
        self._clients.discard(writer)
        self._behind.add(writer)
        writer.transport.abort()

    def _drop(self) -> None:
        """One line per outage: after it, the outage is the news, not the loss."""
        if not self._dropped:
            self._dropped = True
            self._log(f"device away, dropping what clients send to {self._device}")

    def _start_grace(self) -> None:
        """Run the grace, where the device is away and there is a client on it.

        Started where the device goes away, and again where a client arrives
        to an outage with no grace running — the first client into one, or
        the first after a grace has already taken its clients. A client that
        arrives while one is running joins it and leaves on its deadline: the
        grace is the outage's, not the client's (ADR-0066). Nothing starts
        for an outage nobody is connected to: what the grace ends is
        connections, and there are none to end.
        """
        if self._grace is not None or self._open is not None or not self._clients:
            return
        self._grace = asyncio.create_task(self._disconnect_after_grace())

    def _stop_grace(self) -> None:
        """End the grace unrun: the device is open again, or the app is."""
        grace, self._grace = self._grace, None
        if grace is not None:
            grace.cancel()

    async def _disconnect_after_grace(self) -> None:
        """Wait out the grace and drop what is still connected.

        Aborted rather than closed, as in `_cut_off`: the socket closing is
        the whole signal that the device is away (ADR-0066), and a close
        waits for what is outstanding to drain first, which is a signal that
        never arrives for the client whose window is shut. What the abort
        costs is bytes from before an outage that has already outlasted its
        grace, to a client that is about to be told the device is gone.

        Each client leaves by its handler, which is where a disconnect is
        logged, so the line here says what this did and the lines under it
        say to whom — and it says it of clients that are all actually going.
        """
        await asyncio.sleep(GRACE_REOPENS * self._first_backoff_s)
        self._grace = None
        clients = tuple(self._clients)
        if not clients:
            return
        self._log(
            f"device still away, disconnecting {len(clients)} clients"
            f" of {self._device}"
        )
        for writer in clients:
            writer.transport.abort()

    async def _watch(self) -> None:
        """Keep the device open, retrying with backoff while it is away."""
        backoff = self._first_backoff_s
        while True:
            try:
                device = Device.open(self._device)
            except DEVICE_AWAY:
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, self._max_backoff_s)
                continue
            self._open = device
            self._stop_grace()
            self._log(f"serial open {self._device}")
            try:
                spoke = await self._mirror(device)
            finally:
                self._open = None
                # The outage that starts here is news again, however many
                # have been reported before it.
                self._dropped = False
                self._start_grace()
                device.let_go()
                self._log(f"serial closed {self._device}")
            # Opening is not proof the device is there: a session that ends
            # without a byte keeps the backoff it was reached with, and only
            # one that carried traffic starts over. Either way the next
            # attempt waits, because reopening a device that is gone again at
            # once is a hot loop with a log line per turn.
            if spoke:
                backoff = self._first_backoff_s
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, self._max_backoff_s)

    async def _mirror(self, device: Device) -> bool:
        """Fan what the device sends to every client, until it goes away.

        Says whether the device spoke at all, which is what tells a session
        that ended from a device that was never really there.

        One line, and a method of its own for the one reason: a test stands a
        whole device session in here, which leaves the watcher's pacing —
        the backoff, and what a session that carried nothing costs — under
        test without a device that has to misbehave on cue.
        """
        return await device.until_gone(self._fan_out)

    def _fan_out(self, arrived: bytes) -> None:
        """Every byte the device sent, to every client that is keeping up.

        Per client rather than per byte: nothing here can wait for a client
        to drain, so the one question a synchronous write can ask is whether
        this client is still keeping up.
        """
        for writer in tuple(self._clients):
            if writer.is_closing():
                continue
            if outstanding(writer) > self._max_outstanding_bytes:
                self._cut_off(writer)
                continue
            writer.write(arrived)

    def _serving(self) -> asyncio.Server:
        if self._server is None:
            raise RuntimeError("the station is not started")
        return self._server


def outstanding(writer: asyncio.StreamWriter) -> int:
    """How much has been written to a client that the OS has not taken yet.

    Asyncio counts it already, so this reads its count rather than keeping a
    second one that could disagree with it.
    """
    return writer.transport.get_write_buffer_size()
