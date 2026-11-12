"""The workflow that publishes both images to GHCR for an installation release
(rails49/.github#71 d.1, d.2, d.8), read rather than run.

It runs only when the installation's release workflow calls it, so nothing in
a pull request can run it. What can be held here is what it is given and what
it names: that it is called and never triggered, that each image is built on
both architectures' own runners from the Dockerfile compose builds it from and
pushed under the name compose gives it, and that the box files it hands on are
the files a box needs.
"""

import json
import re
import textwrap

from tests.deploy.test_stack import (
    BASE,
    BOX,
    HTTPS,
    IMAGE,
    ROOT,
    UI_IMAGE,
    entries,
    services,
    uncommented,
)

WORKFLOW = ROOT / ".github" / "workflows" / "images.yml"


def under(*keys: str) -> str:
    """What one key path of the workflow holds, as written: an inline value, or
    the lines nested under it, dedented. Indentation is the whole parser, as it
    is for `services()`."""
    text = "\n".join(uncommented(WORKFLOW.read_text()))
    return within(text, *keys)


def within(text: str, *keys: str) -> str:
    """`under()` for a piece of the workflow already taken out of it."""
    for key in keys:
        lines = text.splitlines()
        at = next(i for i, line in enumerate(lines) if re.match(rf"{key}:(\s|$)", line))
        inline = lines[at][len(key) + 1 :].strip()
        if inline and not inline.startswith((">", "|")):
            text = inline
            continue
        nested: list[str] = []
        for line in lines[at + 1 :]:
            if line and not line[0].isspace():
                break
            nested.append(line)
        text = textwrap.dedent("\n".join(nested))
    return text


def keys(text: str) -> list[str]:
    """The keys of one mapping, in order."""
    return [line.split(":")[0] for line in text.splitlines() if re.match(r"\S", line)]


def items(text: str) -> list[str]:
    """The items of one list, each dedented as a mapping."""
    found: list[str] = []
    for line in text.splitlines():
        if line.startswith("- "):
            found.append("")
            line = "  " + line[2:]
        found[-1] += line + "\n"
    return [textwrap.dedent(item) for item in found]


def images() -> dict[str, str]:
    """Each image the workflow publishes, by its name under ghcr.io/rails49,
    and the Dockerfile it builds it from."""
    return {i["name"]: i["file"] for i in json.loads(under("env", "IMAGES"))}


def test_the_images_are_built_when_a_release_calls_for_them_and_never_else() -> None:
    """No pull request or merge builds or pushes an image (#71 d.1). The
    installation release names the commit (d.8)."""
    assert keys(under("on")) == ["workflow_call"]
    assert (
        within(under("on", "workflow_call", "inputs", "commit"), "required") == "true"
    )
    assert within(under("on", "workflow_call", "inputs", "commit"), "type") == "string"


def test_each_image_is_built_on_each_architectures_own_runner() -> None:
    """amd64 and arm64, each native (#71 d.2, rails49/.github#70)."""
    runners = under("jobs", "build", "strategy", "matrix", "runner")
    assert runners == "[ubuntu-24.04, ubuntu-24.04-arm]"


def built_by_compose() -> dict[str, str]:
    """Each image compose names, without its commit, and the Dockerfile it
    builds it from."""
    built: dict[str, str] = {}
    for block in (*services(BASE).values(), *services(BOX).values()):
        image = re.search(
            r"^ +image: (\S+):\$\{DCCEX_COMMIT:-dev\}$", block, re.MULTILINE
        )
        file = re.search(r"^ +dockerfile: (\S+)$", block, re.MULTILINE)
        if image and file:
            built[image.group(1)] = file.group(1)
    return built


def test_each_image_is_published_under_the_name_compose_builds_it_under() -> None:
    """A box that builds and a box that pulls name the same image, from the
    same Dockerfile (#71 d.5)."""
    published = {f"ghcr.io/rails49/{name}": file for name, file in images().items()}
    assert published == built_by_compose()
    assert set(published) == {IMAGE, UI_IMAGE}


def test_the_outputs_are_both_images_digests() -> None:
    """What the installation release pins (#71 d.10)."""
    outputs = under("on", "workflow_call", "outputs")
    assert keys(outputs) == list(images())
    for name in images():
        joined = f"${{{{ jobs.join.outputs.{name} }}}}"
        assert within(outputs, name, "value") == joined


def test_each_build_is_given_the_commit_for_its_revision() -> None:
    """Both Dockerfiles turn `DCCEX_COMMIT` into
    `org.opencontainers.image.revision` (ADR-0005 d.4)."""
    steps = items(under("jobs", "build", "steps"))
    build = next(step for step in steps if "id: build\n" in step)
    assert within(build, "with", "build-args") == "DCCEX_COMMIT=${{ inputs.commit }}"
    assert within(build, "with", "context") == "."


def test_the_box_files_are_the_compose_files_and_what_they_mount() -> None:
    """The installation's release archives them, and a box needs no clone
    (#71 d.10). A bind mount of a path in this repository starts with `.`."""
    steps = items(under("jobs", "box-files", "steps"))
    upload = next(step for step in steps if "name: dccex-box-files\n" in step)
    uploaded = set(within(upload, "with", "path").split())
    mounted = {
        re.sub(r"^\./", "", volume.split(":")[0])
        for compose in (BASE, BOX, HTTPS)
        for block in services(compose).values()
        for volume in entries(block, "volumes")
        if volume.startswith(".")
    }
    assert uploaded == {
        "compose.yaml",
        "compose.box.yaml",
        "compose.https.yaml",
        *mounted,
    }
