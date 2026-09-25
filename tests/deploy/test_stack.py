"""The stack a box runs, held to what a box needs of it.

Everything here reads the files. What they do when a daemon runs them is
`test_mirror_serves.py`'s, which builds the image and exercises 2560 against
it, and `tests/ui/test_compose_serves.py`'s, which brings the project up and
reads the page's route off the running container. Those two carry the `docker`
marker and the gate does not collect them; this file is in the gate, because
the claims below are about what is written down and a machine with no daemon
can still be held to them.

The deploy is run as well as read, and that is `test_deploy_runs.py`'s: what a
failed `up` leaves in `.env` is a sequence rather than a line, so the program
the heredoc is goes through `bash` here against a clone the suite makes (#83).
It needs no daemon either, so it is in the gate beside this. What
`scripts/deploy.sh` says is still this file's.

The claims are the ones a box would otherwise discover: that the project is
pinned by name, that the shared network is joined rather than created, that a
missing box declaration stops the stack by name, that the device mapping
`control` deleted is recreated on both sides, that 2560 is on the LAN and the
face's port is on nothing, that the door is handed the page and the face on
one host with the face's prefix stripped and 2560 routed by nobody, that neither image's bases can move underneath a
name that never moves, that the mirror is given a flash to be waited out and
the cutover's stop is bounded by something else, that the repository a box
pulls from is written down rather than taken from whoever ran the deploy, and
that the deploy names the image after the commit and writes down what it
replaced.
"""

import re
import stat
from pathlib import Path

from dccex_usb.face import PORT as FACE_PORT

ROOT = Path(__file__).resolve().parent.parent.parent

#: The clean clone's half: the page, the project's name, and a network it
#: creates for itself.
BASE = ROOT / "compose.yaml"

#: The box's half: the mirror, the shared network external, and the
#: declaration required rather than defaulted.
BOX = ROOT / "compose.box.yaml"

DOCKERFILE = ROOT / "deploy" / "Dockerfile"

#: The page's own, which is the second image of a commit (ADR-0005 d.2, as
#: amended) and is built by the clean clone's half above.
UI_DOCKERFILE = ROOT / "deploy" / "ui.Dockerfile"

#: The repository, written on the image beside the revision. It names a
#: repository and not a build, so nothing a build is or is not given moves it.
SOURCE = "org.opencontainers.image.source=https://github.com/rails49/dccex"

#: A base image as either build names one: the readable tag, and beside it the
#: one build that tag pointed at when the pin was made.
PINNED = re.compile(r"FROM (\S+:\S+)@sha256:[0-9a-f]{64}(?: AS \w+)?")

DEPLOY = ROOT / "scripts" / "deploy.sh"

#: The page the evening the port changes hands is followed from. Its check 6
#: stops this stack's container with a client on 2560 that has stopped
#: reading, which is where the grace below is read as something it is not.
CUTOVER = ROOT / "docs" / "cutover.md"

#: The room a flash is waited out in: `firmware.py` allows esptool 300 seconds
#: and a container killed in the middle of a write leaves the command station
#: half written (#15). It is not what a stop takes, and it is not to be tidied
#: down to one.
GRACE = "stop_grace_period: 330s"

#: What check 6 holds a healthy stop to, spelt as both files spell it. A
#: shutdown with nothing being written is about a second — the face closed,
#: the clients aborted, the device let go — and this is the wall clock that
#: separates that from a shutdown waiting on a client that will never read.
BOUND = "five seconds"

GATE = ROOT / "scripts" / "check.sh"

#: The box's declaration of itself. Root-owned, edited by hand, and named in
#: every sentence that refuses to come up without it.
DECLARATION = "/etc/rails49/box.env"

#: The prefix the face answers under on the page's origin, which the door
#: strips (ADR-0004 d.2). The page spells it once, in `FACE_TS`, and the
#: overlay spells it in its route; a test holds the two together.
PREFIX = "/dccex-usb"

FACE_TS = ROOT / "ui" / "src" / "face.ts"

#: The one host both routers answer for, as the overlay writes it.
HOST = "Host(`dccex.${BOX_DOMAIN}`)"

#: What a box has run, one line per deploy (ADR-0005 d.5).
RECORD = "/var/lib/rails49/deploys/dccex"

#: The repository a box's clone is pointed at and pulls from. It is written
#: into the script rather than read out of the environment (#102): which
#: repository a box deploys is this checkout's answer and not the surrounding
#: shell's.
ORIGIN = "https://github.com/rails49/dccex.git"

#: The command station's device on the box this deploys to: a symlink to
#: whichever `ttyUSB` the node came up as, which is why it is the `by-id` path
#: and not the number.
BY_ID = "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0"

#: What the device is called inside the container. It is the app's own default
#: argument and what this repository's prose has always said, and it was the
#: container side of `control`'s `devices:` entry before that.
INSIDE = "/dev/dccex"


def uncommented(text: str) -> list[str]:
    """The file's lines with its prose taken out.

    Every claim below is about what compose is given, and these files carry
    more comment than declaration: a check that searched the whole text would
    find `traefik` in a paragraph explaining why the mirror has no route.
    """
    return [line for line in text.splitlines() if not line.lstrip().startswith("#")]


def services(compose: Path) -> dict[str, str]:
    """Each service's block of one compose file, by name.

    Indentation is the whole parser. It is enough for what is asked below —
    which service declares what — and it needs nothing installed, which is
    what keeps this in the gate.
    """
    blocks: dict[str, list[str]] = {}
    name = ""
    inside = False
    for line in uncommented(compose.read_text()):
        if line and not line[0].isspace():
            inside = line.startswith("services:")
            name = ""
            continue
        if not inside:
            continue
        started = re.fullmatch(r"  (\w[\w-]*):\s*", line)
        if started is not None:
            name = started.group(1) or ""
            blocks[name] = []
        elif name:
            blocks[name].append(line)
    return {name: "\n".join(body) for name, body in blocks.items()}


def comment_above(path: Path, line: str) -> str:
    """The paragraph written over one line of a file.

    What a declaration is given is `services()`'s, which drops every comment
    because a claim about what compose is handed cannot be met by prose. This
    is the opposite read, for the one claim below that is about the prose: a
    number whose reasons are not beside it is a number the next reader
    re-derives.
    """
    lines = path.read_text().splitlines()
    above = lines.index(line)
    taken: list[str] = []
    while above and lines[above - 1].lstrip().startswith("#"):
        above -= 1
        taken.append(lines[above])
    return "\n".join(reversed(taken))


def check_six() -> str:
    """The deaf-client step of the cutover page, as its reader meets it."""
    said = CUTOVER.read_text()
    start = said.index("\n6. ")
    return said[start : said.index("\n## ", start)]


def entries(block: str, key: str) -> list[str]:
    """One list-valued key of a service block, as it is written."""
    listed: list[str] = []
    taking = False
    for line in block.splitlines():
        if re.fullmatch(rf"    {key}:\s*", line):
            taking = True
        elif taking and (item := re.fullmatch(r"      - (.*)", line)) is not None:
            listed.append(item.group(1).strip().strip('"'))
        elif taking and line.strip():
            break
    return listed


def test_the_project_is_pinned_by_name_and_the_overlay_inherits_it() -> None:
    """`name: dccex` is the base's, and the overlay declares no name of its
    own — so ADR-0005 d.7's `.env` is one project's and both files resolve to
    it."""
    assert "name: dccex" in uncommented(BASE.read_text())
    assert [
        line for line in uncommented(BOX.read_text()) if line.startswith("name:")
    ] == []


def test_the_shared_network_is_external_on_a_box_and_not_in_a_clean_clone() -> None:
    """The reconciliation the two files are for.

    A clean clone must come up with no box behind it, so the base declares no
    `rails49` at all. A box joins the installation's rather than creating a
    second one under the same name, so the overlay declares it external.
    """
    base = "\n".join(uncommented(BASE.read_text()))
    assert not re.search(r"^networks:", base, re.MULTILINE), (
        "the clean clone declares a network, and an external one would refuse"
        " to come up where the installation has not run"
    )
    box = "\n".join(uncommented(BOX.read_text()))
    assert re.search(r"^networks:\n  rails49:\n    external: true$", box, re.MULTILINE)


def test_the_page_joins_the_network_the_door_dials_it_on() -> None:
    """The label has named `rails49` since it was written; this is the line
    that puts the container on it."""
    assert entries(services(BOX)["web"], "networks") == ["default", "rails49"]


def test_a_missing_box_declaration_stops_the_stack_by_name() -> None:
    """Compose's `:?`, on the one value a box must declare. Without the
    declaration the stack does not come up on a default that is wrong for a
    box — it stops, and the sentence names the file to go and look at.

    It is a top-level line of its own and not a default inside a label (#40),
    so a route can be rewritten without taking the guard with it."""
    guards = [
        line
        for line in uncommented(BOX.read_text())
        if re.search(r"\$\{BOX_DOMAIN:\?", line)
    ]
    assert len(guards) == 1, guards
    assert guards[0].startswith("x-require-box-domain: ${BOX_DOMAIN:?")
    assert DECLARATION in guards[0]


def test_the_deploy_refuses_a_box_with_no_declaration_before_it_pulls() -> None:
    """The same guard on the other side of the ssh, so that nothing is pulled
    or built on a box the installation has not been run on."""
    said = DEPLOY.read_text()
    assert '[ ! -r "\\$box_env" ]' in said
    assert f"BOX_ENV={DECLARATION}" in said


def test_the_device_mapping_control_deleted_is_recreated_on_both_sides() -> None:
    """There is no udev rule in any repository and there never was one:
    `/dev/dccex` was the container side of `control`'s entry, and this is the
    entry."""
    assert entries(services(BOX)["mirror"], "devices") == [
        f"${{DCCEX_STATION_DEVICE:-{BY_ID}}}:{INSIDE}"
    ]


def test_the_mirror_publishes_2560_and_the_face_is_published_by_nothing() -> None:
    """2560 raw on the LAN, because it always has been and JMRI has no other
    way in. The face's port is not beside it: it writes firmware onto the
    command station, and it reaches a browser through the door or not at all
    (ADR-0004 d.1, d.5)."""
    ports = entries(services(BOX)["mirror"], "ports")
    assert ports == ["2560:2560"]
    assert all(not port.endswith(f":{FACE_PORT}") for port in ports)


def test_the_mirror_runs_the_device_and_the_port_the_mapping_names() -> None:
    """The flags compose passes, against the names above rather than against
    themselves: a stack that mapped the device to one name and opened another
    would come up and mirror nothing."""
    assert f'"--device", "{INSIDE}", "--port", "2560"' in services(BOX)["mirror"]


def test_the_mirrors_grace_is_a_flashs_and_names_the_page_a_stop_is_on() -> None:
    """330 seconds, and the reasons beside it (#15).

    The value is what a flash is allowed and the paragraph over it has said so
    since it was written. What is asserted with it is the other half (#103):
    that the same paragraph names the page which bounds a stop, so that the
    number cannot be read as what stopping this container should take. A
    reader who has only the first half re-derives the conflict that made the
    cutover's check 6 measure nothing.
    """
    assert GRACE in services(BOX)["mirror"], "the grace moved, or went"
    beside = comment_above(BOX, f"    {GRACE}")
    assert "docs/cutover.md" in beside, "the grace does not point at the page"
    assert BOUND in beside, "the grace does not say what a stop is held to"


def test_the_cutovers_stop_is_bounded_by_a_clock_and_not_by_the_grace() -> None:
    """Check 6's reading, against the grace it is not (#103).

    The step was written against Docker's ten seconds, which this container
    has not had since the grace landed: a mirror that hangs on shutdown is not
    killed at ten seconds any more, it is waited out for five and a half
    minutes and then killed, and comes back dead of `137` (#114, and
    `docs/cutover.md` beside it). The exit status does tell a hung stop from a
    healthy one — only not until those five and a half minutes are up, and
    nobody has to stand there for them. So the page states a wall clock a
    healthy stop meets and a hung one misses, times the stop to read the same
    fault straight away, and says what the 330 seconds are instead — all three
    asserted here, because a page that dropped any of them is a check that
    passes either way.
    """
    said = check_six()
    assert "time docker stop" in said, "the stop is not timed"
    assert BOUND in said, "check 6 states no bound a stop is held to"
    assert "ten-second" not in said, "check 6 still reads Docker's default"
    assert "330" in said, "check 6 does not say what the configured grace is"


def labels(compose: Path, service: str) -> dict[str, str]:
    """One service's door labels in one file, as a key and what it is set to."""
    return dict(
        label.split("=", 1)
        for label in entries(services(compose)[service], "labels")
        if label.startswith("traefik.")
    )


def test_only_the_page_and_the_mirror_carry_door_labels() -> None:
    """Only a container a browser reaches carries a route (ADR-0004 d.5). The
    face is in the mirror's container, so the mirror is one of them."""
    carrying = {
        name
        for compose in (BASE, BOX)
        for name, block in services(compose).items()
        if "traefik." in block
    }
    assert carrying == {"web", "mirror"}


def test_the_mirrors_route_dials_the_face_and_nothing_routes_2560() -> None:
    """The mirror's one service is the face's port, taken from the package
    rather than written again, and 2560 is named by no label (d.5)."""
    face = labels(BOX, "mirror")
    ports = {v for k, v in face.items() if k.endswith(".loadbalancer.server.port")}
    assert ports == {str(FACE_PORT)}
    assert not [v for v in face.values() if "2560" in v]


def test_the_page_yields_the_prefix_to_the_face() -> None:
    """Two routers on one host. The page's is the catch-all at priority 1 and
    the face's claims `/dccex-usb` at 2; in Traefik the higher one wins, so the
    page keeps everything the face does not claim (ADR-0004 d.2)."""
    page = labels(BOX, "web") | {
        k: v for k, v in labels(BASE, "web").items() if not k.endswith(".rule")
    }
    face = labels(BOX, "mirror")
    assert page["traefik.http.routers.dccex-ui.rule"] == HOST
    assert page["traefik.http.routers.dccex-ui.priority"] == "1"
    assert face["traefik.http.routers.dccex-usb.rule"] == (
        f"{HOST} && PathPrefix(`{PREFIX}`)"
    )
    assert face["traefik.http.routers.dccex-usb.priority"] == "2"


def test_the_prefix_is_stripped_as_the_page_spells_it() -> None:
    """The face answers `/releases`, not `/dccex-usb/releases`, and the prefix
    the door strips is the one the page builds every address from."""
    face = labels(BOX, "mirror")
    middleware = face["traefik.http.routers.dccex-usb.middlewares"]
    assert face[f"traefik.http.middlewares.{middleware}.stripprefix.prefixes"] == (
        PREFIX
    )
    assert f'export const FACE = "{PREFIX}";' in FACE_TS.read_text()


def test_the_face_joins_the_network_the_door_dials_it_on() -> None:
    """The mirror joins `rails49` for its face, and the label names it."""
    assert entries(services(BOX)["mirror"], "networks") == ["default", "rails49"]
    assert labels(BOX, "mirror")["traefik.docker.network"] == "rails49"


def test_a_foreign_origin_is_the_faces_to_refuse_and_not_the_doors() -> None:
    """No `-foreign` router and no middleware that answers for the face: the
    face refuses with a status and a sentence (`face.py`, ADR-0004 d.4), and
    nothing on the route rewrites the `Host` that refusal compares against."""
    face = labels(BOX, "mirror")
    routers = {k.split(".")[3] for k in face if k.startswith("traefik.http.routers.")}
    assert routers == {"dccex-usb"}
    middlewares = {
        k.split(".")[3] for k in face if k.startswith("traefik.http.middlewares.")
    }
    assert middlewares == {"dccex-usb-strip"}
    assert not [k for k in face if "headers" in k or "passhostheader" in k.lower()]


def test_both_images_are_named_by_the_commit_they_were_built_from() -> None:
    """ADR-0005 d.1, and one variable for the two: the page and the mirror are
    two images of one commit, so going back is the one line d.7 asks for."""
    assert "image: dccex:${DCCEX_COMMIT:-dev}" in services(BOX)["mirror"]
    assert "image: dccex-ui:${DCCEX_COMMIT:-dev}" in services(BASE)["web"]


def test_the_image_carries_the_commit_as_well_as_being_named_by_it() -> None:
    """So that `docker inspect` answers the question for one somebody renamed
    (ADR-0005 d.4).

    The default is empty and the overlay hands the build the same variable the
    name is built from — the page's rule since #57, and this image's since #97.
    `dev` is a true thing to call a name and a false thing to put in a field
    that means the commit this was built from: it reads like a commit
    reference, it is none, and it would send somebody looking for a checkout
    that never existed, where an empty revision can only be read as nobody
    having named one. The name is still `dev`, which is the test above.

    What a built image then carries is `test_mirror_serves.py`'s, which builds
    it rather than reading it. The repository beside the revision is asserted
    here because nothing a build is or is not given moves it.
    """
    said = DOCKERFILE.read_text()
    assert re.search(r"^ARG DCCEX_COMMIT=$", said, re.MULTILINE), (
        "the mirror's image takes no commit, or defaults it to something that"
        " reads like one"
    )
    assert "LABEL org.opencontainers.image.revision=$DCCEX_COMMIT" in said
    assert f"LABEL {SOURCE}" in said
    assert "DCCEX_COMMIT: ${DCCEX_COMMIT:-}" in services(BOX)["mirror"]


def test_the_pages_build_is_handed_the_commit_its_name_is_built_from() -> None:
    """The same rule for the second image, which had only the name (#57).

    The build takes the argument the page's image records, and the project
    passes it the variable the name is built from — one value, so a `docker
    inspect` and the name can never say different commits. Its fallback is
    empty where the name's is `dev`: `dev` names an image nobody named a
    commit for, and a revision that reads like a commit reference and is none
    is worse than no revision at all (`deploy/ui.Dockerfile`).

    What a built image then carries is `tests/ui/test_page_serves.py`'s and
    `tests/ui/test_compose_serves.py`'s, which run it rather than read it.
    """
    said = UI_DOCKERFILE.read_text()
    assert re.search(r"^ARG DCCEX_COMMIT=$", said, re.MULTILINE), (
        "the page's image takes no commit, or defaults it to something that"
        " reads like one"
    )
    assert "LABEL org.opencontainers.image.revision=$DCCEX_COMMIT" in said
    assert "DCCEX_COMMIT: ${DCCEX_COMMIT:-}" in services(BASE)["web"]


def test_the_pages_bases_are_pinned_by_digest_with_the_tag_kept_beside_it() -> None:
    """ADR-0005 d.1 — one commit, one image, one name — is not true of a build
    whose bases move underneath it, and d.7's rebuild of an older commit does
    not reproduce what shipped (#59). A digest names one artefact and cannot
    be republished; the tag is kept beside it because a digest says nothing to
    a reader about what the image is.

    What the built image then contains is `tests/ui/test_page_serves.py`'s,
    which runs it. This is the claim a machine with no daemon can be held to:
    that neither `FROM` line names something that can move.
    """
    froms = [
        line
        for line in uncommented(UI_DOCKERFILE.read_text())
        if line.startswith("FROM ")
    ]
    floating = [line for line in froms if PINNED.fullmatch(line) is None]
    assert floating == [], f"a base that can move under the build: {floating}"
    pinned = [match.group(1) for line in froms if (match := PINNED.fullmatch(line))]
    assert pinned == ["node:22-alpine", "nginx:alpine"], (
        "the page is not built by node and served by nginx any more, or the"
        " tag a reader reads the pin by is gone"
    )


def test_the_page_says_how_a_pin_is_moved_and_that_moving_it_is_a_commit() -> None:
    """A pin nobody knows how to move is a base that never takes a security
    update again, so what it costs and how it is paid are written beside the
    two lines it is about (#59): the command that resolves a tag to a digest,
    on a machine that can reach a registry, and that what comes back is
    committed here rather than resolved during a build.

    The prose only. The pins themselves are the check above, and a sentence
    about them in a paragraph is not one of them.
    """
    prose = "\n".join(
        line
        for line in UI_DOCKERFILE.read_text().splitlines()
        if line.lstrip().startswith("#")
    )
    assert (
        "docker buildx imagetools inspect" in prose
    ), "the pins do not say what resolves a tag to a digest"
    assert (
        "a commit of this repository" in prose
    ), "the pins do not say that moving one is a commit like any other"


def test_the_mirrors_bases_are_pinned_by_digest_with_the_tag_kept_beside_it() -> None:
    """The same claim as the page's above, about the other image (#96). This
    one was written where no registry was reachable, so it carried two tags
    that move underneath a name ADR-0005 d.1 says never moves, and the file
    said so and called pinning them a ticket of its own. This is that ticket
    done: the digests were read on a machine that could reach both registries
    and written down.

    Shape and not values here too. What the pinned image then does is
    `tests/deploy/test_mirror_serves.py`'s, which builds it and dials 2560.
    """
    froms = [
        line for line in uncommented(DOCKERFILE.read_text()) if line.startswith("FROM ")
    ]
    floating = [line for line in froms if PINNED.fullmatch(line) is None]
    assert floating == [], f"a base that can move under the build: {floating}"
    pinned = [match.group(1) for line in froms if (match := PINNED.fullmatch(line))]
    assert pinned == [
        "ghcr.io/astral-sh/uv:python3.12-bookworm-slim",
        "python:3.12-slim-bookworm",
    ], (
        "the image is not built by uv and run on python:3.12 any more, or the"
        " tag a reader reads the pin by is gone"
    )


def test_the_mirror_says_how_a_pin_is_moved_and_when_the_digests_were_read() -> None:
    """A pin nobody knows how to move is a base that never takes a security
    update again, so the procedure is beside the lines it is about here as it
    is beside the page's: the command that resolves a tag to a digest on a
    machine that can reach a registry, and that what comes back is committed
    here rather than resolved during a build (#96).

    And the day they were read, because a pin says nothing about how old it is
    and somebody has to decide whether to move it. The date is held as a date
    and not as a value: moving a pin moves it.

    The argument itself is `ui.Dockerfile`'s and this file points at it rather
    than repeating it, so that is asserted too. The prose only — the pins
    themselves are the check above.
    """
    prose = "\n".join(
        line
        for line in DOCKERFILE.read_text().splitlines()
        if line.lstrip().startswith("#")
    )
    assert (
        "docker buildx imagetools inspect" in prose
    ), "the pins do not say what resolves a tag to a digest"
    assert (
        "a commit of this repository" in prose
    ), "the pins do not say that moving one is a commit like any other"
    assert re.search(
        r"\b\d{4}-\d{2}-\d{2}\b", prose
    ), "the pins do not say when the digests were read"
    assert (
        "ui.Dockerfile" in prose
    ), "the pins do not point at where the argument for them is written"


def test_the_image_is_built_from_the_lock_file_and_not_from_the_index() -> None:
    """`--frozen` on every sync: a lock file that has drifted from
    `pyproject.toml` stops the build rather than being rewritten inside it,
    which is the rule the page's packages are already held to."""
    syncs = re.findall(r"uv sync[^\n]*", DOCKERFILE.read_text())
    assert syncs, "the image installs nothing from the lock file"
    assert all("--frozen" in sync and "--no-dev" in sync for sync in syncs)


def test_the_image_runs_the_mirror_on_its_own_defaults() -> None:
    """`docker run dccex:<commit>` is the mirror, with no Python on the host
    and nothing passed."""
    said = DOCKERFILE.read_text()
    assert 'ENTRYPOINT ["python", "-m", "dccex_usb"]' in said
    assert f'CMD ["--device", "{INSIDE}", "--port", "2560"]' in said


def test_the_deploy_is_a_program_a_box_can_be_deployed_by() -> None:
    """Executable, and `control`'s shape: one ssh, one login shell, no
    credential prompt, and an origin set rather than believed."""
    assert DEPLOY.stat().st_mode & stat.S_IXUSR
    said = DEPLOY.read_text()
    assert 'ssh "$BOX" bash -l <<REMOTE' in said
    assert "GIT_TERMINAL_PROMPT=0" in said
    assert "git remote set-url origin" in said
    assert "up -d --build --remove-orphans" in said
    assert '--env-file "\\$box_env"' in said


def test_the_origin_is_the_scripts_own_and_not_the_environments() -> None:
    """Which repository a box deploys is this checkout's answer (#102).

    The origin is set rather than believed, because a clone somebody had
    repointed by hand stopped a deploy dead — and a variable would have handed
    the shell that ran the deploy the very say that was taken off the box,
    under a comment saying the value comes from here. So the constant is
    asserted as written, and `DCCEX_ORIGIN` as gone: a default that happens to
    be this repository is still an override.

    It is set before the pull, which is the whole of what setting it is for: a
    fetch is what brings somebody else's commits onto the box, and an origin
    corrected afterwards would correct nothing. The box and the branch stay
    variables beside it — a different box or a different branch is an ordinary
    thing to want, and neither decides whose code runs.
    """
    said = DEPLOY.read_text()
    assert f"\nORIGIN={ORIGIN}\n" in said, "the origin is not a constant of the script"
    assert "DCCEX_ORIGIN" not in said, "the origin is read out of the environment"
    setting = said.index('git remote set-url origin "$ORIGIN"')
    assert setting < said.index("git fetch"), "the origin is set after the pull"
    assert re.search(r"^BOX=\$\{DCCEX_BOX:-", said, re.MULTILINE)
    assert re.search(r"^BRANCH=\$\{DCCEX_BRANCH:-", said, re.MULTILINE)


def test_the_deploy_refuses_a_clone_that_is_not_clean() -> None:
    """ADR-0005 d.4: the image's name would be a commit that is not what was
    built, and the name outlives whoever typed it."""
    said = DEPLOY.read_text()
    assert "git status --porcelain" in said
    assert "ADR-0005 d.4" in said


def test_the_deploy_writes_down_what_it_replaced_and_keeps_it() -> None:
    """One line per deploy, appended and never rewritten (d.5), and nothing
    pruned, so the image that went is the one step back (d.6)."""
    said = DEPLOY.read_text()
    assert '>> "\\$record"' in said
    assert f"RECORD={RECORD}" in said
    ran = "\n".join(uncommented(said)).replace("git fetch --prune", "")
    assert "prune" not in ran and "--rmi" not in ran, "the deploy prunes something"


def test_the_rollback_never_builds() -> None:
    """ADR-0005 d.7 as amended for #41: with the old image pruned, a plain
    `up -d` builds the current checkout under the older commit's name."""
    for page in (DEPLOY, ROOT / "docs" / "dccex_usb" / "README.md"):
        said = page.read_text()
        assert "--env-file .env up -d --no-build" in said, page.name
        bare = re.search(r"--env-file \.env up -d$", said, re.MULTILINE)
        assert not bare, page.name


def test_the_gate_is_still_one_command_with_one_exit_code() -> None:
    """The check that starts the built image needs a daemon and the page's
    JavaScript modules need a node, so each carries a marker and the gate
    collects neither (#54, #56, #101). Nothing in this ticket moved that
    line."""
    assert '-m "not docker and not node"' in GATE.read_text()
