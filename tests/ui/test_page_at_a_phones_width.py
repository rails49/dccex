"""The page laid out at a phone's width, in a browser that does layout.

Everything else about how the page is shaped is read off the stylesheet it is
written in. That is not a habit, it is what the machines allowed: the gate is
Python with no browser in it, and happy-dom — which is what mounts the
components in the `node` job — draws no boxes, so a width, a wrap or an
element that is off the side of the screen is not a thing either of them can
see (`ui/test/mounted.ts`, `tests/ui/test_band.py`). The narrow-width rules
were therefore written and never rendered, which is what #1's Further Notes
recorded as "narrow widths were not verified" and what this is (#127).

So: a real Chromium, against the built page image, at 375px and at a desktop
width. It is the same artefact `tests/ui/test_page_serves.py` builds — the
image the box will serve — which is the other half of why this is the `docker`
job's and not a job of its own: #1 asks that one check run the thing in the
image it will run in, and a layout check that drove `vite dev` would be
asserting a page nobody ships.

**The browser is a container and not a dependency.** Nothing is added to
`pyproject.toml` and nothing is installed on the machine: the driver below is
handed to `python` inside the Playwright image, which carries the browsers,
and that container joins the page container's own network namespace, so the
address it loads is `http://127.0.0.1/` and no port has to be agreed between
them. The gate is untouched by all of it, which is the criterion #127 ends on.

**There is no face behind the page here**, so the stream never opens, the link
reads as not answering and the build is blank — the "nothing said" state, and
enough for layout. The one exception is the release list: rows are what the
wrap rule is about, and a page with none of them cannot be asked whether they
wrap, so the browser answers that one request with three releases and nothing
else is stood up. They go in through the page's own `fetch`, so what is
measured is the rows the page draws rather than a shape poked into a
component.

**This is not part of the gate.** It carries the `docker` marker, which
`scripts/check.sh` does not collect, and the workflow runs it in the job that
already builds and serves this image, where a missing daemon is a failure and
not a skip (#54, #56). Run by hand on a machine with no daemon it skips and
says why.
"""

import json
import os
import subprocess
import uuid
from collections.abc import Iterator
from typing import Any, cast

import pytest

from tests.ui.test_page_serves import (
    BUILD_SECONDS,
    DOCKERFILE,
    docker,
    no_daemon,
    published,
    wait_until_answering,
)

pytestmark = pytest.mark.docker

#: The browser, and the machine it needs, in one image: Chromium and its
#: libraries. The `playwright` package that drives it is not in the image and
#: is installed at the tag's version on each run (`DRIVE`). It is pinned by tag
#: rather than by digest — unlike the two bases `deploy/ui.Dockerfile` pins,
#: because nothing ships out of this one and a republished tag here changes
#: what a check ran in rather than what a box serves. Moving it is the same
#: gesture: a newer `vX.Y.Z` on the line below, and a run of the `docker` job.
#:
#: Nothing in the gate resolves it, for the reason the Dockerfile's digests
#: are not resolved either: that needs a registry. A name that is not there
#: is this check failing where it runs, with what the daemon said.
PLAYWRIGHT = "mcr.microsoft.com/playwright/python:v1.49.0-noble"

#: Install the package that matches the image's browsers, then run the driver
#: with the arguments that follow it: `$0` is the driver, `$@` the rest.
DRIVE = (
    f"pip install -q --break-system-packages playwright=={PLAYWRIGHT.split(':v')[1].split('-')[0]}"
    ' && exec python -c "$0" "$@"'
)

#: Where the page is, from inside the browser's container. It shares the page
#: container's network namespace (`--network=container:…`), so the server is on
#: its own loopback and the published host port is nobody's business but
#: `wait_until_answering`'s.
PAGE = "http://127.0.0.1/"

#: A phone held upright, which is the thing at the layout: an iPhone's CSS
#: width and height. 375 is under the 560 the band turns at and is the
#: narrowest width anybody reads this page on.
PHONE = (375, 812)

#: A desktop, which is where the rules that are dropped below 560px have to go
#: on holding.
DESKTOP = (1280, 800)

#: The two of them, in the order the browser walks them, by the name the
#: assertions below ask for them under.
WIDTHS = {"phone": PHONE, "desktop": DESKTOP}

#: What the browser answers the face's release request with. Three releases,
#: because rows are what the wrap rule is about and the nothing-said state has
#: none — and the fields are the three the face passes on and no more
#: (`ui/src/releases.js`, `carried()`).
CARRIED = [
    {
        "tag": "v5.2.76-rails49-2026-08-03",
        "published": "2026-08-03T09:00:00Z",
        "flashable": True,
    },
    {"tag": "v5.2.75", "published": "2026-07-02T09:00:00Z", "flashable": False},
    {"tag": "v5.2.74", "published": "2026-06-01T09:00:00Z", "flashable": True},
]

#: The tag long enough that its row cannot fit on one line at 375px. A real
#: one: the fork stamps the day into the name, so this is the length an
#: operator actually reads, and it is what the wrap rule was written for.
LONG = "v5.2.76-rails49-2026-08-03"

#: Where the page asks the face for them, as a pattern the browser matches the
#: request against. The path is `face.ts`'s `RELEASES_PATH`; nothing else the
#: page asks for is answered, so everything else is the state a page with no
#: face behind it draws.
RELEASES = "**/dccex-usb/releases"

#: What is typed into the command box, and read back out of it. It asks the
#: station what it is running and it is never sent — there is no stream open
#: to send it on and nothing here presses the send.
TYPED = "<s>"

#: A pixel of slack on a comparison between two rendered edges. Layout is
#: worked out in fractions and rounded for painting, and a rule that read a
#: row as overflowing its own parent by a third of a pixel would be red about
#: nothing.
SLACK = 1.0

#: How long the browser gets, pull included. The image is a large one and the
#: `docker` job fetches it once per run.
DRIVE_SECONDS = 900

#: The program the Playwright image runs. It loads the page at each width,
#: measures what was drawn and prints one JSON line; every assertion about
#: what it measured is below, in Python, where a reader of a failure can see
#: what was expected.
#:
#: It is a string rather than a module beside this one because the gate's
#: tools read every `.py` under `tests/` and `playwright` is not installed in
#: the environment they run in: a file importing it would be a type error on
#: every machine but the one inside the container.
DRIVER = '''
import json
import sys

from playwright.sync_api import Route, sync_playwright

URL, RELEASES, TYPED = sys.argv[1], sys.argv[2], sys.argv[3]
CARRIED = json.loads(sys.argv[4])
WIDTHS = json.loads(sys.argv[5])

#: What the page drew, at one width. The command box is measured with the
#: release row shut, which is how the page opens; the rows are measured with
#: it open, because that is the only way anybody reads one.
MEASURE = """
() => {
  const box = (drawn) => {
    const at = drawn.getBoundingClientRect();
    return {
      top: at.top, right: at.right, bottom: at.bottom, left: at.left,
      width: at.width, height: at.height,
    };
  };
  const app = document.querySelector("dccex-app");
  const band = app.renderRoot.querySelector("dccex-band");
  const reading = (of) => {
    const drawn = band.renderRoot.querySelector(".reading." + of);
    return drawn === null ? null : box(drawn);
  };
  const monitor = app.renderRoot.querySelector("dccex-monitor");
  const typed = box(monitor.renderRoot.querySelector("input.typed"));
  const send = box(monitor.renderRoot.querySelector(".box button"));
  const releases = app.renderRoot.querySelector("dccex-releases");
  const row = releases.renderRoot.querySelector("details");
  const shut = document.documentElement.scrollWidth;
  row.open = true;
  const rows = [...releases.renderRoot.querySelectorAll(".release")].map(
    (release) => ({
      tag: release.querySelector(".tag").textContent,
      box: box(release),
      scrollWidth: release.scrollWidth,
      clientWidth: release.clientWidth,
      parts: [...release.children].map((part) => ({
        part: part.className,
        box: box(part),
      })),
    }),
  );
  const opened = document.documentElement.scrollWidth;
  row.open = false;
  return {
    innerWidth: window.innerWidth,
    innerHeight: window.innerHeight,
    scrollWidth: { shut: shut, opened: opened },
    link: reading("link"),
    rails: reading("rails"),
    typed: typed,
    send: send,
    rows: rows,
  };
}
"""


def answered(route: Route) -> None:
    """The one request a face would answer, answered."""
    route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps({"releases": CARRIED}),
    )


def measured(page, width, height):
    """The page loaded at one width, measured, and typed into."""
    page.set_viewport_size({"width": width, "height": height})
    page.goto(URL)
    page.wait_for_selector("input.typed")
    # Attached rather than visible: the release rows are inside a row that
    # opens, and a shut one draws nothing.
    page.wait_for_selector(".release", state="attached")
    drawn = page.evaluate(MEASURE)
    page.fill("input.typed", TYPED)
    drawn["reads"] = page.input_value("input.typed")
    return drawn


with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    context = browser.new_context()
    context.route(RELEASES, answered)
    page = context.new_page()
    drawn = {
        name: measured(page, width, height) for name, (width, height) in WIDTHS.items()
    }
    browser.close()

print(json.dumps(drawn))
'''


def lines(row: dict[str, Any]) -> int:
    """How many lines one release row's parts were laid out on.

    A flex line's boxes overlap each other vertically and never overlap the
    next line's, so a part whose top is at or below everything above it is on
    a line of its own. Counted rather than taken off the row's height: the
    parts are baseline-aligned and of three different sizes, so two of them
    side by side do not share a top and a taller row is not by itself a
    wrapped one.
    """
    drawn = sorted(
        (part["box"] for part in row["parts"] if part["box"]["height"] > 0),
        key=lambda box: cast(float, box["top"]),
    )
    counted = 0
    floor: float | None = None
    for box in drawn:
        if floor is None or box["top"] >= floor:
            counted += 1
            floor = cast(float, box["bottom"])
        else:
            floor = max(floor, cast(float, box["bottom"]))
    return counted


def row(drawn: dict[str, Any], tag: str) -> dict[str, Any]:
    """The one release row named `tag`, asserted to have been drawn."""
    found = [release for release in drawn["rows"] if release["tag"] == tag]
    assert len(found) == 1, f"{tag} was drawn {len(found)} times"
    return cast(dict[str, Any], found[0])


@pytest.fixture(scope="module")
def drawn() -> Iterator[dict[str, Any]]:
    """What a browser made of the built page, at each width, once.

    One build, one container and one browser for the whole module, as the
    check beside this one does it: the build is the expensive part and every
    assertion below is about the same artefact. It builds a second time where
    `tests/ui/test_page_serves.py` has already built, which is a layer cache
    hit and not a second build on any machine that keeps one.
    """
    why = no_daemon()
    if why is not None:
        # Where this is required — the workflow's docker job — the daemon is
        # part of what was promised, so its absence is the check failing and
        # not the check excusing itself (#54).
        if os.environ.get("CI"):
            pytest.fail(f"this job requires a Docker daemon: {why}")
        pytest.skip(f"the page cannot be drawn here: {why}")

    tag = f"dccex-ui:width-{uuid.uuid4().hex[:8]}"
    docker("build", "-f", DOCKERFILE, "-t", tag, ".", seconds=BUILD_SECONDS)
    container = ""
    try:
        container = docker("run", "-d", "-p", "127.0.0.1:0:80", tag)
        wait_until_answering(published(container))
        said = docker(
            "run",
            "--rm",
            # Chromium wants more than the default 64MB of shared memory, and
            # this is what Playwright's own page says to give it.
            "--ipc=host",
            f"--network=container:{container}",
            PLAYWRIGHT,
            "sh",
            "-c",
            DRIVE,
            DRIVER,
            PAGE,
            RELEASES,
            TYPED,
            json.dumps(CARRIED),
            json.dumps(WIDTHS),
            seconds=DRIVE_SECONDS,
        )
        # The last line, because a pull writes to this stream too.
        yield cast(dict[str, Any], json.loads(said.splitlines()[-1]))
    finally:
        if container:
            subprocess.run(
                ["docker", "rm", "-f", container], capture_output=True, check=False
            )
        subprocess.run(
            ["docker", "image", "rm", "-f", tag], capture_output=True, check=False
        )


def test_the_page_does_not_scroll_sideways_at_either_width(
    drawn: dict[str, Any],
) -> None:
    """Nothing on the page is off the side of it, at a phone's width or at a
    desktop's.

    A horizontal scrollbar on a page held in one hand is the failure this
    whole check exists to catch: it is what a rule that was written and never
    rendered produces, and it is invisible to every check that reads the
    stylesheet.

    With the release row shut, which is how the page opens, and with it open,
    which is the widest the page ever is: a long **tag** is the longest thing
    on it and it is behind the one control that hides something.
    """
    for width, page in drawn.items():
        for state, wide in page["scrollWidth"].items():
            assert wide <= page["innerWidth"] + SLACK, (
                f"the page is {wide}px wide in a {page['innerWidth']}px {width}"
                f" with the releases {state}"
            )


def test_the_narrow_band_draws_the_link_and_not_the_rails(
    drawn: dict[str, Any],
) -> None:
    """Below the width the band turns at, the reading that survives is whether
    the station is answering.

    `tests/ui/test_band.py` holds the rule as it is written — which reading the
    media query names, and that it is not the link, under the name this one
    borrows. What is held here is that a browser does it: the link is drawn and has a size at 375px, the rails reading has
    none, and at a desktop width both are there. The last of the three is what
    keeps the first two from passing on a page that drew no band at all.
    """
    phone, desktop = drawn["phone"], drawn["desktop"]
    assert (
        phone["link"] is not None and phone["link"]["width"] > 0
    ), "the narrow band drops the link"
    assert phone["rails"] is not None, "the band draws no rails reading at all"
    assert (
        phone["rails"]["width"] == 0 and phone["rails"]["height"] == 0
    ), f"the narrow band still draws the rails: {phone['rails']}"
    assert (
        desktop["rails"] is not None and desktop["rails"]["width"] > 0
    ), "the band drops the rails at every width"


def test_the_command_box_is_on_a_phone_s_screen_and_can_be_typed_into(
    drawn: dict[str, Any],
) -> None:
    """The one place a command is typed at the station, reachable on the thing
    it is typed on.

    Both halves: the field and the send are inside the viewport — the field
    shrinks rather than pushing the send off the side (docs/ui/README.md) — and
    a line typed into the field is in the field. Nothing is sent: there is no
    stream open here, and what a send does is `tests/ui/test_message.py`'s.
    """
    phone = drawn["phone"]
    for part in ("typed", "send"):
        box = phone[part]
        assert box["width"] > 0 and box["height"] > 0, f"the {part} was not drawn"
        assert (
            box["left"] >= -SLACK and box["right"] <= phone["innerWidth"] + SLACK
        ), f"the {part} is off the side of the screen: {box}"
        assert (
            box["top"] >= -SLACK and box["bottom"] <= phone["innerHeight"] + SLACK
        ), f"the {part} is off the screen: {box}"
    assert phone["reads"] == TYPED, "the command box could not be typed into"


def test_the_release_rows_wrap_on_a_phone_rather_than_running_off_the_side(
    drawn: dict[str, Any],
) -> None:
    """A long **tag** costs a line and never a reading.

    The date and what is said of a release go under the tag when there is no
    room beside it, so nothing is off the side of a row and no row is off the
    side of the page. The row with the long tag is the one asserted to have
    taken a second line: the shorter two may or may not, which is the rule
    working rather than a thing to pin down.
    """
    phone = drawn["phone"]
    assert len(phone["rows"]) == len(CARRIED), "the releases were not drawn"
    for release in phone["rows"]:
        assert (
            release["scrollWidth"] <= release["clientWidth"] + SLACK
        ), f"{release['tag']} overflows its own row"
        assert (
            release["box"]["right"] <= phone["innerWidth"] + SLACK
        ), f"{release['tag']} runs off the side of the page"
        for part in release["parts"]:
            assert (
                part["box"]["right"] <= release["box"]["right"] + SLACK
            ), f"{release['tag']}'s {part['part']} runs off the side of its row"
    assert lines(row(phone, LONG)) > 1, f"{LONG}'s row did not wrap"
