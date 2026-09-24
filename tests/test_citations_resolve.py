"""A citation of ADR-0002 in the source says which repository's it is.

There are two decisions with that number and they are not related. The
organisation's, in `rails49/.github`, is that a UI talks to the bus, the store
and its own app's face; this repository's is that a defect in copied code is
fixed where it came from, and it is superseded (ADR-0003). A reader who
follows a bare "ADR-0002" out of the source lands on whichever one they
happened to look in, and ADR-0006 d.4 already records the collision: "neither
ADR-0002 is available to carry it".

Nothing can be renamed to end it — one of the two is another repository's — so
what the source owes a reader is the owner beside the number. The glossary
carries the URL once (`CONTEXT.md`, **face**), which is where the name is
resolved rather than only disambiguated.

**The source is two trees.** The package is under `src/` and the page is not,
so for as long as this read `src/` alone it was green while three bare
citations sat in the newest code in the repository (#86).
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CONTEXT = ROOT / "CONTEXT.md"

#: What a reader of the code reads, tree by tree: the package's prose and the
#: provenance note beside it, the page's modules and any note left among them.
#: Anything else under either is something a build left there.
PROSE = {
    ROOT / "src": ("*.py", "*.md"),
    ROOT / "ui" / "src": ("*.ts", "*.js", "*.md"),
}

#: The organisation's copy, at the address the rest of the repository links it
#: at — the mirror's page, ADR-0001 and ADR-0004 all use this one.
ORG = (
    "https://github.com/rails49/.github/blob/main/docs/adr/"
    "0002-a-ui-talks-to-the-bus-the-store-and-its-own-apps-face.md"
)

#: Whose the decision is, written before the number — across a line break as
#: readily as not, because prose wraps. A wrapped line of the page's prose
#: opens with the `*` its comment block is drawn with, so the break carries one
#: and the owner is still beside the number. Either owner resolves the name;
#: what is forbidden is neither.
OWNED = re.compile(r"(the organisation's|this repository's)[\s*]+ADR-0002")

CITED = re.compile(r"ADR-0002")


def prose() -> list[Path]:
    """Every file of the source a reader of the code reads, both trees."""
    return sorted(
        page
        for tree, kinds in PROSE.items()
        for kind in kinds
        for page in tree.rglob(kind)
    )


def cited(text: str) -> list[str]:
    """Every mention of the number that does not say whose it is."""
    return [
        text[max(0, mention.start() - 40) : mention.end()]
        for mention in CITED.finditer(OWNED.sub("", text))
    ]


def test_no_citation_of_adr_0002_in_the_source_is_bare() -> None:
    bare = {
        str(page.relative_to(ROOT)): loose
        for page in prose()
        if (loose := cited(page.read_text()))
    }
    assert bare == {}, f"ADR-0002 cited without saying whose it is: {bare}"


def test_the_source_cites_adr_0002_at_all() -> None:
    """Named so the check above cannot pass by looking at nothing.

    The mirror's face, the module the page reaches a face through and the two
    components that say what the page talks to all mean the organisation's;
    `SOURCE.md` means this repository's, which is superseded and says so.
    `face.ts` is in this set across a line break, which is the wrap the
    pattern allows for.
    """
    owned = {
        page.relative_to(ROOT).as_posix()
        for page in prose()
        if OWNED.search(page.read_text())
    }
    assert owned == {
        "src/SOURCE.md",
        "src/dccex_usb/face.py",
        "ui/src/face.ts",
        "ui/src/ui/dccex-app.ts",
        "ui/src/ui/dccex-releases.ts",
    }


def test_the_glossary_resolves_the_organisations_adr_0002() -> None:
    """One place a reader of the code can turn the name into a decision."""
    text = CONTEXT.read_text()
    assert text.count(ORG) == 1, f"the glossary links {ORG} {text.count(ORG)} times"
