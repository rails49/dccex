"""The mirror, inside the image a box runs it in.

Everything else about the mirror reads the sources and gives them a pty. This
runs the built thing: the image is built the way the deploy builds it, the
container is started on its own defaults, and 2560 is dialled from outside it.

The argument is `rails49/installation`#15, which is the one
`tests/ui/test_page_serves.py` carries too. Its page was rendered by a script
the suite read and reasoned about, and it read green everywhere except the one
image it ever ran in. A suite that reads the files cannot tell two programs of
the same name apart, and the interpreter, the packages and the entry point in
this image are not the ones the rest of the suite runs under.

**The device is the container's own pty.** There is no command station here
and there is no host device to pass in, so the check makes one where the app
will look for it: a pty opened inside the container, with `/dev/dccex` pointed
at its slave, and the master held by this check as the station's end of the
cable. The app's retry loop is what picks it up — a device that is not there
yet is an outage and not a crash (`station.py`) — so the order below is the
container first and the station after, which is also the order a box powers
things on in.

**There is a second build, and it is given no commit.** One build and one
container serve every assertion about a running mirror; what an image carries
when nobody named a commit for it is about the build argument itself, so it
gets a build of its own with nothing passed and nothing run from it (#97).
Everything under the label is the first build's layers.

**This is not part of the gate.** It carries the `docker` marker, which
`scripts/check.sh` does not collect, and the workflow runs it in a job of its
own that the pull request requires (#54, #56). Where it runs, a missing daemon
is a **failure**; run by hand on a machine with no daemon it skips and says
why, because a laptop without Docker cannot be made to run this by going red.
"""

import contextlib
import os
import socket
import subprocess
import threading
import time
import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field

import pytest

from tests.ui.test_look import ROOT
from tests.ui.test_page_serves import (
    BUILD_SECONDS,
    REVISION,
    carried,
    docker,
    no_daemon,
)

pytestmark = pytest.mark.docker

DOCKERFILE = "deploy/Dockerfile"

#: The device inside the container, which is the image's own default argument
#: and what the stack maps the box's `by-id` path to.
INSIDE = "/dev/dccex"

#: The port, which is what it has always been.
PORT = 2560

#: Where the repository is written on the image, beside the revision. It names
#: a repository and not a build, so nothing a build is or is not given moves
#: it.
SOURCE = "org.opencontainers.image.source"
REPOSITORY = "https://github.com/rails49/dccex"

#: How long the app gets to say what it is serving, and the station's first
#: line to reach a client after that. The device is opened with backoff, so
#: this is a few retries and not one.
START_SECONDS = 60

#: A station that never stops talking, so nothing below depends on having
#: connected before it spoke. It is a real banner: the build in the `G-` field
#: is what the page reads a station's build off (ADR-0008).
BANNER = b"<iDCC-EX V-5.0.7 / MEGA / STANDARD_MOTOR_SHIELD G-9db6d10>\n"

#: What a client types at the station, which is the shortest thing anything
#: ever asks it (`docs/dccex_usb/README.md`).
ASKED = b"<s>"

#: The station's end of the cable, run inside the container as root.
#:
#: It opens a pty, points `/dev/dccex` at the slave, and is the thing on the
#: other side of it: the banner goes down the master on a timer, and whatever
#: comes back up is printed, which is how this check sees what a client sent
#: reach the device. Nothing of it is in the image — it is handed to a
#: `python` the image already has, because the image is this repository's
#: Python and that is the whole point of it.
STATION = f"""
import os, pty, select, sys, time

master, slave = pty.openpty()
os.set_blocking(master, False)
os.chmod(os.ttyname(slave), 0o666)
if os.path.lexists({INSIDE!r}):
    os.remove({INSIDE!r})
os.symlink(os.ttyname(slave), {INSIDE!r})

deadline = time.monotonic() + {START_SECONDS * 4}
due = 0.0
while time.monotonic() < deadline:
    now = time.monotonic()
    if now >= due:
        try:
            os.write(master, {BANNER!r})
        except BlockingIOError:
            pass
        due = now + 0.25
    if select.select([master], [], [], 0.1)[0]:
        try:
            up = os.read(master, 4096)
        except BlockingIOError:
            continue
        sys.stdout.buffer.write(up)
        sys.stdout.buffer.flush()
"""


def logs(container: str) -> str:
    """What the container has said, both ways.

    `docker logs` hands the container's stdout to its own stdout and the
    container's stderr to its own stderr, and this app's log is stderr —
    connects, disconnects, the device, and the line it says on its way up
    (`station.py`). A reader that took one of the two would find nothing and
    report an app that said nothing.
    """
    said = subprocess.run(
        ["docker", "logs", container],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return said.stdout + said.stderr


@dataclass
class Talking:
    """The station's end of the cable, and everything it has heard."""

    running: subprocess.Popen[bytes]
    heard: bytearray = field(default_factory=bytearray)

    def read(self) -> None:
        """Drain the process's stdout for as long as it is running."""
        stream = self.running.stdout
        assert stream is not None
        while chunk := stream.read(1):
            self.heard += chunk

    def stop(self) -> None:
        self.running.terminate()
        # In a tear-down, so a station that will not go is not allowed to
        # stand in front of whatever failure got us here.
        with contextlib.suppress(subprocess.TimeoutExpired):
            self.running.wait(timeout=10)


@dataclass(frozen=True)
class Mirroring:
    """The image, up and mirroring: what every assertion below is about."""

    #: The container, by id.
    container: str
    #: The commit it was built under, which is also its name's second half.
    commit: str
    #: The host port the daemon put in front of 2560.
    port: int
    #: The station on the other end of the container's pty.
    station: Talking


def needs_a_daemon() -> None:
    """Stop here if no daemon answers, the way the split says to.

    Where these are required — the workflow's docker job — the daemon is part
    of what was promised, so its absence is the check failing and not the
    check excusing itself (#54). Run by hand on a laptop with no Docker it
    skips and says why, because such a machine cannot be made to run this by
    going red.
    """
    why = no_daemon()
    if why is None:
        return
    if os.environ.get("CI"):
        pytest.fail(f"this job requires a Docker daemon: {why}")
    pytest.skip(f"the mirror cannot be run here: {why}")


def published(container: str) -> int:
    """The host port the daemon put in front of the container's 2560."""
    mapping = docker("port", container, str(PORT))
    first = mapping.splitlines()[0] if mapping else ""
    _, _, where = first.rpartition(":")
    assert where.strip().isdigit(), f"no host port in {mapping!r}"
    return int(where.strip())


def dial(port: int) -> socket.socket:
    """One client of the mirror's port, as JMRI is one."""
    client = socket.create_connection(("127.0.0.1", port), timeout=5)
    client.settimeout(5)
    return client


def until(said: str, container: str) -> None:
    """Wait for one line in the container's log, or fail with what it said."""
    deadline = time.monotonic() + START_SECONDS
    while time.monotonic() < deadline:
        if said in logs(container):
            return
        time.sleep(0.2)
    raise AssertionError(f"{said!r} was never said; the log is {logs(container)!r}")


def heard_by_a_client(port: int, wanted: bytes) -> bytes:
    """Everything one client is handed until it has been handed `wanted`."""
    client = dial(port)
    got = bytearray()
    try:
        deadline = time.monotonic() + START_SECONDS
        while wanted not in got and time.monotonic() < deadline:
            try:
                chunk = client.recv(4096)
            except TimeoutError:
                continue
            if not chunk:
                break
            got += chunk
    finally:
        client.close()
    return bytes(got)


@pytest.fixture(scope="module")
def mirroring() -> Iterator[Mirroring]:
    """The image built, the container up, and a station on its device.

    One build and one container for the whole module: the build is the
    expensive part of this check and it is the same artefact every assertion
    below is about.
    """
    needs_a_daemon()

    commit = f"check-{uuid.uuid4().hex[:8]}"
    tag = f"dccex:{commit}"
    docker(
        "build",
        "-f",
        DOCKERFILE,
        "--build-arg",
        f"DCCEX_COMMIT={commit}",
        "-t",
        tag,
        ".",
        seconds=BUILD_SECONDS,
    )

    container = ""
    station: Talking | None = None
    try:
        # No command: the image's own defaults are `/dev/dccex` and 2560, and
        # a box that had to pass them would be a box that had read a
        # Dockerfile.
        container = docker("run", "-d", "-p", f"127.0.0.1:0:{PORT}", tag)
        until(f"serving {INSIDE} on {PORT}", container)

        running = subprocess.Popen(
            ["docker", "exec", container, "python", "-c", STATION],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        station = Talking(running)
        threading.Thread(target=station.read, daemon=True).start()

        port = published(container)
        yield Mirroring(container=container, commit=commit, port=port, station=station)
    finally:
        if station is not None:
            station.stop()
        if container:
            subprocess.run(
                ["docker", "rm", "-f", container], capture_output=True, check=False
            )
        subprocess.run(
            ["docker", "image", "rm", "-f", tag], capture_output=True, check=False
        )


@pytest.fixture(scope="module")
def unnamed() -> Iterator[str]:
    """The same image built with no commit passed, by tag.

    A second build rather than a second reading of the one above, because the
    argument is what this is about and the fixture above passes one. It is the
    same Dockerfile and everything under the label is the first build's layers,
    so what the second costs is the end of the last stage. Nothing is run from
    it: the claim is about the artefact, which is why this yields a tag where
    `mirroring` yields a container.
    """
    needs_a_daemon()

    tag = f"dccex:check-{uuid.uuid4().hex[:8]}"
    docker("build", "-f", DOCKERFILE, "-t", tag, ".", seconds=BUILD_SECONDS)
    try:
        yield tag
    finally:
        subprocess.run(
            ["docker", "image", "rm", "-f", tag], capture_output=True, check=False
        )


def test_the_image_runs_the_mirror_with_no_python_on_the_host(
    mirroring: Mirroring,
) -> None:
    """A box with Docker and nothing else: the app comes up and says on its
    way up what it is serving on which."""
    assert f"serving {INSIDE} on {PORT}" in logs(mirroring.container)


def test_the_port_is_published_and_a_client_is_taken(mirroring: Mirroring) -> None:
    """2560, raw on the interface the run published it on — which is what JMRI
    and the throttles have, and the only way in they have ever had."""
    client = dial(mirroring.port)
    try:
        assert client.getpeername()[1] == mirroring.port
    finally:
        client.close()


def test_what_the_station_says_reaches_a_client_of_2560(
    mirroring: Mirroring,
) -> None:
    """The mirror's downward half, through the image: a banner written onto
    the container's pty is handed to a program that dialled the published
    port."""
    assert BANNER.strip() in heard_by_a_client(mirroring.port, BANNER.strip())


def test_what_a_client_sends_reaches_the_device(mirroring: Mirroring) -> None:
    """And the upward half. `<s>` is one whole message, so it goes down the
    cable in one write (`framing.py`) and the station's end of the pty sees
    it."""
    client = dial(mirroring.port)
    try:
        client.sendall(ASKED)
        deadline = time.monotonic() + START_SECONDS
        while ASKED not in mirroring.station.heard and time.monotonic() < deadline:
            time.sleep(0.1)
    finally:
        client.close()
    assert ASKED in mirroring.station.heard, bytes(mirroring.station.heard)


def test_the_image_carries_the_commit_it_was_built_from(mirroring: Mirroring) -> None:
    """ADR-0005 d.4, off the built image rather than off the Dockerfile: a
    `docker inspect` on the box answers the question even for one somebody
    renamed."""
    revision = docker(
        "inspect",
        "--format",
        '{{index .Config.Labels "org.opencontainers.image.revision"}}',
        mirroring.container,
    )
    assert revision == mirroring.commit


def test_a_build_given_no_commit_claims_none(unnamed: str) -> None:
    """The clean clone's build: `docker build` with nothing passed, which is
    what `up --build` does where `DCCEX_COMMIT` is unset.

    The label is there and it is empty. An image nobody named a commit for
    says so in the place ADR-0005 d.4 asks the commit to be said, and it says
    nothing else: a `dev`, an `unknown` or a `local` there would read like a
    commit reference and be none, where an empty revision cannot be read as
    anything but nobody having named one (#97, and the page's since #57).
    `dev` is still said — in the name, where it is true, and
    `tests/deploy/test_stack.py` is what holds it.

    The repository beside it is unchanged by any of that: it names a
    repository and not a build, so a build that was told no commit carries it
    exactly as the one above does.
    """
    on_it = carried(unnamed)
    assert REVISION in on_it, f"the image carries no revision at all: {on_it}"
    assert on_it[REVISION] == "", (
        f"a build that was given no commit claims {on_it[REVISION]!r} as the one"
        " it was built from"
    )
    assert on_it.get(SOURCE) == REPOSITORY, f"the repository is {on_it.get(SOURCE)!r}"
