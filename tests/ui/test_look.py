"""The values the page draws with, against the copy they came from.

Four colours and two sizes are one system across rails49's UIs, and they
travel as a file rather than a package: `ui/look/tokens.css` is a verbatim copy
of `docs/tokens.css` in `rails49/.github`, pinned to the commit it was taken at
(org ADR-0005, `ui/look/README.md`). The copy is inert — nothing imports it and
the page does not link it — so what holds the two together is this.

It reads the copy and the files beside it and **nothing outside this
repository**. A check that fetched the source would go red on somebody else's
commit, which under a required gate red-lights every open pull request here
until somebody syncs; this one goes red on an edit here, which is the one thing
it is for (org ADR-0010).

It is a `pytest` rather than a test in the UI's own toolchain because
`scripts/check.sh` is this repository's gate and that gate is Python. What
ADR-0010 asks for is that the check runs in the consumer's gate, and it needs
no node on the machine it runs on — which is the box's property too, node
building the page inside the image and nowhere else (`deploy/ui.Dockerfile`).
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

UI = ROOT / "ui"

#: The verbatim copy: what the values are.
COPY = UI / "look" / "tokens.css"

#: This UI's own expression of them: what the page draws with.
DRAWN = UI / "src" / "look.css"

#: The height the rail turns at, as a number, for the one place CSS cannot
#: carry a custom property.
LOOK_TS = UI / "src" / "look.ts"

PAGE = UI / "index.html"

#: A colour written out: `#rgb` and `#rrggbb`, and the two forms that carry an
#: alpha channel. Held to those four lengths so that an issue number, a
#: fragment or an id selector is not read as a colour.
HEX = re.compile(r"#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b")

#: The two sheets that turn: the grid that gives the rail a row, and the rail
#: that lies its own contents down. Named rather than globbed — the claim is
#: that these two agree, and a glob would pass by finding neither.
TURNING = [
    UI / "src" / "ui" / "dccex-app.styles.ts",
    UI / "src" / "ui" / "dccex-rail.styles.ts",
]


def sheets() -> dict[str, str]:
    """Every component stylesheet the page draws with, by file name.

    Narrower than `painted()` below, and on purpose. What reads this is the
    claim that some rule *asks* for each token, and the rules that paint the
    chrome are these: `page.css` names Shoelace's tokens rather than these
    ones, and `index.html` carries no rules at all, so a `var(--band)` found
    in either would satisfy the claim with nothing painted by it. What a
    colour can be *written into* is a wider set, and that is the other
    function's.
    """
    return {
        sheet.name: sheet.read_text()
        for sheet in sorted((UI / "src" / "ui").glob("*.styles.ts"))
    }


def declarations(css: str) -> dict[str, str]:
    """The custom properties a stylesheet declares.

    Comments come out first: they carry a `--rail-button` or two in prose, and
    a reader of declarations cannot tell those from the real ones.
    """
    written = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    found: dict[str, str] = {}
    for match in re.finditer(r"(--[a-z-]+)\s*:\s*([^;]+);", written):
        name: str = match.group(1)
        value: str = match.group(2)
        found[name] = value.strip()
    return found


def paintable() -> list[Path]:
    """Every file a colour the page draws with can be written into.

    The component stylesheets, the components themselves, the plain
    stylesheets beside them, and the page — a `style` attribute or a `<style>`
    block paints as surely as a rule in a Lit sheet does, and a colour written
    into any of the four is a second place the page's chrome is changed in.

    The components are in it because that is where the markup went when the
    page grew Lit templates: `style="color:#f00"` on a release row is a colour
    written into the chrome with no stylesheet anywhere near it (#85).

    A component stylesheet is a `*.ts` too, so the second glob leaves out what
    the first one found. `painted()` below is keyed by file name, and a name
    arriving twice would read as a collision rather than as a finding.
    """
    return [
        *sorted((UI / "src" / "ui").glob("*.styles.ts")),
        *(
            component
            for component in sorted((UI / "src" / "ui").glob("*.ts"))
            if not component.name.endswith(".styles.ts")
        ),
        *sorted((UI / "src").glob("*.css")),
        PAGE,
    ]


def painted() -> dict[str, str]:
    """The text of every file `paintable()` names, by file name.

    `look.css` is the one place a colour is meant to be written, so the
    declarations of the copy's own tokens come out of it before the scan reads
    it — those, in that one file, and nothing else. A component sheet
    declaring `--band` as a hex of its own is the drift this is for, and a hex
    anywhere else in `look.css` is a rule painting past the block above it.
    """
    written: dict[str, str] = {}
    for source in paintable():
        text = source.read_text()
        if source == DRAWN:
            for token in declarations(COPY.read_text()):
                text = re.sub(rf"{token}\s*:\s*[^;]*;", "", text)
        written[source.name] = text
    return written


def rail_turns_px() -> int:
    """`RAIL_TURNS_PX`, read out of the module that exports it."""
    match = re.search(r"RAIL_TURNS_PX\s*=\s*(\d+)", LOOK_TS.read_text())
    assert match is not None, f"{LOOK_TS.name} exports no RAIL_TURNS_PX"
    return int(match.group(1))


def test_the_values_the_page_draws_with_are_the_copys() -> None:
    """Both directions at once.

    A value that drifted here fails, and so does a token added over there that
    this UI has not followed yet — which is the whole reason for keeping a
    copy rather than a note of what was current.
    """
    assert declarations(DRAWN.read_text()) == declarations(COPY.read_text())


def test_the_copy_holds_the_six_the_look_rules_bind() -> None:
    """The dcc-ex UI's row in LOOK.md is *everything*: both pieces of chrome
    are drawn here, so no token is one this page has nothing to spend it on."""
    assert sorted(declarations(COPY.read_text())) == [
        "--band",
        "--band-ink",
        "--rail",
        "--rail-button",
        "--rail-group",
        "--rail-turns",
    ]


def test_every_token_that_can_be_asked_for_is_asked_for_by_a_rule() -> None:
    """A value nothing draws with is a value that can drift unseen.

    `--rail-turns` is left out: a media query cannot read a custom property,
    and what carries it instead is held below.
    """
    written = "".join(sheets().values())
    for token in declarations(COPY.read_text()):
        if token == "--rail-turns":
            continue
        assert f"var({token})" in written, f"no rule asks for {token}"


def test_nothing_the_page_draws_with_writes_a_colour_out_as_a_hex() -> None:
    """One place a colour is changed in.

    A rule carrying the hex would pass the assertion above with the rule
    broken: the token would be read somewhere and that sheet would go on
    painting whatever it was copied with. A hex in `page.css` or in the page's
    own markup is the same break with a different file around it, which is why
    what is read here is everything the page draws with rather than the
    component sheets alone (#60).

    Any hex, rather than the four the copy gives. The claim above this one is
    that the page holds its colours in one place; a colour written out that
    the look rules never named is a second place with the drift still to come.
    """
    for name, written in sorted(painted().items()):
        found = [match.group() for match in HEX.finditer(written)]
        assert not found, f"{name} writes a colour out as a hex: {', '.join(found)}"


def test_the_height_the_rail_turns_at_is_the_copys() -> None:
    assert f"{rail_turns_px()}px" == declarations(COPY.read_text())["--rail-turns"]


def test_the_height_is_one_number_in_both_sheets_that_turn() -> None:
    """Interpolated rather than typed twice.

    `dccex-app` gives the rail a row to lie in and `dccex-rail` lies its own
    contents down. Turning at two different heights would draw the strip
    inside a column that is still there, which is the bug with extra steps.
    """
    for sheet in TURNING:
        assert (
            "max-height: ${unsafeCSS(RAIL_TURNS_PX)}px" in sheet.read_text()
        ), f"{sheet.name} does not turn at the one number"


def test_the_page_links_the_values_it_draws_with() -> None:
    assert f'href="/src/{DRAWN.name}"' in PAGE.read_text()


def test_the_copy_is_inert() -> None:
    """Nothing imports it, no build reads it and the page does not link it.

    That is what org ADR-0005 asks of a consumer, and it is what leaves this
    UI free to express the values in whatever form suits it. What is looked
    for is a reference rather than the name: the prose here and in `look.ts`
    says where the copy is, and saying so is not reading it.
    """
    reference = re.compile(
        r"""(?:from|import|href\s*=|url\()\s*["'(]?[^"')\n]*""" + COPY.name
    )
    reading = [PAGE, *(UI / "src").rglob("*.ts"), *(UI / "src").rglob("*.css")]
    for source in sorted(reading):
        assert not reference.search(source.read_text()), f"{source.name} reads the copy"


def test_both_themes_are_linked_wherever_one_of_them_is() -> None:
    """Shoelace's dark theme is a class rather than a query of its own, so a
    module that linked one theme alone would leave the page in it whatever the
    system says (LOOK.md)."""
    for module in sorted((UI / "src").rglob("*.ts")):
        source = module.read_text()
        assert ("themes/light.css" in source) == (
            "themes/dark.css" in source
        ), f"{module.name} links one theme and not the other"
