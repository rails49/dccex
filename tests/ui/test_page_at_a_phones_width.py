"""The page laid out at a phone's width, in a browser that does layout.

Everything else about how the page is shaped is read off the stylesheet it is
written in. That is not a habit, it is what the machines allowed: the gate is
Python with no browser in it, and happy-dom — which is what mounts the
components in the `node` job — draws no boxes, so a width, a wrap or an
element that is off the side of the screen is not a thing either of them can
see (`ui/test/mounted.ts`, `tests/ui/test_band.py`). The narrow-width rules
were therefore written and never rendered, which is what #1's Further Notes
recorded as "narrow widths were not verified" and what this is (#127).

So: a real Chromium, against the built page image, at two phone widths and at
a desktop one. It is the same artefact `tests/ui/test_page_serves.py` builds —
the image the box will serve — which is the other half of why this is the
`docker` job's and not a job of its own: #1 asks that one check run the thing in the
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

**Both views are measured, and the rail is what gets to the second.** The page
opens on the **monitor** and the releases are a view of its own (#169), so the
browser presses the rail's button for them and measures the rows there. A
press that did not switch the view leaves the rows undrawn, so the wait for
one times out and every assertion below is red at once.

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

from tests.ui.test_look import COPY, declarations
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
#: width and height. 375 is under both widths the band gives something up at —
#: the build below 560 and the link's words below 400.
PHONE = (375, 812)

#: The narrowest phone this page is read on, at the same height. 320 is the
#: width #208 asks the band to fit in: the chrome carries the name, the link
#: and two thumb-wide presses there, and nothing is dropped between here and
#: 375. The height is the phone's above rather than a short screen's, because
#: what this width is about is the band and a window under `--rail-turns` is
#: the **rail** lying down as well (`dccex-rail.styles.ts`).
NARROW = (320, 812)

#: A desktop, which is where what the band gives up on a phone has to be back.
DESKTOP = (1280, 800)

#: The three of them, in the order the browser walks them, by the name the
#: assertions below ask for them under.
WIDTHS = {"narrow": NARROW, "phone": PHONE, "desktop": DESKTOP}

#: The two **view**s this check walks, by the name the rail's button for each
#: of them carries and the page keeps in its hash (`ui/src/view.ts`, #169).
#: The browser opens on the first and presses the rail to reach the second,
#: which is the one gesture a reader has for getting there. The **script** view
#: is reached the same way, with one railroad answered for it (#185).
MONITOR, RELEASES_VIEW, SCRIPT_VIEW = "monitor", "releases", "script"

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

#: The look rules' minimum for a thumb, read off the copy the page draws with
#: rather than written out: the two presses on the band and the two buttons on
#: the rail are pressed on the phone this check is about (`ui/look/README.md`,
#: ADR-0011 d.1, ADR-0020 d.1, #169).
THUMB = int(declarations(COPY.read_text())["--rail-button"].removesuffix("px"))

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
MONITOR, RELEASES_VIEW, SCRIPT_VIEW = sys.argv[6], sys.argv[7], sys.argv[8]

#: One railroad, and its script with a line longer than a phone is wide.
RAILROAD = "crossover-yard"
SCRIPT = "# " + "a line longer than a phone is wide " * 4 + "\\n"

#: What the page drew, on one view, at one width. Each view is measured while
#: it is the one showing: the other is not in the document, which is what a
#: page that draws the view the rail picked means.
MEASURE = """
(view) => {
  const box = (drawn) => {
    const at = drawn.getBoundingClientRect();
    return {
      top: at.top, right: at.right, bottom: at.bottom, left: at.left,
      width: at.width, height: at.height,
    };
  };
  const app = document.querySelector("dccex-app");
  const wide = document.documentElement.scrollWidth;
  if (view === "script") {
    const pane = app.renderRoot.querySelector("dccex-script");
    return {
      hash: location.hash,
      scrollWidth: wide,
      box: box(pane.renderRoot.querySelector(".script")),
    };
  }
  if (view === "releases") {
    const releases = app.renderRoot.querySelector("dccex-releases");
    return {
      hash: location.hash,
      scrollWidth: wide,
      rows: [...releases.renderRoot.querySelectorAll(".release")].map(
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
      ),
    };
  }
  const band = app.renderRoot.querySelector("dccex-band");
  // What one part of the band was drawn as. The display is read as well as the
  // box: the build is blank with no face behind the page, so a box of no width
  // is what a drawn one and a dropped one both measure.
  const part = (selector) => {
    const drawn = band.renderRoot.querySelector(selector);
    return drawn === null
      ? null
      : { box: box(drawn), display: getComputedStyle(drawn).display };
  };
  const rail = app.renderRoot.querySelector("dccex-rail");
  const button = (selector) => box(rail.renderRoot.querySelector(selector));
  const monitor = app.renderRoot.querySelector("dccex-monitor");
  const typed = box(monitor.renderRoot.querySelector("input.typed"));
  const send = box(monitor.renderRoot.querySelector(".box button[type=submit]"));
  return {
    innerWidth: window.innerWidth,
    innerHeight: window.innerHeight,
    hash: location.hash,
    scrollWidth: wide,
    band: {
      build: part(".build"),
      dot: part(".dot"),
      says: part(".says"),
      power: part(".power"),
      stop: part(".stop"),
    },
    rail: {
      monitor: button("button.monitor"),
      releases: button("button.releases"),
      script: button("button.script"),
    },
    typed: typed,
    send: send,
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
    """The page loaded at one width, measured on both views, and typed into.

    It opens on the monitor, which is what a page with nothing in its hash
    shows, and reaches the releases the way a person does: the rail's button.
    A press that did not switch the view is a wait that times out here rather
    than an assertion below.
    """
    page.set_viewport_size({"width": width, "height": height})
    page.goto(URL)
    page.wait_for_selector("input.typed")
    drawn = page.evaluate(MEASURE, MONITOR)
    page.fill("input.typed", TYPED)
    drawn["reads"] = page.input_value("input.typed")
    page.click(f"dccex-rail button.{RELEASES_VIEW}")
    page.wait_for_selector(".release")
    drawn[RELEASES_VIEW] = page.evaluate(MEASURE, RELEASES_VIEW)
    page.click(f"dccex-rail button.{SCRIPT_VIEW}")
    page.click("dccex-script .railroad")
    page.wait_for_selector("dccex-script .script")
    drawn[SCRIPT_VIEW] = page.evaluate(MEASURE, SCRIPT_VIEW)
    return drawn


with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    context = browser.new_context()
    context.route(RELEASES, answered)
    context.route(
        "**/dccex-usb/railroads",
        lambda route: route.fulfill(json={"railroads": [RAILROAD]}),
    )
    context.route(
        "**/dccex-usb/scripts/*",
        lambda route: route.fulfill(json={"text": SCRIPT}),
    )
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
    """The one release row named `tag`, asserted to have been drawn.

    Off the releases view, which is where a release row is.
    """
    found = [
        release for release in drawn[RELEASES_VIEW]["rows"] if release["tag"] == tag
    ]
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
            MONITOR,
            RELEASES_VIEW,
            SCRIPT_VIEW,
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


def test_the_page_does_not_scroll_sideways_at_any_width(
    drawn: dict[str, Any],
) -> None:
    """Nothing on the page is off the side of it, at either phone's width or at
    a desktop's.

    A horizontal scrollbar on a page held in one hand is the failure this
    whole check exists to catch: it is what a rule that was written and never
    rendered produces, and it is invisible to every check that reads the
    stylesheet.

    On every **view**, because each is measured while it is the one showing.
    The widest things on the page are a long **tag** on the releases and a
    long line of a script.
    """
    for width, page in drawn.items():
        for view in (MONITOR, RELEASES_VIEW, SCRIPT_VIEW):
            measured = page if view == MONITOR else page[view]
            wide = measured["scrollWidth"]
            assert wide <= page["innerWidth"] + SLACK, (
                f"the page is {wide}px wide in a {page['innerWidth']}px {width}"
                f" on the {view} view"
            )


def test_the_script_box_is_inside_a_phone_s_screen(drawn: dict[str, Any]) -> None:
    """The box a script is typed into fits across the screen; a long line
    scrolls inside it and not the page (#185)."""
    for width, page in drawn.items():
        box = page[SCRIPT_VIEW]["box"]
        assert box["width"] > 0, f"no script box in a {width}"
        assert box["left"] >= -SLACK, f"the script box is off the left of a {width}"
        assert (
            box["right"] <= page["innerWidth"] + SLACK
        ), f"the script box is off the side of a {width}: {box}"


def test_the_rail_offers_both_views_and_is_pressed_to_reach_one(
    drawn: dict[str, Any],
) -> None:
    """The one gesture a reader has for changing what the work pane shows
    (#169).

    Every button is drawn, each is the thumb the look rules ask for, and none
    is off the side of a phone. That the press worked is the hash and
    the rows: the fixture pressed the releases button and the browser was on
    `#releases` with the list drawn, which is a page that read the hash back.
    """
    for width, page in drawn.items():
        for view, button in page["rail"].items():
            assert (
                button["width"] >= THUMB - SLACK and button["height"] >= THUMB - SLACK
            ), f"the rail's {view} button is under a thumb in a {width}: {button}"
            assert (
                button["left"] >= -SLACK
                and button["right"] <= page["innerWidth"] + SLACK
            ), f"the rail's {view} button is off the side of a {width}: {button}"
        assert page["hash"] in (
            "",
            f"#{MONITOR}",
        ), "the page did not open on the monitor"
        assert (
            page[RELEASES_VIEW]["hash"] == f"#{RELEASES_VIEW}"
        ), "pressing the rail did not put the view in the hash"


def test_the_narrow_band_keeps_the_dot_and_both_presses(
    drawn: dict[str, Any],
) -> None:
    """Below the widths the band gives things up at, what survives is the link
    at a glance and the two controls.

    `tests/ui/test_band.py` holds the rules as they are written — which part
    each query names, and that none of them names the dot or either press. What
    is held here is that a browser does it: at both phone widths the **build**
    and the link's words are not laid out, the dot, the power button and STOP
    are, and at a desktop width the words are back. The last of them is what
    keeps the rest from passing on a page that drew no band at all.

    Each press is measured against `--rail-button` as well, which is the look
    rules' minimum for a thumb: they are pressed on the phone held at the
    layout, and a rule that asked for that height inside a row that squashed it
    would read as this passing (ADR-0011 d.1, ADR-0020 d.1).

    **320px is where the second press had to fit** (#208). The band carries the
    name, the link and two thumbs there, and that is the width the whole of it
    is asserted at rather than the width it happens to be read at.
    """
    desktop = drawn["desktop"]["band"]
    for width in ("narrow", "phone"):
        page = drawn[width]
        band = page["band"]
        for name in ("build", "dot", "says", "power", "stop"):
            assert band[name] is not None, f"the band drew no {name} at all"
        assert band["build"]["display"] == "none", f"a {width} band keeps the build"
        assert band["says"]["display"] == "none", f"a {width} band keeps the words"
        assert band["dot"]["box"]["width"] > 0, f"a {width} band drops the link"
        for press in ("power", "stop"):
            box = band[press]["box"]
            assert (
                box["width"] >= THUMB - SLACK and box["height"] >= THUMB - SLACK
            ), f"the {press} press is under a thumb in a {width}: {box}"
            assert (
                box["left"] >= -SLACK and box["right"] <= page["innerWidth"] + SLACK
            ), f"the {press} press is off the side of a {width}: {box}"
        assert (
            band["stop"]["box"]["left"] >= band["power"]["box"]["right"] - SLACK
        ), f"STOP is not right of the power button in a {width}"
    assert (
        desktop["says"]["display"] != "none"
    ), "the band drops the words at every width"
    assert desktop["says"]["box"]["width"] > 0, "the band says nothing at any width"


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
    rows = phone[RELEASES_VIEW]["rows"]
    assert len(rows) == len(CARRIED), "the releases were not drawn"
    for release in rows:
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
