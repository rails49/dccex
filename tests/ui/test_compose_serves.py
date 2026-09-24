"""The compose project, brought up the way its own header says.

`tests/ui/test_page_serves.py` builds `deploy/ui.Dockerfile` and runs the image
with `docker run`. That proves the image. It does not touch `compose.yaml` —
the project name, the image name, the published port, the build stanza and the
labels the door reads the route off — and until this file there was nothing in
the repository that did: the one artefact whose header promises that
`docker compose up --build` from a clean clone serves the page was held by
reading it (#53, #3).

So this brings that project up, asks it for the page on the port compose
published, reads the labels off the running container — which is where a door
reads them from — and takes it down again. What is not held here is what a
route *does*: there is no door on this machine, no certificate and no shared
network, and that is the box's and #40's. What is held is that the file parses,
builds, comes up, serves, carries the route a door would need, and hands the
build the commit it names the image by (#57).

The network is deliberately not declared external in `compose.yaml`, so `up`
works on a clean clone. That is the one thing the file has to do, and this is
the check that holds it.

**This is not part of the gate.** Like the check beside it, it carries the
`docker` marker, which `scripts/check.sh` does not collect, and the workflow
runs it in a job of its own that the pull request requires (#54, #56). Where it
runs, a missing daemon is a **failure**; run by hand on a machine with no
daemon it skips and says why.

It builds a second time where `test_page_serves.py` has already built, which is
a layer cache hit and not a second build on any machine that keeps one.
"""

import json
import os
import re
import subprocess
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from typing import cast

import pytest

from tests.ui.test_look import ROOT
from tests.ui.test_page_serves import (
    BUILD_SECONDS,
    REVISION,
    docker,
    no_daemon,
    served,
    wait_until_answering,
)

pytestmark = pytest.mark.docker

PROJECT_FILE = "compose.yaml"

#: The name the file pins (`name: dccex`). Nothing here passes `-p`, so every
#: command below is resolved by that line; a clone that lost it would name the
#: project after whatever directory it was cloned into, and the label read off
#: the running container would stop saying `dccex`.
PROJECT = "dccex"

#: The service. One, and the file says so.
SERVICE = "web"

#: How long `down` gets: stopping a container and removing an image it built.
DOWN_SECONDS = 180

#: What the file substitutes into itself. They are dropped from the environment
#: every command below runs in, so a machine that has any of them set — a
#: development box, a shell left over from a deploy — runs the same check as a
#: clean clone does.
DROPPED = ("DCCEX_COMMIT", "DCCEX_UI_PORT", "BOX_DOMAIN")

#: The route, as the door reads it off the container: written out here rather
#: than parsed out of `compose.yaml`, because a check that read the values from
#: the file it is checking would pass on any values at all. `BOX_DOMAIN` is
#: unset, so the host rule is the default a clean clone comes up with, and the
#: priority is the low one the page takes so that the face's own router claims
#: its prefix first (ADR-0004 d.2).
ROUTE = {
    "traefik.enable": "true",
    "traefik.docker.network": "rails49",
    "traefik.http.services.dccex-ui.loadbalancer.server.port": "80",
    "traefik.http.routers.dccex-ui.rule": "Host(`dccex.localhost`)",
    "traefik.http.routers.dccex-ui.priority": "1",
    "traefik.http.routers.dccex-ui.entrypoints": "websecure",
    "traefik.http.routers.dccex-ui.service": "dccex-ui",
    "traefik.http.routers.dccex-ui.tls.certresolver": "le",
}


def environment(**set_here: str) -> dict[str, str]:
    """The environment a `docker compose` command is run in."""
    clean = {name: value for name, value in os.environ.items() if name not in DROPPED}
    clean.update(set_here)
    return clean


def arguments(*argument: str) -> list[str]:
    """One command against this repository's own project file.

    `--env-file` is pointed at nothing on purpose: a `.env` beside the file is
    a developer's and would quietly move the published port out from under
    this check.
    """
    return [
        "docker",
        "compose",
        "--env-file",
        os.devnull,
        "-f",
        PROJECT_FILE,
        *argument,
    ]


def compose(
    *argument: str, seconds: int = 60, env: dict[str, str] | None = None
) -> str:
    """One `docker compose` command, carrying what it said if it failed."""
    done = subprocess.run(
        arguments(*argument),
        cwd=ROOT,
        env=environment() if env is None else env,
        capture_output=True,
        text=True,
        timeout=seconds,
        check=False,
    )
    assert done.returncode == 0, f"docker compose {argument[0]} failed:\n{done.stderr}"
    return done.stdout.strip()


def standing(env: dict[str, str] | None = None) -> str | None:
    """Why this cannot start, or `None` if nothing is in the way.

    A project already up under the pinned name is somebody else's — this check
    brings one up and takes it down again, and taking down a project it did not
    start is not its to do. So it says so and stops, rather than joining one,
    renaming itself around one, or half-running against containers it did not
    build.
    """
    containers = compose("ps", "-aq", env=env).split()
    if not containers:
        return None
    return (
        f"a compose project named {PROJECT} is already up here: "
        f"{len(containers)} container(s), {', '.join(name[:12] for name in containers)}. "
        f"This check brings that project up and takes it down again, so it will not "
        f"run against one it did not start. Bring it down — `docker compose down` at "
        f"the root of this repository — and run this again."
    )


def published(env: dict[str, str]) -> int:
    """The host port the daemon put in front of the service's 80."""
    mapping = compose("port", SERVICE, "80", env=env)
    match = re.search(r":(\d+)\s*$", mapping.splitlines()[0] if mapping else "")
    assert match is not None, f"no host port in {mapping!r}"
    return int(match.group(1))


def labels(container: str) -> dict[str, str]:
    """Every label on the running container, as a door would read them."""
    return cast(
        dict[str, str],
        json.loads(docker("inspect", "--format", "{{json .Config.Labels}}", container)),
    )


def down(env: dict[str, str]) -> None:
    """Whatever the body did, undone: the container, the volumes, the network
    the project created and the image the build produced.

    It says nothing and asserts nothing, because it runs in a `finally` where
    an assertion of its own would stand in front of the failure that got it
    there. What it left behind is asserted by the last test in this file, and
    it is idempotent so that both can call it.
    """
    subprocess.run(
        arguments("down", "--volumes", "--remove-orphans", "--rmi", "all"),
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=DOWN_SECONDS,
        check=False,
    )


@dataclass(frozen=True)
class Up:
    """The project, up: what every assertion below is about."""

    #: The one container, by id.
    container: str
    #: The commit the project was given, which is what the image is named by
    #: and what it is expected to carry.
    commit: str
    #: What the image is named, commit and all.
    image: str
    #: The port compose published, which the daemon picked.
    port: int
    #: What it was brought up with, so that taking it down names the same
    #: image the build produced rather than some other clone's `dev`.
    environment: dict[str, str]


@pytest.fixture(scope="module")
def up() -> Iterator[Up]:
    """The project built, up and answering.

    One build and one project for the whole module: the build is the expensive
    part and it is the same artefact every assertion here is about.
    """
    why = no_daemon()
    if why is not None:
        # Where this is required — the workflow's docker job — the daemon is
        # part of what was promised, so its absence is the check failing and
        # not the check excusing itself (#54).
        if os.environ.get("CI"):
            pytest.fail(f"this job requires a Docker daemon: {why}")
        pytest.skip(f"the compose project cannot be brought up here: {why}")

    # A commit of this check's own. It is what the image is named by, so the
    # substitution is asserted by the name on the running container, and
    # nothing this tears down afterwards can be an image somebody else built.
    commit = f"check-{uuid.uuid4().hex[:8]}"
    # Port 0 is the daemon picking one: this check does not collide with
    # whatever is on 8080, and `docker compose port` is what says where it went.
    where = environment(DCCEX_COMMIT=commit, DCCEX_UI_PORT="0")

    already = standing(where)
    if already is not None:
        pytest.fail(already)

    try:
        compose("up", "-d", "--build", seconds=BUILD_SECONDS, env=where)
        port = published(where)
        wait_until_answering(port)
        yield Up(
            container=compose("ps", "-q", SERVICE, env=where),
            commit=commit,
            image=f"dccex-ui:{commit}",
            port=port,
            environment=where,
        )
    finally:
        down(where)


def test_the_project_comes_up_and_serves_the_page(up: Up) -> None:
    """A clean clone and one command: the page is on the port it published.

    This is `compose.yaml`'s own header, run rather than read.
    """
    status, page = served(up.port, "/")
    assert status == 200
    assert "<dccex-app></dccex-app>" in page
    assert "/assets/" in page, "the page names nothing that was built"


def test_the_image_is_named_by_the_commit_it_was_built_from(up: Up) -> None:
    """`dccex-ui:<commit>`, and the name never moves (ADR-0005 d.1)."""
    assert docker("inspect", "--format", "{{.Config.Image}}", up.container) == up.image


def test_the_project_gives_the_commit_to_the_build_and_not_only_to_the_name(
    up: Up,
) -> None:
    """ADR-0005 d.4, read off the running container rather than off the file.

    The name is where the commit was written and it was the only place it was
    written (#57), so an image somebody renamed — or a container somebody was
    handed — answered nothing. Now the project passes the same variable it
    builds the name from into the build, and what comes out carries it: this
    is that value, off the daemon, which is where a person on the box asks.
    """
    assert labels(up.container)[REVISION] == up.commit


def test_a_clone_that_names_no_commit_builds_dev(up: Up) -> None:
    """`up --build` works with nothing set, which is what a clean clone has.

    It reads the same project the fixture brought up — with `DCCEX_COMMIT`
    dropped, as the environment every command here runs in drops it — and asks
    the file what it would build under.
    """
    assert compose("config", "--images") == "dccex-ui:dev"


def test_the_running_container_carries_the_route_the_door_reads(up: Up) -> None:
    """The labels, off the container rather than off the file.

    A door reads the route from the daemon, so this is the form the claim is
    worth making in: every label the file declares, with the value it declares,
    and nothing extra under that prefix.
    """
    on_it = {
        name: value
        for name, value in labels(up.container).items()
        if name.startswith("traefik.")
    }
    assert on_it == ROUTE


def test_the_container_is_the_project_the_file_pins(up: Up) -> None:
    """Nothing passes `-p`, so this is `name: dccex` read back off the box.

    A clone that lost the pin would be named after its directory, and the
    commands above would be resolving a project this line does not know.
    """
    on_it = labels(up.container)
    assert on_it["com.docker.compose.project"] == PROJECT
    assert on_it["com.docker.compose.service"] == SERVICE


def test_a_project_already_up_is_refused_with_a_sentence(up: Up) -> None:
    """The guard the fixture runs before it starts, asked while one is up.

    The project standing here is this check's own, which is the only project
    this check is ever allowed to have found: so this is the sentence an
    operator would be given, made with a real project rather than a fake one.
    """
    why = standing(up.environment)
    assert why is not None, "a project is up and the guard did not see it"
    assert PROJECT in why
    assert "docker compose down" in why, "the sentence does not say how to end it"


def test_the_project_comes_down_and_leaves_nothing(up: Up) -> None:
    """**Last in this file on purpose**: it takes the project down.

    The fixture takes it down in a `finally`, so it comes down even when an
    assertion above went red — but a `finally` nobody looks at is a claim
    nobody checks. This runs the same tear-down and then asks the daemon what
    is left: no container, no volume, no network of the project's, and not the
    image the build produced.
    """
    down(up.environment)
    assert compose("ps", "-aq", env=up.environment) == "", "a container is still here"
    assert docker("image", "ls", "-q", up.image) == "", f"{up.image} is still here"
    for kind in ("volume", "network"):
        left = docker(
            kind, "ls", "-q", "--filter", f"label=com.docker.compose.project={PROJECT}"
        )
        assert left == "", f"the project left a {kind} behind: {left}"
