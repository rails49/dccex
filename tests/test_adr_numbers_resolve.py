"""A bare ADR number in this repository's prose is this repository's.

The package under `src/dccex_usb` was written in `control` and copied here
(`src/SOURCE.md`), and its prose came across citing `control`'s decisions the
way prose in `control` cites them: bare. This repository has decisions of its
own now, numbered from 0001, so a bare `ADR-0043` in a docstring names a file
that is not there, and a reader who goes looking for it is told nothing. The
day this repository reaches 0042 the same citation names the wrong decision
instead of none, which is worse.

The rule is the one `CONTEXT.md` already keeps in most places: **a bare ADR
number is this repository's**, and anything else names where it was decided —
`control` ADR-0066, or the organisation's ADR-0002 with its link. This module
holds the two halves of it. A bare number resolves to a file in `docs/adr/`,
so a reader who follows one lands on the decision. And a number known to be
`control`'s is never bare, whatever `docs/adr/` holds — which is the half that
stays true after this repository reaches 0042 (#128).

**The owner is checked against what this repository already links.**
`control`'s `docs/adr/` is not readable from a checkout of this one: the
network is not there to reach it, and `control` deleted its copy of this
package (ADR-0003). What each of those numbers decided is recorded here
instead, in the **Related:** links this repository's own ADRs carry, and
`CONTROL` below is held to them title by title.

**The number this repository shares with the organisation is another
question.** A citation can resolve to a file in `docs/adr/` and still leave a
reader on the wrong decision: there is one numbered 0002 here and another in
`rails49/.github`, and the organisation's ADR-0002 is cited here often enough
that the number owes a reader an owner of its own. Holding it to one is
`tests/test_citations_resolve.py`, over a wider reach than this one, and a
citation of that number saying neither owner is red there rather than here.

**What is read.** `CONTEXT.md`, the package under `src/` with the provenance
note beside it, and every page of `docs/`. That is where the unqualified
citations were found and it is what #128 asked for. The page under `ui/src/`
and the checks under `tests/` cite `control`'s numbers bare in places too;
bringing them into reach is a change of its own, the way each widening of the
module beside this one was (#86, #117, #123).

**What is deliberately not.** `docs/adr/`. An ADR is a record of what was
decided at the time and is not edited to satisfy a check (#123): each one
names `control`'s repository in its **Related:** links and then uses the
number alone in the prose below it, which is a shorthand that reads inside
one page. This module is not read either, for want of being under a tree this
reads at all — the bare citations in it are what the scan is run over.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: The records, which are not read, for the reason written above them.
ADRS = ROOT / "docs" / "adr"

#: What this scan reads, tree by tree and with the depth in the glob: the
#: glossary, the package's prose and the provenance note beside it, and the
#: pages under `docs/`. The root is named file by file rather than globbed —
#: `README.md` at the root is the page's business and is read by the module
#: beside this one, which owns the number both repositories carry.
PROSE = {
    ROOT: ("CONTEXT.md",),
    ROOT / "src": ("**/*.py", "**/*.md"),
    ROOT / "docs": ("**/*.md",),
}

#: `control`'s decisions as this repository cites them, and what each one
#: decided. Written out rather than read off the links that carry them, for
#: the reason `scripts/check.sh` writes its words out rather than reading them
#: off `CONTEXT.md`: a list taken from the files being checked passes on
#: whatever those files happen to say. The links hold it to `control`'s own
#: titles below.
CONTROL = {
    "0042": "the edge terminates TLS and the LAN is the trust boundary",
    "0043": "the layout interface is a core app and hardware hangs under it by address",
    "0050": "broken hardware is reported never worked around",
    "0051": "track power is cut by the client that was written to cut it",
    "0062": "a guarantee about a railroad lives in the client that makes it",
    "0065": "the app that owns the device flashes it",
    "0066": "the link is the station answering not the socket being open",
}

#: Where `control`'s records are, at the address every link in this repository
#: reaches them at.
CONTROL_ADRS = "https://github.com/rails49/control/blob/main/docs/adr/"

#: Whose the decision is, written before the number. `control` is named with
#: the backticks a repository gets in prose or without them, as the pages that
#: cite it do both, and in the possessive where the sentence wants one; the
#: organisation's and this repository's are the two phrases the module beside
#: this one settled on. The owner is capitalised where it opens a sentence and
#: reaches the number across a line break as readily as not — prose wraps
#: where the width runs out. A wrapped line of a comment block opens with
#: whatever the block is drawn with, which is `#` in a module and `*` on the
#: page, so the owner is still beside the number.
GAP = r"[\s*#]+"
OWNER = rf"(?:`?control`?(?:'s)?|[Tt]he{GAP}organisation's|[Tt]his{GAP}repository's)"

#: A citation, with the owner in front of it where there is one. Four digits,
#: because that is how every ADR on either side is numbered, and what follows
#: them — a `d.4`, a possessive, a closing bracket — is no part of the name.
CITED = re.compile(rf"(?:(?P<owner>{OWNER}){GAP})?ADR-(?P<number>\d{{4}})")

#: A citation that is the text of a link into `control`'s records. Following
#: one lands a reader on the decision itself, which is more than the owner
#: beside the number gives them, so a link is an owner too — the call the
#: module beside this one made for the number both repositories carry. Every
#: link of this kind in the tree says `control` in its text as well; what this
#: is for is the one that does not.
LINKED = re.compile(
    rf"\[ADR-\d{{4}}\]\({re.escape(CONTROL_ADRS)}\d{{4}}-[a-z0-9-]+\.md\)"
)


def prose() -> list[Path]:
    """Every page this scan reads, minus the records it does not."""
    return sorted(
        page
        for tree, kinds in PROSE.items()
        for kind in kinds
        for page in tree.glob(kind)
        if not any(spot == page or spot in page.parents for spot in (ADRS,))
    )


def ours() -> set[str]:
    """Every number `docs/adr/` has a file for."""
    return {page.name[:4] for page in ADRS.glob("[0-9][0-9][0-9][0-9]-*.md")}


def spent(text: str) -> str:
    """The text with every linked citation blanked and nothing moved.

    A citation a reader can follow has been read and is done with, but
    deleting it would slide everything after it along, and what `bare()` hands
    back is the forty characters in front of a citation — cut out of the text
    the file holds, so that a page carrying a link ahead of a bare citation is
    reported at the bare one rather than forty characters early.
    """
    return LINKED.sub(lambda said: " " * len(said.group()), text)


def bare(text: str) -> list[tuple[str, str]]:
    """Every citation that names no repository: its number, and where it sits.

    Where it sits is the forty characters in front of it, which is the sentence
    a reader is sent to rather than the line number of a file this was handed
    the text of.
    """
    return [
        (said.group("number"), text[max(0, said.start() - 40) : said.end()])
        for said in CITED.finditer(spent(text))
        if not said.group("owner")
    ]


def unresolved(text: str, held: set[str] | None = None) -> list[str]:
    """Every bare citation naming a decision `docs/adr/` has no file for."""
    there = ours() if held is None else held
    return [where for number, where in bare(text) if number not in there]


def borrowed(text: str) -> list[str]:
    """Every bare citation of a number that is `control`'s.

    What `docs/adr/` holds is not asked. A number is `control`'s because
    `CONTROL` says so, so this stays red on a bare `ADR-0042` on the day this
    repository accepts an ADR-0042 of its own — the day `unresolved()` goes
    quiet about it and a reader starts landing on the wrong decision.
    """
    return [where for number, where in bare(text) if number in CONTROL]


def struck(page: Path, citation: str) -> str:
    """The page's text with the owner struck off one of its citations.

    The strike goes on the text the scan read rather than on the file, so a
    run that dies leaves the tree as it found it. That the page is read and
    that there was an owner on it to strike are asserted first: a tree that
    moved or prose that moved would otherwise leave a caller passing on a
    substitution that never happened.
    """
    assert page in prose(), f"{page.relative_to(ROOT)} is not read"
    written = page.read_text()
    assert written.count(citation) == 1, f"{citation!r} is not once in {page.name}"
    return written.replace(citation, citation.replace("control ", ""), 1)


def test_every_bare_citation_names_a_decision_that_is_here() -> None:
    loose = {
        page.relative_to(ROOT).as_posix(): where
        for page in prose()
        if (where := unresolved(page.read_text()))
    }
    assert loose == {}, f"cited bare, and not a decision of this repository: {loose}"


def test_no_decision_of_controls_is_cited_bare() -> None:
    """The half of the rule that outlives this repository's numbering.

    A citation caught here is caught by the check above as well for as long as
    the numbers do not overlap. What this one says is that the day they do,
    the prose is already right.
    """
    loose = {
        page.relative_to(ROOT).as_posix(): where
        for page in prose()
        if (where := borrowed(page.read_text()))
    }
    assert loose == {}, f"a decision of `control`'s, cited as ours: {loose}"


def test_the_prose_cites_controls_decisions_at_all() -> None:
    """Named so the check above cannot pass by looking at nothing.

    Every page that leans on a decision made in `control`: the six modules of
    the package that came across with its prose, the glossary, and the two
    READMEs that say what the mirror and the page do. `firmware.py` cites five
    of the seven, which is the file whose whole subject — writing a build onto
    the station the mirror is holding — was settled over there.
    """
    said = {
        page.relative_to(ROOT).as_posix()
        for page in prose()
        if any(
            found.group("owner") and found.group("number") in CONTROL
            for found in CITED.finditer(page.read_text())
        )
    }
    assert said == {
        "CONTEXT.md",
        "docs/dccex_usb/README.md",
        "docs/ui/README.md",
        "src/dccex_usb/__main__.py",
        "src/dccex_usb/face.py",
        "src/dccex_usb/firmware.py",
        "src/dccex_usb/framing.py",
        "src/dccex_usb/station.py",
        "src/dccex_usb/stream.py",
    }


def test_a_struck_owner_under_the_package_is_caught() -> None:
    """The scan, over a module of the package with an owner struck off.

    `stream.py`'s is the citation on `MAX_FRAME_BYTES`, which says why a frame
    larger than a command is not read. Both halves of the rule catch it today;
    `borrowed()` is the one that still would at 0042.
    """
    text = struck(ROOT / "src" / "dccex_usb" / "stream.py", "control ADR-0042")
    assert len(unresolved(text)) == 1, unresolved(text)
    assert borrowed(text) == unresolved(text)
    assert unresolved(text)[0].endswith("decides the size\nof (ADR-0042")


def test_a_struck_owner_under_the_docs_is_caught() -> None:
    """The same strike on a page under `docs/`, which is read alongside the
    package because a reader of one reads the other.

    The citation struck is the mirror's README on what a refusal is for, and
    it is struck by the sentence it sits in: the same page links that decision
    higher up, and a link is an owner, so a strike that went by the number
    alone would land on the link and catch nothing.
    """
    text = struck(ROOT / "docs" / "dccex_usb" / "README.md", "(control ADR-0050):")
    assert len(unresolved(text)) == 1, unresolved(text)
    assert borrowed(text) == unresolved(text)
    assert unresolved(text)[0].endswith("read a\nlog on the box (ADR-0050")


def test_a_number_this_repository_reaches_is_still_controls() -> None:
    """The collision the second half of the rule is for.

    `unresolved()` is handed the numbers `docs/adr/` would hold on the day
    this repository accepts an ADR-0043 of its own. The citation is `control`'s
    all the same and goes on resolving to the wrong file, which is what
    `borrowed()` says and the file check no longer can.
    """
    written = "everything else is a client of the port it serves (ADR-0043)"
    assert unresolved(written, ours() | {"0043"}) == []
    assert len(borrowed(written)) == 1, borrowed(written)


def test_an_owner_resolves_however_it_is_written() -> None:
    """The forms the repository writes an owner in, and the breaks prose takes.

    The backticks a repository gets in prose and the possessive a sentence
    sometimes wants; the wrap `docs/ui/README.md` already carries between the
    owner and the number, and the one `station.py` carries inside a comment
    block, where the line under it opens with the `#` the block is drawn with;
    and the phrase that names this repository. Any of the three owners
    resolves the name; what is forbidden is none of them.

    The organisation's is wrapped the same way in `face.py` and is held to it
    by the module beside this one, which is the module that owns that number.
    """
    for written in (
        "the link is the station answering (control ADR-0066)",
        "while the device is open (`control` ADR-0066). The link is down",
        "the order is `control`'s ADR-0065 and the whole of the care here",
        "anyone on the wifi choose what to run (control\nADR-0042)",
        "# not two that can drift apart (control\n# ADR-0066).",
        "superseding this repository's ADR-0002). The commit above",
    ):
        assert bare(written) == [], f"the owner was not read: {written!r}"


def test_a_link_into_controls_records_says_whose_the_decision_is() -> None:
    """A citation a reader can follow, and one they cannot.

    What resolves the number is where the link goes and not its text: a link
    to `control`'s record lands a reader on the decision, and a link to some
    third page leaves them exactly where a bare mention leaves them.
    """
    record = f"{CONTROL_ADRS}0066-the-link-is-the-station-answering-not-the-socket-being-open.md"
    assert bare(f"the link is the station answering ([ADR-0066]({record})).") == []
    loose = bare("the link is the station answering ([ADR-0066](../adr/0066.md)).")
    assert [number for number, _ in loose] == ["0066"], loose


def test_a_bare_citation_is_reported_where_it_sits() -> None:
    """The context a bare citation comes back with, on prose holding both.

    A link ahead of a bare citation is blanked rather than cut out, so what
    comes back is the forty characters the bare one actually sits in. A reader
    given the wrong forty would go looking on the wrong line — which is what
    `docs/dccex_usb/README.md`, holding a link to `control` ADR-0050 and a
    dozen citations after it, would hand them.
    """
    record = f"{CONTROL_ADRS}0050-broken-hardware-is-reported-never-worked-around.md"
    loose = bare(
        f"reported ([ADR-0050]({record})). It is fixed at the hardware (ADR-0050)."
    )
    assert len(loose) == 1, loose
    assert loose[0][1].endswith("It is fixed at the hardware (ADR-0050"), loose[0]


def test_the_records_are_not_read_and_are_carrying_what_they_would_be_red_on() -> None:
    """The one exclusion, and that there is something behind it.

    An exclusion with nothing behind it is an exclusion nobody would notice
    going wrong. ADR-0004 names `control` ADR-0042 in its **Related:** links
    and then writes the number alone five times in the prose under them, which
    is the shorthand a record is allowed and a docstring is not.
    """
    assert [page for page in prose() if ADRS in page.parents] == []
    door = (
        ADRS / "0004-the-face-reaches-a-browser-through-the-door-and-never-the-lan.md"
    )
    assert len(borrowed(door.read_text())) == 4, borrowed(door.read_text())


def test_the_borrowed_numbers_are_what_this_repository_links() -> None:
    """`CONTROL` against the links this repository's own ADRs carry.

    This is the check of a citation against `control`'s `docs/adr/` that #128
    asked for, made where it can be made: the URL of each record, with its
    title in the name of the file, is written down in this repository and is
    what a reader follows. A number cited here that no ADR of ours links is a
    number nobody checked.
    """
    linked = {
        found.group(1): found.group(2)
        for page in ADRS.glob("*.md")
        for found in re.finditer(
            rf"{re.escape(CONTROL_ADRS)}(\d{{4}})-([a-z0-9-]+)\.md", page.read_text()
        )
    }
    assert set(linked) == set(CONTROL)
    assert linked == {
        number: decided.replace(" ", "-").lower() for number, decided in CONTROL.items()
    }
