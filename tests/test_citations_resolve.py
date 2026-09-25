"""A citation of ADR-0002 in this repository's prose says whose it is.

There are two decisions with that number and they are not related. The
organisation's, in `rails49/.github`, is that a UI talks to the bus, the store
and its own app's face; this repository's is that a defect in copied code is
fixed where it came from, and it is superseded (ADR-0003). A reader who
follows a bare "ADR-0002" out of a page lands on whichever one they happened
to look in, and ADR-0006 d.4 already records the collision: "neither
ADR-0002 is available to carry it".

Nothing can be renamed to end it — one of the two is another repository's — so
what a page owes a reader is the owner beside the number. The glossary
carries the URL once (`CONTEXT.md`, **face**), which is where the name is
resolved rather than only disambiguated.

**A link is an owner too.** A citation written as the text of a link to one of
the two files lands a reader on the decision itself, which is more than the
owner beside the number gives them. The glossary, the root `README.md` and the
mirror's page all cite it that way and none of them says an owner in words
(#123).

**What is read.** Every tree a reader of this repository reads: the two pages
at the root, the package under `src/`, every page of `docs/`, the page's own
modules and the stylesheets beside them under `ui/src/`, the suites that mount
its components under `ui/test/`, the page beside the look rules' copy, every
check under `tests/` and the node runners among them, and what the box is built
and served from under `deploy/`. The same trees the module beside this one
reads, so this number owes a reader an owner in the same places whichever check
is asking (#150).

Each widening before the last came of bare citations sitting where nothing was
looking: three in the newest code in the repository while this read `src/`
alone (#86), and six across `docs/` and `tests/` while it read those two trees
(#117, #123). The last came of none. `ui/test/`, `ui/look/` and `deploy/` cite
this number nowhere, and what #150 found bare in them was the other half of the
rule (#151) — but a reader does not know which check is looking where, and two
checks of the same prose over two different reaches is a gap nobody can hold in
their head.

**What is deliberately not.** `docs/adr/` and this module, each written out
beside `PROSE` with its reason. Both carry bare citations and neither is
edited to end them: an ADR is a record of what was decided at the time, and
the bare citation here is what the scan is run over.

`ui/look/tokens.css` is not read either, and is not globbed rather than
excluded: it is `rails49/.github`'s file, copied verbatim and pinned to the
commit it was taken at, so the prose in it is that repository's to qualify
(`ui/look/README.md`). The compose files, `scripts/` and `ui`'s own
configuration are the next widening, written out at the same place in the
module beside this one.
"""

import re
from pathlib import Path

#: This module, which is not read. The citations in it are what the scan is
#: run over below — a bare one to catch, and an owner to strike off a whole
#: one — so a scan that read this file would be red on its own test data.
SELF = Path(__file__).resolve()

ROOT = SELF.parent.parent

CONTEXT = ROOT / "CONTEXT.md"

#: The records, which are not read. An ADR is accepted as it was written and
#: is not edited to satisfy a check; ADR-0003 and ADR-0006 cite this
#: repository's ADR-0002 bare, where an owner is not what a reader is missing,
#: and ADR-0001 and ADR-0008 write the organisation's as `org ADR-0002` (#123).
ADRS = ROOT / "docs" / "adr"

#: What a reader of this repository reads, tree by tree and with the depth in
#: the glob: the two pages at the root, the package's prose and the provenance
#: note beside it, the pages under `docs/`, the page's modules with the
#: stylesheets beside them and any note left among them, the suites that mount
#: its components, the page beside the look rules' copy, the checks under
#: `tests/` with the node runners among them, and what the box is built and
#: served from. The root is read flat — everything below it worth reading is a
#: tree of its own here, and the rest is what a build, an environment or a
#: package manager left there.
#:
#: `ui/look/` is read for its README alone. `tokens.css` beside it is another
#: repository's file, copied verbatim and pinned to a commit so that diffing
#: the two is a diff of the same thing.
#:
#: The same set as `tests/test_adr_numbers_resolve.py`, written out here too
#: rather than imported from there: a reach taken from the module beside this
#: one would follow it wherever it went, and what a reader of either wants to
#: know is what *this* check looks at (#150).
PROSE = {
    ROOT: ("*.md",),
    ROOT / "src": ("**/*.py", "**/*.md"),
    ROOT / "docs": ("**/*.md",),
    ROOT / "ui" / "src": ("**/*.ts", "**/*.js", "**/*.css", "**/*.md"),
    ROOT / "ui" / "test": ("**/*.ts",),
    ROOT / "ui" / "look": ("*.md",),
    ROOT / "tests": ("**/*.py", "**/*.mjs"),
    ROOT / "deploy": ("*Dockerfile", "*.conf"),
}

#: The two things under those trees that are not read, each for the reason
#: written above it.
NOT_READ = (ADRS, SELF)

#: The organisation's copy, at the address the rest of the repository links it
#: at — the mirror's page, ADR-0001 and ADR-0004 all use this one.
ORG = (
    "https://github.com/rails49/.github/blob/main/docs/adr/"
    "0002-a-ui-talks-to-the-bus-the-store-and-its-own-apps-face.md"
)

#: This repository's copy, which is superseded (ADR-0003), as a page links it:
#: by path, and by a path relative to wherever that page sits. What says which
#: file it is is the name on the end rather than the path in front of it.
OURS = "0002-a-defect-in-copied-code-is-fixed-where-it-came-from.md"

#: Whose the decision is, written before the number — across a line break as
#: readily as not, and at either break the phrase has, because prose wraps
#: wherever the width runs out. A wrapped line of the page's prose opens with
#: the `*` its comment block is drawn with, so the break carries one and the
#: owner is still beside the number. The owner is capitalised where it opens a
#: sentence, which is how the page's README and ADR-0008 write it. Either
#: owner resolves the name; what is forbidden is neither.
OWNED = re.compile(
    r"(?:[Tt]he[\s*]+organisation's|[Tt]his[\s*]+repository's)[\s*]+ADR-0002"
)

#: A citation that is the text of a link to one of the two files. Following
#: one resolves the number, so a link says whose it is without saying it in
#: words. A link whose target is neither file says nothing a bare mention does
#: not and is read as bare.
LINKED = re.compile(
    r"\[ADR-0002\]\((?:" + re.escape(ORG) + r"|[\w./-]*" + re.escape(OURS) + r")\)"
)

CITED = re.compile(r"ADR-0002")

#: A citation as `dccex-app.ts` writes it, and the same citation with the owner
#: struck off: what a bare one added to a file the scan reads looks like. The
#: page's README and the flash's checks write it the same way, so one strike
#: serves the three trees the scan was first shown catching one in. The three
#: #150 brought in cite the number nowhere, so the struck form is planted in
#: those rather than struck out of them (`planted()`).
CITATION = "(the organisation's ADR-0002)"
STRUCK = "(ADR-0002)"


def prose() -> list[Path]:
    """Every page of the repository the scan reads, minus the two it does not."""
    return sorted(
        page
        for tree, kinds in PROSE.items()
        for kind in kinds
        for page in tree.glob(kind)
        if not any(spot == page or spot in page.parents for spot in NOT_READ)
    )


def spent(pattern: re.Pattern[str], text: str) -> str:
    """The text with every match of the pattern blanked and nothing moved.

    A citation that says whose it is has been read and is done with, but
    deleting it would slide everything after it along, and what `cited()`
    hands back is the forty characters in front of a bare one — cut out of the
    text the file holds, so that a page carrying a whole citation ahead of a
    bare one is reported at the bare one rather than forty characters early.
    """
    return pattern.sub(lambda said: " " * len(said.group()), text)


def cited(text: str) -> list[str]:
    """Every mention of the number that does not say whose it is."""
    return [
        text[max(0, mention.start() - 40) : mention.end()]
        for mention in CITED.finditer(spent(LINKED, spent(OWNED, text)))
    ]


def struck(page: Path) -> list[str]:
    """What the scan makes of a page with the owner struck off its citation.

    The strike goes on the text the scan read rather than on the file, so a
    run that dies leaves the tree as it found it. That the page is read and
    that there was a citation on it to strike are asserted first — a tree that
    moved or prose that moved would otherwise leave a caller passing on a
    substitution that never happened.
    """
    assert page in prose(), f"{page.relative_to(ROOT)} is not read"
    written = page.read_text()
    assert CITATION in written, f"no {CITATION} in {page.name} to strike"
    return cited(written.replace(CITATION, STRUCK, 1))


def planted(page: Path) -> str:
    """The page's text with a bare citation of the number written after it.

    Planted rather than struck, because none of the three trees #150 brought
    into reach cites this number at all. What is held either way is the reach
    and not the pattern: a page nothing reads is a page a bare citation can sit
    in for good.

    The plant goes on the text the scan read rather than on the file, so a run
    that dies leaves the tree as it found it, and that the page is read is
    asserted first — a tree that moved would otherwise leave a caller passing
    on a page the scan never looks at.
    """
    assert page in prose(), f"{page.relative_to(ROOT)} is not read"
    return f"{page.read_text()}\na UI talks to its own app's face {STRUCK}\n"


def test_no_citation_of_adr_0002_in_the_prose_is_bare() -> None:
    bare = {
        str(page.relative_to(ROOT)): loose
        for page in prose()
        if (loose := cited(page.read_text()))
    }
    assert bare == {}, f"ADR-0002 cited without saying whose it is: {bare}"


def test_the_prose_cites_adr_0002_at_all() -> None:
    """Named so the check above cannot pass by looking at nothing.

    Both ways of saying whose it is, over the tree as it stands. The mirror's
    face, the module the page reaches a face through, the two components that
    say what the page talks to, the page's README and the two suites of the
    page's checks all mean the organisation's and say so in words; `SOURCE.md`
    means this repository's, which is superseded and says so, and so does the
    module that holds every other number to naming its repository (#128).
    `face.ts` is in this set across a line break and the README's `:39` by
    opening a sentence, which are the two wraps and the one capital the
    pattern allows for.

    The other three say it by where the link goes, and the glossary is one of
    them — the place the name is resolved rather than only disambiguated.
    """
    read = [(page.relative_to(ROOT).as_posix(), page.read_text()) for page in prose()]
    assert {name for name, text in read if OWNED.search(text)} == {
        "docs/ui/README.md",
        "src/SOURCE.md",
        "src/dccex_usb/face.py",
        "tests/test_adr_numbers_resolve.py",
        "tests/ui/test_flash.py",
        "tests/ui/test_releases.py",
        "ui/src/face.ts",
        "ui/src/ui/dccex-app.ts",
        "ui/src/ui/dccex-releases.ts",
    }
    assert {name for name, text in read if LINKED.search(text)} == {
        "CONTEXT.md",
        "README.md",
        "docs/dccex_usb/README.md",
    }


def test_a_bare_citation_under_the_page_is_caught() -> None:
    """The scan, over a page module with the owner struck off its citation.

    What this holds is the reach and not the pattern: before #86 the check
    read `src/` alone, so the module below was not among the files it reads
    and `struck()`'s first assertion is the one that would have failed.
    """
    loose = struck(ROOT / "ui" / "src" / "ui" / "dccex-app.ts")
    assert len(loose) == 1, f"the struck citation was not caught: {loose}"
    assert loose[0].endswith("what the page talks to (ADR-0002")


def test_a_bare_citation_in_the_docs_is_caught() -> None:
    """The same strike on a page under `docs/`, which #123 brought into reach.

    This is the one the triage of #117 was about: the bare citation it found
    had sat on this very page, and the check was green because nothing under
    `docs/` was read.
    """
    loose = struck(ROOT / "docs" / "ui" / "README.md")
    assert len(loose) == 1, f"the struck citation was not caught: {loose}"
    assert loose[0].endswith("face and nothing else (ADR-0002")


def test_a_bare_citation_in_a_test_module_is_caught() -> None:
    """The same strike on a module under `tests/`, which #123 also brought in.

    `tests/` is read apart from this module, so a docstring here owes a reader
    the owner exactly as the code it is about does — which is what #117 had to
    fix by hand in two suites of the page's checks.
    """
    loose = struck(ROOT / "tests" / "ui" / "test_flash.py")
    assert len(loose) == 1, f"the struck citation was not caught: {loose}"
    assert loose[0].endswith("what the page talks to (ADR-0002")


def test_a_bare_citation_under_the_pages_own_suites_is_caught() -> None:
    """A plant in `ui/test/`, where `vitest` mounts the components (#126).

    Nothing there cites this number, so there is no owner in the tree to strike
    off: what is planted is the bare citation itself, and what it holds is that
    the tree is read at all. Before #150 nothing under `ui/test/` was read, and
    the assertion in `planted()` is the one that would have failed.
    """
    loose = cited(planted(ROOT / "ui" / "test" / "monitor.test.ts"))
    assert len(loose) == 1, f"the planted citation was not caught: {loose}"
    assert loose[0].endswith("its own app's face (ADR-0002")


def test_a_bare_citation_beside_the_look_rules_copy_is_caught() -> None:
    """A plant in `ui/look/`, on the page that says where the copy came from.

    The copy itself is not globbed, for the reason written beside `PROSE`. The
    page beside it is this repository's own prose, and the organisation's
    decisions it cites are the look rules' rather than this number (#150).
    """
    loose = cited(planted(ROOT / "ui" / "look" / "README.md"))
    assert len(loose) == 1, f"the planted citation was not caught: {loose}"


def test_a_bare_citation_in_what_the_box_runs_is_caught() -> None:
    """A plant in `deploy/`, where the image the box runs is built.

    The `Dockerfile`s and `nginx.conf` are prose about what the page and the
    face reach each other over, which is the subject this number is cited for
    everywhere else, and they were read by neither check until #150.
    """
    loose = cited(planted(ROOT / "deploy" / "nginx.conf"))
    assert len(loose) == 1, f"the planted citation was not caught: {loose}"


def test_the_records_and_this_module_are_not_read() -> None:
    """The two exclusions, and that each is carrying something to exclude.

    An exclusion that has nothing behind it is an exclusion nobody would
    notice going wrong, so the bare citations are asserted as well as the
    absence: `docs/adr/` because an ADR is a record of what was decided at the
    time, and this module because its bare citation is the scan's test data.
    """
    read = prose()
    assert [
        page.relative_to(ROOT).as_posix() for page in read if ADRS in page.parents
    ] == []
    assert SELF not in read
    superseding = ADRS / "0003-the-copy-has-no-original-left-and-is-fixed-here.md"
    assert cited(superseding.read_text()), f"nothing bare left in {superseding.name}"
    assert cited(SELF.read_text()), "nothing bare left in this module"


def test_an_owner_resolves_wherever_the_line_broke_and_however_it_opened() -> None:
    """The phrase wraps at either of its breaks, and opens a sentence.

    Prose wraps where the width runs out rather than where a pattern would
    like it to, and a line of the page's comment prose opens with the `*` the
    block is drawn with. A sentence that opens on the owner capitalises it,
    which is how `docs/ui/README.md` and ADR-0008 write it — a form the
    pattern could not read for as long as it read `src/` and `ui/src/` alone,
    where no citation opens one (#123).
    """
    for written in (
        "about the app rather than about a railroad (the\norganisation's ADR-0002)",
        " *  the store and its own app's face (the organisation's\n *  ADR-0002)",
        "The organisation's ADR-0002 permits all three.",
        "This repository's ADR-0002 is superseded.",
    ):
        assert cited(written) == [], f"the owner was not read: {written!r}"


def test_a_bare_citation_is_reported_where_it_sits() -> None:
    """The context a bare citation comes back with, on a page holding both.

    Every file the check read until #123 held one citation or several of one
    kind, so nothing showed that a whole citation ahead of a bare one moved
    what the bare one was reported with. `docs/ui/README.md` holds one of
    each, and a reader given the wrong forty characters would go looking on
    the wrong line.
    """
    written = "it permits all three (the organisation's ADR-0002). It is ADR-0002."
    loose = cited(written)
    assert len(loose) == 1, f"the whole citation was read as bare too: {loose}"
    assert loose[0].endswith("). It is ADR-0002"), loose[0]


def test_a_linked_citation_says_whose_it_is() -> None:
    """A link to either file, which lands a reader on the decision itself.

    The organisation's is linked at `ORG` wherever this repository links it at
    all. This repository's is linked by path, from wherever the page doing the
    linking sits, so both a page at the root and a page beside the file
    resolve the number.
    """
    assert cited(f"its own app's face ([ADR-0002]({ORG})).") == []
    assert cited(f"fixed where it came from ([ADR-0002](docs/adr/{OURS})).") == []
    assert cited(f"the decision it supersedes ([ADR-0002](../adr/{OURS})).") == []


def test_a_link_to_anything_else_is_not_an_owner() -> None:
    """What resolves the number is where the link goes and not its text.

    A link to some third page leaves a reader exactly where a bare mention
    leaves them, so the scan reads it as one.
    """
    loose = cited("the decision ([ADR-0002](https://example.invalid/0002.md)).")
    assert len(loose) == 1, f"a link to a third page was read as owned: {loose}"
    assert loose[0].endswith("ADR-0002")


def test_the_glossary_resolves_the_organisations_adr_0002() -> None:
    """One place a reader of the code can turn the name into a decision."""
    text = CONTEXT.read_text()
    assert text.count(ORG) == 1, f"the glossary links {ORG} {text.count(ORG)} times"
