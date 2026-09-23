"""Writing a released build onto the command station.

The firmware is built elsewhere, against the station's own source, and that
does not change; what this makes is the writing of a released build onto the
box something the running system does on a gesture, rather than something a
person does from a checkout (ADR-0065). The gesture names one thing, a `tag`,
and **this app is the only thing that can answer it**: flashing means owning
the serial port, the mirror holds it for as long as the railroad is up, and no
container can stop a sibling without handing a process the Docker daemon's
socket.

**Nothing outside this process can make the gesture.** It arrived on a bus in
`control` and it arrives at this app's own face now (ADR-0001, #13), which is
in this process and on this loop. `wanted` is the whole of the way in, and it
is a call: there is no topic, no second port and no command-line option that
reaches it.

**The gesture names a tag and never a source.** The LAN is the trust boundary
and carries no authentication on purpose (ADR-0042), so an ask that said where
to fetch from would let anyone on the wifi have the station fetch and run an
arbitrary binary. Where releases are read from is a flag on this app, and a tag
can only choose among the builds already published there. `latest` is not a tag
either: it names a different build depending on when it is read, and the point
of the gesture is to be able to say afterwards what was written.

**The order is the point.** The release is resolved, the binary fetched and
its digest checked *before* the device is let go. A network failure then costs
nothing, where the other order leaves the railroad with a closed port and no
firmware. esptool verifies what it wrote and not what was fetched, so the
digest the release API reports for the asset is what says the bytes are the
ones that were published.

**esptool is a subprocess with a timeout**, injected as a runner so the suite
substitutes a fake — nothing in the gate may need a command station, and the
suite's device is a pty, which esptool cannot flash. A subprocess is also what
keeps its failures off this process: it manipulates the port and exits on
error, and this is the process every throttle, DecoderPro and the translator
depend on being up.

**What became of the gesture is answered, and there is still no progress.**
`wanted` comes back with a `Wrote` — what it was refused for, or nothing where
the build was written, and the sentence that says which — so whoever asked is
told rather than sent to read a log on the box (ADR-0050). Every refusal is
still said on the box as well, because the device is the railroad's and what
was done to it is the box's record. What a flash is *doing* meanwhile is read
off the station itself and not from here: the link goes down while it is
written and comes back carrying the `build` it now reports.

**The refusals are this file's terms and not a protocol's.** A `Refusal` says
what went wrong with a station and a release; the status that carries it to a
caller is a fact about the way that caller asked, and belongs to whatever
answered them (`face.py`).

**A second gesture while a flash is in flight is refused, not queued.** A
command is honoured now or ignored, which is what this app already does with
what a client sends while the device is away; a queued flash is a station that
reboots minutes after somebody asked.
"""

import asyncio
import enum
import hashlib
import json
import tempfile
import urllib.error
import urllib.request
from collections.abc import Awaitable, Callable, Sequence
from contextlib import AbstractAsyncContextManager
from pathlib import Path
from typing import NamedTuple, Protocol, cast
from urllib.parse import quote

from dccex_usb.station import to_stderr

RELEASES = "https://api.github.com/repos/rails49/CommandStation-EX/releases"
"""Where releases are read from unless a box says otherwise: this
installation's fork of the command station's source, whose releases carry a
`firmware.bin` and a digest for it. Configuration rather than payload, which
is the whole of what keeps the gesture from naming what the station runs
(ADR-0042, ADR-0065)."""

ASSET = "firmware.bin"
"""The release asset that is written to the station."""

SHA256 = "sha256:"
"""The digest form the release API reports per asset, and the one form read
here. A digest in any other form checks nothing, so what it covers is refused
rather than written."""

CHIP = "esp32"
FLASH_BAUD = "460800"
FLASH_MODE = "dio"
FLASH_FREQ = "80m"
FLASH_SIZE = "4MB"
ADDRESS = "0x0"
"""The upload settings, which are the station core's own."""

LATEST = "latest"

TIMEOUT_S = 300.0
"""How long esptool is given before it is killed. Writing four megabytes at
460800 baud is a minute or two, and what this bounds is the other case: a tool
that has stopped talking to a station that has stopped answering, with the
mirror off the port for as long as it lasts."""

FETCH_S = 60.0
"""How long one fetch is given. Both of them happen before the device is let
go, so what this costs when it runs out is nothing but a refusal."""

ACCEPT = "application/vnd.github+json"

NO_SUCH = 404
"""The one answer from the release API that says the source carries no release
by that tag. Any other answer is the source failing to answer the question,
which is a different refusal (#46). Not a status this app replies with — that
is `face.py`'s — but the one it reads."""


class Asset(NamedTuple):
    """The firmware a release carries: where to fetch it, and the digest the
    API reports for it. The digest is empty where the API reports none, which
    is a refusal rather than an unchecked write."""

    url: str
    digest: str


class Ran(NamedTuple):
    """What running a command came to: its exit status, or None where it
    outlived the timeout and was killed, and what it said while doing so."""

    code: int | None
    said: str


class Refusal(enum.Enum):
    """Why a build was not written, in this file's terms and not a caller's.

    Every way a gesture is turned down is one of these, so that whoever
    answered the caller can say which it was without reading a sentence
    (`face.py`). The sentence is still what a person reads; this is what a
    program branches on.
    """

    LATEST = enum.auto()
    """`latest` was asked for, which names a different build depending on when
    it is read."""

    IN_FLIGHT = enum.auto()
    """A flash is already under way. The second is refused, never queued."""

    NO_STATION = enum.auto()
    """The device is not there, so there is nothing to write to."""

    NO_RELEASE = enum.auto()
    """The source has no release by that tag."""

    SOURCE_AWAY = enum.auto()
    """The source could not be asked about that tag: it did not answer, or
    what it answered is not a release. Not the tag's doing, and not a reason
    to go and type another one."""

    NO_ASSET = enum.auto()
    """The release carries no firmware to write, or none that could be
    fetched — which is the same thing to a caller holding a tag."""

    NO_DIGEST = enum.auto()
    """The release reports no digest for its firmware, so what was fetched
    cannot be checked, and unchecked is not written (ADR-0065)."""

    NOT_PUBLISHED = enum.auto()
    """What was fetched is not what the release says it published."""

    TOOL_FAILED = enum.auto()
    """esptool exited non-zero. The station may be half written."""

    TOOL_KILLED = enum.auto()
    """esptool outlived its timeout and was killed. So may the station be."""

    RAISED = enum.auto()
    """Something else went wrong while writing. Not a refusal anybody wrote
    down, and an answer all the same: a caller that was told nothing is a page
    waiting on a flash that ended minutes ago."""


class Wrote(NamedTuple):
    """What became of a gesture: what it was refused for, or None where the
    build was written, and the sentence that says which.

    One sentence, because what is on the other end is a person: it is the line
    the box's log gets and the reason whoever asked is given (ADR-0050).
    """

    refusal: Refusal | None
    said: str


Fetch = Callable[[str], Awaitable[bytes]]
"""How bytes are read off a URL, injected so the suite reaches no network."""

Runner = Callable[[Sequence[str], float], Awaitable[Ran]]
"""How a command is run to its end, injected so the suite runs no esptool:
nothing in the gate may need a command station (docs/dccex_usb/README.md)."""


class Device(Protocol):
    """What a flash needs of the thing that owns the serial device.

    The mirror, and nothing else this package has — `Station` satisfies it by
    having the members. Narrow on purpose: what the flash may do to the
    railroad's one live port is exactly these three things, and a test can
    stand in for all of them.
    """

    @property
    def path(self) -> str: ...

    @property
    def held(self) -> bool: ...

    def released(self) -> AbstractAsyncContextManager[None]: ...


def release_url(releases: str, tag: str) -> str:
    """Where the release API is asked about one tag.

    The tag is **escaped whole**: it arrives from a caller on a LAN with no
    authentication on it (ADR-0042), and a tag that kept its slashes would name
    a path of the caller's choosing under the host this app was configured
    with.
    """
    return f"{releases.rstrip('/')}/tags/{quote(tag, safe='')}"


def asset(document: object, name: str = ASSET) -> Asset | None:
    """The firmware asset a release document names, or None where it names
    none.

    Read the way a payload is read (BUS.md, rule 4) and for the same
    reason one level out: this is a document from a service, and a build that
    reached into it would be taken down by whatever the service returned the
    day it returned something else.
    """
    if not isinstance(document, dict):
        return None
    listed = cast(dict[str, object], document).get("assets")
    if not isinstance(listed, list):
        return None
    for entry in cast(list[object], listed):
        if not isinstance(entry, dict):
            continue
        fields = cast(dict[str, object], entry)
        if fields.get("name") != name:
            continue
        url, digest = fields.get("browser_download_url"), fields.get("digest")
        if not isinstance(url, str):
            return None
        return Asset(url, digest if isinstance(digest, str) else "")
    return None


def matches(binary: bytes, digest: str) -> bool:
    """Whether what was fetched is what the release says it published.

    A digest this cannot read matches nothing: the check is the whole reason a
    tag chosen at runtime is safe to write, so an unchecked binary is refused
    rather than written (ADR-0065, decision 4).
    """
    if not digest.lower().startswith(SHA256):
        return False
    return hashlib.sha256(binary).hexdigest() == digest[len(SHA256) :].strip().lower()


def argv(device: str, firmware: Path) -> list[str]:
    """What esptool is given, against the device this app already holds.

    Hyphenated throughout: esptool 5 renamed the entry point and the
    subcommands, and the underscore forms are deprecated aliases a later major
    drops. The flash mode, frequency and size are the station core's own
    upload settings, and the tool is pinned by `pyproject.toml` — the version
    the repository was tested at, in the one shared image.
    """
    return [
        "esptool",
        "--chip",
        CHIP,
        "--port",
        device,
        "--baud",
        FLASH_BAUD,
        "--before",
        "default-reset",
        "--after",
        "hard-reset",
        "write-flash",
        "-z",
        "--flash-mode",
        FLASH_MODE,
        "--flash-freq",
        FLASH_FREQ,
        "--flash-size",
        FLASH_SIZE,
        ADDRESS,
        str(firmware),
    ]


async def fetch(url: str) -> bytes:
    """What is at `url`, read off the loop's thread.

    In a thread because the mirror is on this loop: the fan-out happens while
    a release is being fetched, and a client whose bytes waited on a download
    would be a throttle that did nothing for a minute.
    """
    return await asyncio.to_thread(_read, url)


def _read(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"Accept": ACCEPT})
    with urllib.request.urlopen(request, timeout=FETCH_S) as answer:
        return cast(bytes, answer.read())


async def run(command: Sequence[str], timeout_s: float) -> Ran:
    """Run a command to its end, killing it where it outlives `timeout_s`.

    Its output is kept whole and both streams are one: what a refusal carries
    is the last thing the tool said, and which stream it said it on is not
    something a person reading a bus row has any use for.
    """
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        said, _ = await asyncio.wait_for(process.communicate(), timeout_s)
    except TimeoutError:
        process.kill()
        await process.wait()
        return Ran(None, "")
    return Ran(process.returncode, said.decode(errors="replace"))


def said(output: str) -> str:
    """The last thing a tool said, for the row a person reads. Its whole
    output on a state row would be a screenful where a sentence is wanted, and
    what an error was is the end of it."""
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    return lines[-1] if lines else ""


class Flasher:
    """The gesture answered: a released build written onto the command
    station by the app that owns its device.

    Constructed on the mirror, and reached by a call on this loop and by
    nothing else: there is no subscription here, and the one caller is the
    route the face answers with (ADR-0001, #13). Whether it is
    safe to reset the station is not a thing this reads, and neither is
    anything else about the railroad: that guarantee lives in the client
    written to honour it, which is where the one about cutting track power
    lives too (ADR-0051, ADR-0062, ADR-0065, ADR-0006).
    """

    def __init__(
        self,
        device: Device,
        releases: str = RELEASES,
        *,
        fetch: Fetch = fetch,
        runner: Runner = run,
        timeout_s: float = TIMEOUT_S,
        log: Callable[[str], None] = to_stderr,
    ) -> None:
        self._device = device
        self._releases = releases
        self._fetch = fetch
        self._runner = runner
        self._timeout_s = timeout_s
        self._log = log
        # The one flash there may be, held so a second gesture is refused
        # rather than queued, and so that the process ending can wait for the
        # one in flight rather than leaving a station half written.
        self._flashing: asyncio.Task[Wrote] | None = None

    @property
    def flashing(self) -> bool:
        """Whether a flash is in flight. What a second gesture is refused on."""
        return self._flashing is not None

    async def settled(self) -> None:
        """Come back once the flash in flight, if there is one, is over.

        What the process waits on as it ends: the mirror gives the device back
        when the flash is done with it, and an exit in the middle of one would
        leave the station written halfway and the port closed.
        """
        flashing = self._flashing
        if flashing is not None:
            await asyncio.shield(flashing)

    async def wanted(self, tag: str) -> Wrote:
        """A build asked for: refused here, or written and answered.

        **The flash is a task of its own and this waits on it**, because both
        halves of that matter. It is a task because this runs on the loop that
        is the mirror: the fan-out goes on for the whole of a fetch — which the
        device is held through — and the port goes on being served for the
        whole of the flash after it, which is what lets a client that was
        disconnected by the outage come back to a mirror that is answering. It
        is waited on because whoever asked is owed what became of it, and
        esptool exiting non-zero is not knowable before esptool has run.

        **A caller that goes away does not take the flash with it**, which is
        what the shield is for. The station is being written by then; a browser
        closing its tab, or the request's own patience running out, must not
        leave it half written. What is lost is only the answer, which nobody is
        there for.

        The three refusals above the task are the ones that need nothing of the
        network or the device, and they are answered before anything is
        started. Checking `flashing` here rather than in the task is what makes
        a second gesture a refusal and not a queue: nothing is awaited between
        the check and the task being made, so two callers cannot both pass it.
        """
        if tag == LATEST:
            return self._refused(
                Refusal.LATEST,
                f"'{LATEST}' is not a build: it names a different one"
                " depending on when it is read, and what was written has to be"
                " sayable afterwards",
            )
        if self.flashing:
            return self._refused(
                Refusal.IN_FLIGHT,
                f"a flash is already under way, so '{tag}' was not started",
            )
        if not self._device.held:
            return self._refused(
                Refusal.NO_STATION,
                f"the command station is not there — '{tag}' was not"
                f" written to {self._device.path}",
            )
        self._flashing = asyncio.create_task(self._flash(tag))
        return await asyncio.shield(self._flashing)

    def _refused(self, refusal: Refusal, said: str) -> Wrote:
        """Turned down before anything was started: said on the box, and
        answered to whoever asked."""
        self._log(f"refused: {said}")
        return Wrote(refusal, said)

    async def _flash(self, tag: str) -> Wrote:
        """One flash, from the release to the station, and what it came to.

        Every way out of it says what became of the flash, and the flag falls
        whichever way it went: an app that refused a flash and then refused
        every one after it because a failure left the flag standing would be
        worse than the failure. Nothing waits after the flag falls, so the
        gesture that is answered next is answered by an app that has already
        said what became of this one.
        """
        self._log(f"flashing '{tag}' from {self._releases}")
        try:
            wrote = await self._written(tag)
        except Exception as raised:  # noqa: BLE001 — reported, never absorbed
            wrote = Wrote(
                Refusal.RAISED,
                f"writing '{tag}' to the command station failed: {raised}",
            )
        finally:
            self._flashing = None
        self._log(wrote.said if wrote.refusal is None else f"refused: {wrote.said}")
        return wrote

    async def _written(self, tag: str) -> Wrote:
        """The build written, or why it was not.

        The order is ADR-0065's and the whole of the care in this file: the
        release is resolved, fetched and checked while the mirror still holds
        the device, and only then is the device let go.
        """
        url = release_url(self._releases, tag)
        try:
            document = json.loads(await self._fetch(url))
        except urllib.error.HTTPError as replied:
            # The source answered. A 404 is it saying it carries no such
            # release, which is the tag's doing; anything else is it failing
            # to answer, which is not. `HTTPError` is an `URLError` and so an
            # `OSError`, so this has to be told apart before them (#46).
            if replied.code != NO_SUCH:
                return self._unreachable(tag, replied)
            return Wrote(Refusal.NO_RELEASE, f"no release '{tag}' at {url}: {replied}")
        except (OSError, ValueError) as away:
            # Refused, timed out, no such host, or a body that is not JSON:
            # the source was never asked, so the tag is not what is wrong.
            return self._unreachable(tag, away)
        found = asset(document)
        if found is None:
            return Wrote(Refusal.NO_ASSET, f"release '{tag}' carries no {ASSET}")
        if not found.digest:
            return Wrote(
                Refusal.NO_DIGEST,
                f"release '{tag}' reports no digest for {ASSET}, so it is unchecked",
            )
        try:
            binary = await self._fetch(found.url)
        except (OSError, urllib.error.URLError) as away:
            return Wrote(
                Refusal.NO_ASSET,
                f"{ASSET} for '{tag}' could not be fetched from {found.url}: {away}",
            )
        if not matches(binary, found.digest):
            return Wrote(
                Refusal.NOT_PUBLISHED,
                f"{ASSET} for '{tag}' is not what the release reports"
                f" ({found.digest}), so it was not written",
            )
        return await self._runs(tag, binary)

    def _unreachable(self, tag: str, away: Exception) -> Wrote:
        """The source could not be asked, said the way the releases route
        says it: the source named, and what went wrong with it (`face.py`).

        Separate from `NO_RELEASE` because the two send a person to different
        places — one to type a tag the source carries, the other to find out
        why the source is away — and an outage told as a missing release sends
        them to the wrong one (#46).
        """
        return Wrote(
            Refusal.SOURCE_AWAY,
            f"the releases at {self._releases} could not be read,"
            f" so '{tag}' was not written: {away}",
        )

    async def _runs(self, tag: str, binary: bytes) -> Wrote:
        """The device handed over, esptool run on it, and the device taken
        back — the one ordering that can leave the railroad with a closed port
        and no firmware if it is got wrong."""
        with tempfile.TemporaryDirectory() as workspace:
            firmware = Path(workspace) / ASSET
            firmware.write_bytes(binary)
            command = argv(self._device.path, firmware)
            async with self._device.released():
                ran = await self._runner(command, self._timeout_s)
        if ran.code is None:
            return Wrote(
                Refusal.TOOL_KILLED,
                f"writing '{tag}' outlived {self._timeout_s:.0f}s and was killed;"
                f" the command station may be half written",
            )
        if ran.code != 0:
            return Wrote(
                Refusal.TOOL_FAILED,
                f"writing '{tag}' failed: esptool exited {ran.code}. {said(ran.said)}",
            )
        return Wrote(None, f"flashed '{tag}'")
