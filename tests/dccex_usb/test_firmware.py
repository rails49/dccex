"""Tests at the flash seam, with no station, no network and no esptool.

The suite's device is a pty, which esptool cannot write, and nothing in the
gate may reach a release API. So the two things that leave this process are
injected — what fetches a URL, and what runs a command — and what is asserted
here is everything but them: the URL a tag becomes, the digest check that
makes a tag chosen at runtime safe to write, the argv esptool is given, the
ordering the railroad depends on, and every way a flash is refused.

The device is a fake here; `tests/dccex_usb/test_station.py` holds the real
one to the same handover against a pty.

What went with the bus is the two cases that read a payload: a gesture is a
call, made by the face (ADR-0001, #12, #13), and a refusal is a line in the log
rather than a row. Everything else came across.

What #13 added to that is the other half of a refusal: `wanted` answers what
became of the flash, so every case below asserts the value whoever asked is
given as well as the line the box is told. What a status those become is
`test_face.py`'s.
"""

import asyncio
import contextlib
import hashlib
import json
import urllib.error
from collections.abc import AsyncGenerator, Callable, Sequence
from email.message import Message
from pathlib import Path

import pytest

from dccex_usb.firmware import (
    ASSET,
    LATEST,
    Asset,
    Flasher,
    Ran,
    Refusal,
    Wrote,
    argv,
    asset,
    matches,
    reads_as_release,
    release_url,
)
from tests.dccex_usb.test_station import Log, Pty, station

RELEASES = "https://api.example.invalid/repos/rails49/CommandStation-EX/releases"
TAG = "v5.6.4-rails49.1"
DEVICE = "/dev/dccex"
BINARY = b"the build the railroad asked for"
DIGEST = f"sha256:{hashlib.sha256(BINARY).hexdigest()}"
DOWNLOAD = "https://releases.example.invalid/firmware.bin"
NOWHERE = "example.invalid"
"""The host the configured source and the firmware it publishes are both at.
A sentence that spelled either of them — whole, or by the host on its own —
carries this, so one assertion catches the lot (#94)."""
TIMEOUT_S = 30.0
SETTLE_S = 5.0

REFUSED = "refused: "
"""What the log says where a flash was turned down. There is no row and
nobody to publish one to (ADR-0001); what there is besides the line is the
answer to whoever asked (#13)."""


def refusals(log: Log) -> list[str]:
    """What the flasher refused, in its own words and in order."""
    return [line[len(REFUSED) :] for line in log.lines if line.startswith(REFUSED)]


def answered(code: int, reason: str = "") -> urllib.error.HTTPError:
    """What the release API raises where it answered with a status: `404`
    where it carries no release by that tag, anything else where it did not
    answer the question that was asked (#46)."""
    return urllib.error.HTTPError(
        release_url(RELEASES, TAG), code, reason, Message(), None
    )


def release(digest: object = DIGEST, name: str = ASSET) -> bytes:
    """A release document, as the API answers a tag with one."""
    return json.dumps(
        {
            "tag_name": TAG,
            "assets": [
                {"name": "notes.txt", "browser_download_url": "…", "digest": "…"},
                {"name": name, "browser_download_url": DOWNLOAD, "digest": digest},
            ],
        }
    ).encode()


class FakeDevice:
    """The mirror, faked: what it was asked to do, in the order it was asked.

    `order` is what the ordering test reads, and the fake runner appends to
    the same list — so "released, ran, resumed" is one sequence rather than
    two that have to be lined up.
    """

    def __init__(self, held: bool = True) -> None:
        self.path = DEVICE
        self.held = held
        self.order: list[str] = []

    @contextlib.asynccontextmanager
    async def released(self) -> AsyncGenerator[None]:
        self.order.append("released")
        self.held = False
        try:
            yield
        finally:
            self.held = True
            self.order.append("resumed")


class FakeFetch:
    """What a URL answers with, and a record of what was asked for."""

    def __init__(
        self,
        document: bytes | Exception | None = None,
        binary: bytes | Exception = BINARY,
    ) -> None:
        self._answers: dict[str, bytes | Exception] = {
            release_url(RELEASES, TAG): release() if document is None else document,
            DOWNLOAD: binary,
        }
        self.asked: list[str] = []

    async def __call__(self, url: str) -> bytes:
        self.asked.append(url)
        answer = self._answers.get(url, OSError(f"nothing at {url}"))
        if isinstance(answer, Exception):
            raise answer
        return answer


FLASHED = Ran(0, "")
"""What esptool comes to where it wrote the station."""


class FakeRunner:
    """esptool, faked: what it was given, and what it came to.

    It reads the file it was pointed at as it runs, because the flash writes
    that file into a directory that is gone by the time the test looks — and
    what reached the disk is the thing being asserted anyway.
    """

    def __init__(self, ran: Ran = FLASHED, *, waits: bool = False) -> None:
        self._ran = ran
        self._let_go = asyncio.Event() if waits else None
        self.commands: list[Sequence[str]] = []
        self.timeouts: list[float] = []
        self.wrote: list[bytes] = []
        self.order: list[str] | None = None
        self.called = asyncio.Event()

    async def __call__(self, command: Sequence[str], timeout_s: float) -> Ran:
        self.commands.append(command)
        self.timeouts.append(timeout_s)
        self.wrote.append(Path(command[-1]).read_bytes())
        if self.order is not None:
            self.order.append("ran")
        self.called.set()
        if self._let_go is not None:
            await self._let_go.wait()
        return self._ran

    def let_go(self) -> None:
        assert self._let_go is not None
        self._let_go.set()


class Flash:
    """One flasher, and the gestures a test makes at it."""

    def __init__(
        self,
        device: FakeDevice | None = None,
        fetch: FakeFetch | None = None,
        runner: FakeRunner | None = None,
    ) -> None:
        self.device = device if device is not None else FakeDevice()
        self.fetch = fetch if fetch is not None else FakeFetch()
        self.runner = runner if runner is not None else FakeRunner()
        self.log = Log()
        self.flasher = Flasher(
            self.device,
            RELEASES,
            fetch=self.fetch,
            runner=self.runner,
            timeout_s=TIMEOUT_S,
            log=self.log,
        )

    @property
    def refusals(self) -> list[str]:
        return refusals(self.log)

    async def wants(self, tag: str = TAG) -> Wrote:
        """A build asked for the way the face asks for one, and what it came
        to answered back to whoever asked (#13)."""
        return await asyncio.wait_for(self.flasher.wanted(tag), SETTLE_S)

    async def settled(self) -> None:
        """Wait out the flash in flight, whichever way it ended."""
        await asyncio.wait_for(self.flasher.settled(), SETTLE_S)


# -- the pure units ----------------------------------------------------------


def test_a_tag_is_asked_about_by_the_release_api() -> None:
    assert release_url(RELEASES, TAG) == f"{RELEASES}/tags/{TAG}"


def test_a_releases_url_with_a_trailing_slash_is_the_same_url() -> None:
    assert release_url(f"{RELEASES}/", TAG) == release_url(RELEASES, TAG)


def test_a_tag_cannot_walk_out_of_the_releases_it_was_configured_with() -> None:
    """A tag arrives from a caller on a LAN with no authentication on it
    (ADR-0042), so it is escaped whole: nothing in it names a path of its own
    choosing."""
    asked = release_url(RELEASES, "../../../other/releases/tags/v1")

    assert asked.startswith(f"{RELEASES}/tags/")
    assert "/" not in asked[len(RELEASES) + len("/tags/") :]


def test_the_firmware_asset_is_where_to_fetch_it_and_its_digest() -> None:
    assert asset(json.loads(release())) == Asset(DOWNLOAD, DIGEST)


def test_a_release_without_the_firmware_names_no_asset() -> None:
    assert asset(json.loads(release(name="other.bin"))) is None


@pytest.mark.parametrize(
    "document", ["", [], {"assets": "several"}, {"assets": [1, 2]}, {}]
)
def test_a_document_that_cannot_be_read_names_no_asset(document: object) -> None:
    assert asset(document) is None


def test_a_release_document_reads_as_a_release() -> None:
    assert reads_as_release(json.loads(release()))
    assert reads_as_release(json.loads(release(name="other.bin")))


def test_a_release_carrying_nothing_at_all_still_reads_as_a_release() -> None:
    """An empty list is a release that carries no firmware, which is what
    `NO_ASSET` is for. The source answered the question that was asked."""
    assert reads_as_release({"assets": []})


@pytest.mark.parametrize(
    "document", ["", [], {}, {"assets": "several"}, {"tag_name": TAG}, None]
)
def test_a_document_that_is_not_a_release_does_not_read_as_one(
    document: object,
) -> None:
    """What `asset` answers None for twice over is told apart here: a release
    with nothing in it, and a document this app cannot read as a release at
    all (#66)."""
    assert not reads_as_release(document)


def test_an_asset_the_api_reports_no_digest_for_carries_none() -> None:
    found = asset(json.loads(release(digest=None)))

    assert found is not None and found.digest == ""


def test_the_digest_is_what_says_the_bytes_are_the_published_ones() -> None:
    assert matches(BINARY, DIGEST)
    assert not matches(BINARY + b"!", DIGEST)


def test_a_digest_in_a_form_this_cannot_read_matches_nothing() -> None:
    """An unchecked binary is refused rather than written (ADR-0065)."""
    assert not matches(BINARY, "")
    assert not matches(BINARY, hashlib.sha256(BINARY).hexdigest())
    assert not matches(BINARY, f"md5:{hashlib.md5(BINARY).hexdigest()}")


def test_the_argv_esptool_is_given() -> None:
    """Hyphenated throughout: esptool 5 renamed the entry point and the
    subcommands, and the underscore forms are aliases a later major drops."""
    assert argv(DEVICE, Path("/tmp/firmware.bin")) == [
        "esptool",
        "--chip",
        "esp32",
        "--port",
        DEVICE,
        "--baud",
        "460800",
        "--before",
        "default-reset",
        "--after",
        "hard-reset",
        "write-flash",
        "-z",
        "--flash-mode",
        "dio",
        "--flash-freq",
        "80m",
        "--flash-size",
        "4MB",
        "0x0",
        "/tmp/firmware.bin",
    ]


# -- the flash ---------------------------------------------------------------


def test_what_a_flash_came_to_is_answered_to_whoever_asked() -> None:
    """The gesture has a caller now (#13), so what became of it is a value and
    not only a line on the box: the face turns it into a status and a reason
    for whoever asked, and a refusal written to nobody is the thing the face
    was for (ADR-0001, ADR-0050)."""

    async def scenario() -> None:
        flash = Flash()

        wrote = await flash.wants()

        assert wrote.refusal is None
        assert TAG in wrote.said

    asyncio.run(scenario())


def test_the_release_is_written_to_the_station_and_nothing_is_refused() -> None:
    async def scenario() -> None:
        flash = Flash()

        await flash.wants()
        await flash.settled()

        assert flash.refusals == []
        assert flash.runner.wrote == [BINARY]
        assert flash.runner.timeouts == [TIMEOUT_S]
        command = list(flash.runner.commands[0])
        assert command[:-1] == argv(DEVICE, Path(ASSET))[:-1]
        assert command[-1].endswith(f"/{ASSET}")

    asyncio.run(scenario())


def test_the_device_is_let_go_before_esptool_and_taken_back_after() -> None:
    """The one ordering that can break the railroad (ADR-0065): two openers
    fight over the line discipline, and a flash that ran with the mirror on
    the port would leave the railroad with neither."""

    async def scenario() -> None:
        flash = Flash()
        device, runner = flash.device, flash.runner
        assert isinstance(runner, FakeRunner)
        runner.order = device.order

        await flash.wants()
        await flash.settled()

        assert device.order == ["released", "ran", "resumed"]
        assert device.held

    asyncio.run(scenario())


def test_the_device_is_let_go_only_once_the_build_is_fetched_and_checked() -> None:
    """A network failure costs nothing: the reverse order leaves the railroad
    with a closed port and no firmware."""

    async def scenario() -> None:
        flash = Flash(fetch=FakeFetch(binary=b"a different build"))

        wrote = await flash.wants()

        assert flash.device.order == []
        assert flash.runner.commands == []
        assert wrote.refusal is Refusal.NOT_PUBLISHED
        assert "not what the release reports" in wrote.said
        assert flash.refusals == [wrote.said]

    asyncio.run(scenario())


def test_a_tag_with_no_such_release_is_refused() -> None:
    """The source answered, and what it said is that it carries no release by
    that tag. The tag is the thing to fix, and the sentence names it."""

    async def scenario() -> None:
        flash = Flash(fetch=FakeFetch(document=answered(404)))

        wrote = await flash.wants()

        assert wrote.refusal is Refusal.NO_RELEASE
        assert f"no release '{TAG}'" in wrote.said
        assert flash.refusals == [wrote.said]
        assert flash.device.order == []

    asyncio.run(scenario())


def test_a_source_that_cannot_be_reached_is_refused_as_the_source() -> None:
    """Not the tag's doing: the source was never asked, so a caller told the
    release does not exist would go off and retype a tag that is good. The
    sentence says the release source could not be read, and what went wrong
    with reading it, and names the tag it turned down (#46, #94)."""

    async def scenario() -> None:
        away = urllib.error.URLError(ConnectionRefusedError("Connection refused"))
        flash = Flash(fetch=FakeFetch(document=away))

        wrote = await flash.wants()

        assert wrote.refusal is Refusal.SOURCE_AWAY
        assert f"the release source could not be read, so '{TAG}' was" in wrote.said
        assert "Connection refused" in wrote.said
        assert flash.refusals == [wrote.said]
        assert flash.device.order == []
        assert flash.device.held, "the device is not let go"

    asyncio.run(scenario())


def test_a_source_that_answers_something_that_is_not_json_is_refused() -> None:
    """A login page, an error page, a proxy's own apology: the source did not
    answer the question, so this is the source and not the tag (#46)."""

    async def scenario() -> None:
        flash = Flash(fetch=FakeFetch(document=b"<html>not a release</html>"))

        wrote = await flash.wants()

        assert wrote.refusal is Refusal.SOURCE_AWAY
        assert f"the release source could not be read, so '{TAG}' was" in wrote.said
        assert flash.refusals == [wrote.said]
        assert flash.device.order == []
        assert flash.device.held, "the device is not let go"

    asyncio.run(scenario())


def test_a_source_that_answers_a_status_other_than_404_is_refused() -> None:
    """Somebody else's service having a bad day — a 500, a 403, a gateway in
    front of it — is not a tag that does not exist (#46)."""

    async def scenario() -> None:
        flash = Flash(fetch=FakeFetch(document=answered(500, "Internal Server Error")))

        wrote = await flash.wants()

        assert wrote.refusal is Refusal.SOURCE_AWAY
        assert f"the release source could not be read, so '{TAG}' was" in wrote.said
        assert "500" in wrote.said
        assert flash.refusals == [wrote.said]
        assert flash.device.order == []
        assert flash.device.held, "the device is not let go"

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "document", [b"[]", b"{}"], ids=["a list of them", "an object with nothing in it"]
)
def test_a_source_that_answers_something_that_is_not_a_release_is_refused(
    document: bytes,
) -> None:
    """A `200` carrying a document this app cannot read as a release is the
    source answering oddly, not a release with nothing in it: the tag is not
    what to go and retype, so it is `SOURCE_AWAY` and the sentence says the
    release source answered with something else (#66)."""

    async def scenario() -> None:
        flash = Flash(fetch=FakeFetch(document=document))

        wrote = await flash.wants()

        assert wrote.refusal is Refusal.SOURCE_AWAY
        assert f"'{TAG}' was not written" in wrote.said
        assert "not a release" in wrote.said
        assert f"carries no {ASSET}" not in wrote.said
        assert flash.refusals == [wrote.said]
        assert flash.device.order == []
        assert flash.device.held, "the device is not let go"

    asyncio.run(scenario())


def test_a_release_that_carries_no_firmware_is_refused() -> None:
    async def scenario() -> None:
        flash = Flash(fetch=FakeFetch(document=release(name="other.bin")))

        wrote = await flash.wants()

        assert wrote == Wrote(Refusal.NO_ASSET, f"release '{TAG}' carries no {ASSET}")
        assert flash.refusals == [wrote.said]

    asyncio.run(scenario())


def test_a_release_the_api_reports_no_digest_for_is_refused() -> None:
    """Unchecked is not written: the per-asset digest is what makes a tag
    chosen at the moment of the gesture safe (ADR-0065, decision 4).

    The whole sentence, because the face now lists such a release as not
    flashable (#81) and this refusal is what is left for a caller that named
    the tag anyway — the flag moved and the sentence did not.
    """

    async def scenario() -> None:
        flash = Flash(fetch=FakeFetch(document=release(digest=None)))

        wrote = await flash.wants()

        assert wrote == Wrote(
            Refusal.NO_DIGEST,
            f"release '{TAG}' reports no digest for {ASSET}, so it is unchecked",
        )
        assert flash.refusals == [wrote.said]
        assert flash.device.order == []

    asyncio.run(scenario())


def test_esptool_exiting_non_zero_is_refused_in_its_own_words() -> None:
    async def scenario() -> None:
        flash = Flash(runner=FakeRunner(Ran(2, "A fatal error occurred: no serial")))

        wrote = await flash.wants()

        assert wrote.refusal is Refusal.TOOL_FAILED
        assert "esptool exited 2" in wrote.said
        assert "A fatal error occurred: no serial" in wrote.said
        assert flash.refusals == [wrote.said]
        assert flash.device.held, "the device is not taken back"

    asyncio.run(scenario())


def test_esptool_outliving_the_timeout_is_refused() -> None:
    async def scenario() -> None:
        flash = Flash(runner=FakeRunner(Ran(None, "")))

        wrote = await flash.wants()

        assert wrote.refusal is Refusal.TOOL_KILLED
        assert "was killed" in wrote.said
        assert flash.refusals == [wrote.said]
        assert flash.device.held

    asyncio.run(scenario())


def test_a_flash_asked_for_while_the_station_is_away_is_refused() -> None:
    """The device is not there — switched off, or the cable is out — and a
    station that is not there is not written to."""

    async def scenario() -> None:
        flash = Flash(device=FakeDevice(held=False))

        wrote = await flash.wants()

        assert wrote.refusal is Refusal.NO_STATION
        assert "not there" in wrote.said
        assert flash.refusals == [wrote.said]
        assert flash.fetch.asked == []

    asyncio.run(scenario())


def test_a_second_gesture_while_a_flash_is_in_flight_is_refused_not_queued() -> None:
    """A command is honoured now or ignored, which is what this app already
    does with what a client sends while the device is away; a queued flash is
    a station that reboots minutes after somebody asked."""

    async def scenario() -> None:
        runner = FakeRunner(waits=True)
        flash = Flash(runner=runner)

        asking = asyncio.create_task(flash.wants())
        await asyncio.wait_for(runner.called.wait(), SETTLE_S)

        second = await flash.wants("v5.6.4-rails49.2")

        assert second.refusal is Refusal.IN_FLIGHT
        assert "already under way" in second.said
        assert flash.refusals == [second.said]

        runner.let_go()
        assert (await asking).refusal is None
        await flash.settled()

        assert len(runner.commands) == 1

    asyncio.run(scenario())


def test_a_flash_that_failed_leaves_the_app_able_to_take_the_next_one() -> None:
    """The flag falls whichever way a flash ended. An app that refused every
    gesture after one failure, because the failure left the flag standing,
    would be worse than the failure — and the second ask below would come back
    as a flash in flight instead of being tried."""

    async def scenario() -> None:
        flash = Flash(runner=FakeRunner(Ran(2, "A fatal error occurred")))

        failed = await flash.wants()
        again = await flash.wants()

        assert failed.refusal is Refusal.TOOL_FAILED
        assert again.refusal is Refusal.TOOL_FAILED
        assert len(flash.runner.commands) == 2, "the second ask was not tried"
        assert not flash.flasher.flashing
        assert flash.device.held

    asyncio.run(scenario())


def test_a_flash_that_went_wrong_in_no_written_down_way_is_still_answered() -> None:
    """The tenth way out, which nobody designed: something raised. A caller
    told nothing is a page waiting on a flash that ended minutes ago, so it is
    an answer like the rest — and the app is askable afterwards."""

    async def raising(command: Sequence[str], timeout_s: float) -> Ran:
        raise RuntimeError("the workspace went away")

    async def scenario() -> None:
        log = Log()
        device = FakeDevice()
        flasher = Flasher(device, RELEASES, fetch=FakeFetch(), runner=raising, log=log)

        wrote = await asyncio.wait_for(flasher.wanted(TAG), SETTLE_S)

        assert wrote.refusal is Refusal.RAISED
        assert "the workspace went away" in wrote.said
        assert refusals(log) == [wrote.said]
        assert device.held, "the device is not taken back"
        assert not flasher.flashing

    asyncio.run(scenario())


def test_a_caller_that_goes_away_does_not_take_the_flash_with_it() -> None:
    """By the time anyone can leave, the station is being written. A browser
    that closed its tab, or a request that ran out of patience (face.py), must
    not leave it half written — so the flash is a task and the ask is shielded
    from whatever becomes of the caller. What is lost is the answer, which
    nobody is there for."""

    async def scenario() -> None:
        runner = FakeRunner(waits=True)
        flash = Flash(runner=runner)

        asking = asyncio.create_task(flash.wants())
        await asyncio.wait_for(runner.called.wait(), SETTLE_S)
        asking.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await asking

        runner.let_go()
        await flash.settled()

        assert flash.runner.wrote == [BINARY]
        assert flash.device.order == ["released", "resumed"]
        assert flash.refusals == []
        assert flash.log.lines[-1] == f"flashed '{TAG}'"

    asyncio.run(scenario())


def test_latest_is_not_a_build() -> None:
    """It names a different build depending on when it is read, and what was
    written has to be sayable afterwards (ADR-0065)."""

    async def scenario() -> None:
        flash = Flash()

        wrote = await flash.wants("latest")

        assert wrote.refusal is Refusal.LATEST
        assert flash.refusals == [wrote.said]
        assert flash.fetch.asked == []

    asyncio.run(scenario())


TURNED_DOWN = [
    pytest.param(
        lambda: Flash(fetch=FakeFetch(document=answered(404))),
        TAG,
        id="the source carries no such release",
    ),
    pytest.param(
        lambda: Flash(
            fetch=FakeFetch(
                document=urllib.error.URLError(ConnectionRefusedError("refused"))
            )
        ),
        TAG,
        id="the source could not be reached",
    ),
    pytest.param(
        lambda: Flash(fetch=FakeFetch(document=answered(500, "Internal Server Error"))),
        TAG,
        id="the source answered a status of its own",
    ),
    pytest.param(
        lambda: Flash(fetch=FakeFetch(document=b"<html>not a release</html>")),
        TAG,
        id="the source answered something that is not JSON",
    ),
    pytest.param(
        lambda: Flash(fetch=FakeFetch(document=b"[]")),
        TAG,
        id="the source answered something that is not a release",
    ),
    pytest.param(
        lambda: Flash(fetch=FakeFetch(document=release(name="other.bin"))),
        TAG,
        id="the release carries no firmware",
    ),
    pytest.param(
        lambda: Flash(fetch=FakeFetch(document=release(digest=None))),
        TAG,
        id="the release reports no digest for it",
    ),
    pytest.param(
        lambda: Flash(
            fetch=FakeFetch(binary=urllib.error.URLError(ConnectionResetError("reset")))
        ),
        TAG,
        id="the firmware could not be fetched",
    ),
    pytest.param(
        lambda: Flash(fetch=FakeFetch(binary=b"a different build")),
        TAG,
        id="the firmware is not what the release published",
    ),
    pytest.param(
        lambda: Flash(device=FakeDevice(held=False)),
        TAG,
        id="the command station is not there",
    ),
    pytest.param(lambda: Flash(), LATEST, id="latest"),
    pytest.param(
        lambda: Flash(runner=FakeRunner(Ran(2, "A fatal error occurred"))),
        TAG,
        id="esptool exited non-zero",
    ),
    pytest.param(
        lambda: Flash(runner=FakeRunner(Ran(None, ""))),
        TAG,
        id="esptool was killed",
    ),
]
"""Every way a gesture is turned down, each as the flasher the face holds
would turn it down. `IN_FLIGHT` and `RAISED` are the two that need a gesture
in flight and a runner that raises, and they have tests of their own above;
neither sentence has a URL to put in one."""


@pytest.mark.parametrize(("gesture", "tag"), TURNED_DOWN)
def test_no_refusal_the_face_can_return_names_where_releases_are_read_from(
    gesture: Callable[[], Flash], tag: str
) -> None:
    """The page shows what the face said word for word (#66), so a sentence
    spelling the configured source would put it in a browser — and the page
    promises it names no host, no repository and no query
    (`ui/src/releases.js`, `docs/ui/README.md`). A refusal says which of the
    things went wrong and names the tag; where it was read from stays on the
    box (#94).
    """

    async def scenario() -> None:
        flash = gesture()

        wrote = await flash.wants(tag)

        assert wrote.refusal is not None, "the gesture was not refused"
        assert NOWHERE not in wrote.said, f"the source is in {wrote.said!r}"

    asyncio.run(scenario())


def test_the_box_is_told_where_the_releases_were_read_from() -> None:
    """The source is out of the answer and not gone: the line the box keeps
    names it, so whoever is fixing a source that is away reads the URL where
    they already are (#94)."""

    async def scenario() -> None:
        away = urllib.error.URLError(ConnectionRefusedError("Connection refused"))
        flash = Flash(fetch=FakeFetch(document=away))

        wrote = await flash.wants()

        assert wrote.refusal is Refusal.SOURCE_AWAY
        assert f"flashing '{TAG}' from {RELEASES}" in flash.log.lines

    asyncio.run(scenario())


# -- the wiring --------------------------------------------------------------


def test_the_mirror_is_off_the_port_while_esptool_runs() -> None:
    """The flasher on the real mirror, with a pty for the command station.

    The fake runner is called with the device closed and the mirror has it
    again afterwards — the one ordering that can leave the railroad with a
    closed port and no firmware (ADR-0065). esptool cannot write a pty, which
    is why what runs is a fake and what is asserted is the handover.
    """

    async def scenario() -> None:
        log = Log()
        cable = Pty()
        app = station(cable.path, log)
        held: list[bool] = []

        async def runner(command: Sequence[str], timeout_s: float) -> Ran:
            held.append(app.held)
            return FLASHED

        flasher = Flasher(app, RELEASES, fetch=FakeFetch(), runner=runner, log=log)
        await app.start()
        try:
            await log.wait_for("serial open")

            wrote = await asyncio.wait_for(flasher.wanted(TAG), SETTLE_S)
            assert wrote.refusal is None

            assert held == [False], "esptool ran with the mirror on the port"
            await log.wait_for_count("serial open", 2)
            assert app.held
            assert refusals(log) == []
        finally:
            await app.close()
            cable.close()

    asyncio.run(scenario())
