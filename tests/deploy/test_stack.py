"""The stack a box runs, held to what a box needs of it.

Everything here reads the files. What they do when a daemon runs them is
`test_mirror_serves.py`'s, which builds the image and exercises 2560 against
it, and `tests/ui/test_compose_serves.py`'s, which brings the project up and
reads the page's route off the running container. Those two carry the `docker`
marker and the gate does not collect them; this file is in the gate, because
the claims below are about what is written down and a machine with no daemon
can still be held to them.

The claims are the ones a box would otherwise discover: that the project is
pinned by name, that the shared network is joined rather than created, that a
missing box declaration stops the stack by name, that the device mapping
`control` deleted is recreated on both sides, that 2560 is on the LAN and the
face's port is on nothing, that the page's two bases cannot move underneath a
name that never moves, and that the deploy names the image after the commit
and writes down what it replaced.
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

#: A base image as the page's build names one: the readable tag, and beside it
#: the one build that tag pointed at when the pin was made.
PINNED = re.compile(r"FROM (\S+:\S+)@sha256:[0-9a-f]{64}(?: AS \w+)?")

DEPLOY = ROOT / "scripts" / "deploy.sh"

GATE = ROOT / "scripts" / "check.sh"

#: The box's declaration of itself. Root-owned, edited by hand, and named in
#: every sentence that refuses to come up without it.
DECLARATION = "/etc/rails49/box.env"

#: What a box has run, one line per deploy (ADR-0005 d.5).
RECORD = "/var/lib/rails49/deploys/dccex"

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
    box — it stops, and the sentence names the file to go and look at."""
    guard = re.search(r"\$\{BOX_DOMAIN:\?([^}]*)\}", BOX.read_text())
    assert guard is not None, "BOX_DOMAIN has no `:?` guard on it"
    assert DECLARATION in guard.group(1)


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


def test_no_container_in_this_project_carries_a_door_label_but_the_page() -> None:
    """Only a container a browser reaches carries a route (ADR-0004 d.5)."""
    carrying = {
        name
        for compose in (BASE, BOX)
        for name, block in services(compose).items()
        if "traefik." in block
    }
    assert carrying == {"web"}


def test_both_images_are_named_by_the_commit_they_were_built_from() -> None:
    """ADR-0005 d.1, and one variable for the two: the page and the mirror are
    two images of one commit, so going back is the one line d.7 asks for."""
    assert "image: dccex:${DCCEX_COMMIT:-dev}" in services(BOX)["mirror"]
    assert "image: dccex-ui:${DCCEX_COMMIT:-dev}" in services(BASE)["web"]


def test_the_image_carries_the_commit_as_well_as_being_named_by_it() -> None:
    """So that `docker inspect` answers the question for one somebody renamed
    (ADR-0005 d.4)."""
    said = DOCKERFILE.read_text()
    assert "ARG DCCEX_COMMIT=dev" in said
    assert "LABEL org.opencontainers.image.revision=$DCCEX_COMMIT" in said


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


def test_the_gate_is_still_one_command_with_one_exit_code() -> None:
    """The check that starts the built image needs a daemon and the page's five
    JavaScript modules need a node, so each carries a marker and the gate
    collects neither (#54, #56, #101). Nothing in this ticket moved that
    line."""
    assert '-m "not docker and not node"' in GATE.read_text()
