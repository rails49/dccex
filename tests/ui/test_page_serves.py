"""The built page, inside the image that will serve it.

Everything else about the UI reads the sources. This runs them: the image is
built the way a box builds it, the server in it is started, and the page is
fetched over HTTP the way a browser fetches it.

The reason is `rails49/installation`#15. Its page was rendered by a script the
suite read and reasoned about, and it ran green everywhere except the one
place it ran for real — a regex GNU awk accepts and the busybox awk in
`nginx:alpine` rejects took the page down on the first box it reached. A suite
that reads the files cannot tell two programs of the same name apart.

Here the programs are node and nginx, and neither is on the box: the node that
builds the page exists for the length of a build and the nginx that serves it
is the image (`deploy/ui.Dockerfile`). So the only honest place to check that
the page is built and served is inside it, and this is the check that goes
there. It is also where the page's TypeScript is type-checked at all, the
build running `tsc --noEmit` before `vite`.

**It skips where no Docker daemon answers**, and says why. A machine without
one cannot run this and cannot be made to by going red; what it can still run
is the rest of the gate, including `test_look.py`, which holds the one thing
that drifts silently. Where a daemon does answer — a box, a development
machine, the workflow — this runs for real, and it is the only check here that
does.
"""

import http.client
import re
import shutil
import subprocess
import time
import uuid
from collections.abc import Iterator

import pytest

from tests.ui.test_look import COPY, ROOT, declarations

DOCKERFILE = "deploy/ui.Dockerfile"

#: Long enough for a cold build: both base images may have to be pulled and
#: the node stage installs from the lock file.
BUILD_SECONDS = 900

#: How long nginx gets to answer once its container is running.
START_SECONDS = 30


def no_daemon() -> str | None:
    """Why this cannot run here, or `None` if it can."""
    if shutil.which("docker") is None:
        return "no docker on the path"
    answered = subprocess.run(
        ["docker", "info", "--format", "{{.ServerVersion}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if answered.returncode != 0:
        return "no docker daemon answering"
    return None


def docker(*argument: str, seconds: int = 60) -> str:
    """One `docker` command, carrying what it said if it failed."""
    done = subprocess.run(
        ["docker", *argument],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=seconds,
        check=False,
    )
    assert done.returncode == 0, f"docker {argument[0]} failed:\n{done.stderr}"
    return done.stdout.strip()


def served(port: int, path: str) -> tuple[int, str]:
    """One request to the running container, as a browser would make it."""
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request("GET", path)
        answer = connection.getresponse()
        return answer.status, answer.read().decode()
    finally:
        connection.close()


def published(container: str) -> int:
    """The host port the daemon put in front of the container's 80."""
    mapping = docker("port", container, "80")
    match = re.search(r":(\d+)\s*$", mapping.splitlines()[0])
    assert match is not None, f"no host port in {mapping!r}"
    return int(match.group(1))


def wait_until_answering(port: int) -> None:
    """A container that never answers fails here, with what the last attempt
    got, rather than in whichever assertion happened to run first."""
    deadline = time.monotonic() + START_SECONDS
    last = "nothing"
    while time.monotonic() < deadline:
        try:
            status, _ = served(port, "/")
        except OSError as refused:  # not listening yet
            last = str(refused)
        else:
            if status == 200:
                return
            last = f"status {status}"
        time.sleep(0.2)
    raise AssertionError(f"the page never answered: {last}")


@pytest.fixture(scope="module")
def serving() -> Iterator[int]:
    """The image built, run, and answering: the port to ask it on.

    One build and one container for the whole module. The build is the
    expensive part of this check and it is the same artefact every assertion
    below is about.
    """
    why = no_daemon()
    if why is not None:
        pytest.skip(f"the page cannot be served here: {why}")

    tag = f"dccex-ui:check-{uuid.uuid4().hex[:8]}"
    docker("build", "-f", DOCKERFILE, "-t", tag, ".", seconds=BUILD_SECONDS)
    container = ""
    try:
        container = docker("run", "-d", "-p", "127.0.0.1:0:80", tag)
        port = published(container)
        wait_until_answering(port)
        yield port
    finally:
        if container:
            subprocess.run(
                ["docker", "rm", "-f", container], capture_output=True, check=False
            )
        subprocess.run(
            ["docker", "image", "rm", "-f", tag], capture_output=True, check=False
        )


def named(page: str, pattern: str) -> str:
    """The path of one built file the served page names."""
    match = re.search(pattern, page)
    assert match is not None, f"the page names no {pattern}"
    return match.group(1)


def test_the_image_serves_the_page_it_built(serving: int) -> None:
    """A clean clone, no `control` beside it and no node on the machine: a
    browser asking for `/` gets this UI's page."""
    status, page = served(serving, "/")
    assert status == 200
    assert "<dccex-app></dccex-app>" in page
    assert "/assets/" in page, "the page names nothing that was built"


def test_the_band_and_the_rail_are_in_what_was_built(serving: int) -> None:
    """The two pieces of chrome, in the artefact rather than in the sources.

    A page that compiled and drew neither would pass every other check here.
    """
    _, page = served(serving, "/")
    status, module = served(serving, named(page, r'src="([^"]*\.js)"'))
    assert status == 200
    for element in ["dccex-band", "dccex-rail"]:
        assert element in module, f"{element} is not in the built page"


def test_the_chrome_draws_with_the_copied_values(serving: int) -> None:
    """What a browser receives, against `ui/look/tokens.css`.

    `test_look.py` holds the sources against that copy. This holds the served
    bytes against it, which is the same claim with a build, a bundler and a
    server between it and nothing left to assume.
    """
    _, page = served(serving, "/")
    status, stylesheet = served(serving, named(page, r'href="([^"]*\.css)"'))
    assert status == 200
    for token, value in declarations(COPY.read_text()).items():
        assert f"{token}: {value}" in stylesheet, f"{token} is not what is served"


def test_a_path_the_page_owns_is_the_page(serving: int) -> None:
    """One page and one document. Everything on the origin that is not the
    face's prefix is the page's (ADR-0004 d.2), so a reload on a path the page
    put in the bar is the page again rather than a 404 from under it."""
    status, page = served(serving, "/anything")
    assert status == 200
    assert "<dccex-app></dccex-app>" in page
