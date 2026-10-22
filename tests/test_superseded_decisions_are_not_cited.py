"""A decision a later ADR superseded is not cited as standing.

ADR-0026 superseded ADR-0017 d.1 to d.3, and twelve citations of those
decisions stayed in `ui/src` and `docs/ui` until the final review of #322
found them (#324). Nothing read which decisions were superseded. This module
reads it off the **Status:** line of each record in `docs/adr/` and holds the
prose to it (#337).

**What is red.** A citation of this repository's `ADR-NNNN d.M` where that
record's status says d.M is superseded, and a bare `ADR-NNNN` of this
repository where the status says the whole record is. A bare citation of a
record only part of which is superseded is not red, and neither is a decision
that was amended.

**What passes.** A citation in a sentence that says "supersed", in any case,
which is how a page names the decision that replaced it (`ui/src/flash.js`). A
citation the modules beside this one resolve to another owner: `control`'s, or
the organisation's, whose record numbered 0002 is not this repository's.

**What is read.** The trees `tests/test_adr_numbers_resolve.py` reads, by its
`prose()`, minus this module and `tests/test_citations_resolve.py`, whose
citations of the number 0002 are the test data of each. The records are not
read: an ADR cites what it supersedes on purpose.
"""

import re
from itertools import pairwise
from pathlib import Path

from tests.test_adr_numbers_resolve import (
    ADRS,
    CONTROL_ADRS,
    GAP,
    ORG_ADRS,
    OWNER,
    ROOT,
    prose,
)

#: This module, which is not read.
SELF = Path(__file__).resolve()

#: The module that holds the number 0002 to an owner. Its bare citations of
#: it are what that scan is run over.
NUMBER_0002 = SELF.parent / "test_citations_resolve.py"

#: The status line of a record, up to the next field of its header. It wraps
#: as prose wraps, so it runs across line breaks.
STATUS = re.compile(
    r"^- \*\*Status:\*\*(?P<said>.*?)(?=^- \*\*|^\s*$)", re.MULTILINE | re.DOTALL
)

#: What a clause of the status supersedes: the words before "superseded by".
SUPERSEDED = re.compile(r"(?P<what>[^;]*?)\bsuperseded\s+by\b")

#: A decision, as a status or a citation writes one.
DECISION = re.compile(r"d\.(\d+)")

#: The decisions after a number: one, a list, or a range (`d.1–d.3`).
DECISIONS = r"d\.\d+(?:(?:\s*,\s*|\s+and\s+|\s*[–-]\s*|\s+to\s+)d\.\d+)*"

#: A citation, with its owner in front where there is one, the target of the
#: link it is the text of where it is one, and the decisions after it.
CITED = re.compile(
    rf"(?:(?P<owner>{OWNER}){GAP})?\[?ADR-(?P<number>\d{{4}})"
    rf"(?:\]\((?P<target>[^)\s]*)\))?"
    rf"(?:{GAP}(?P<decisions>{DECISIONS}))?"
)

#: Where a sentence ends: a stop before white space, or a blank line, which in
#: a comment block is a line holding only what the block is drawn with.
END = re.compile(r"[.!?](?=\s)|\n[ \t]*(?:[*#]|//)?[ \t]*\n")

#: What `superseded()` returns for a record superseded as a whole.
WHOLE = "whole"


def superseded(status: str) -> set[int] | str:
    """What a status supersedes: `WHOLE`, or the decisions by number.

    A clause that supersedes something it names without a decision number,
    such as ADR-0008's build on the band, supersedes nothing a citation can
    name and is ignored.
    """
    decisions: set[int] = set()
    for clause in status.split(";"):
        for found in SUPERSEDED.finditer(clause):
            what = found.group("what").strip()
            if not what:
                return WHOLE
            decisions |= {int(number) for number in DECISION.findall(what)}
    return decisions


def records() -> dict[str, set[int] | str]:
    """Every record in `docs/adr/` with something superseded, by number."""
    held: dict[str, set[int] | str] = {}
    for page in sorted(ADRS.glob("[0-9][0-9][0-9][0-9]-*.md")):
        status = STATUS.search(page.read_text())
        assert status, f"{page.name} has no status"
        if said := superseded(status.group("said")):
            held[page.name[:4]] = said
    return held


def decided(decisions: str) -> set[int]:
    """The decisions a citation names, with a range filled in."""
    named: set[int] = set()
    numbers = [int(number) for number in DECISION.findall(decisions)]
    for left, right in pairwise(numbers):
        if re.search(rf"d\.{left}\s*(?:[–-]|to)\s*d\.{right}", decisions):
            named |= set(range(left, right + 1))
    return named | set(numbers)


def ours(owner: str | None, target: str | None) -> bool:
    """Whether a citation means this repository's record."""
    if owner and not re.match(r"[Tt]his", owner):
        return False
    return not (target and target.startswith((CONTROL_ADRS, ORG_ADRS)))


def sentence(text: str, start: int, end: int) -> str:
    """The sentence a citation sits in."""
    left = max((stop.end() for stop in END.finditer(text, 0, start)), default=0)
    right = END.search(text, end)
    return text[left : right.start() if right else len(text)]


def stale(text: str, held: dict[str, set[int] | str] | None = None) -> list[str]:
    """Every citation of a superseded decision, by the sentence it sits in."""
    gone = records() if held is None else held
    found: list[str] = []
    for said in CITED.finditer(text):
        number = said.group("number")
        if number not in gone or not ours(said.group("owner"), said.group("target")):
            continue
        if said.group("decisions"):
            named = decided(said.group("decisions"))
            hit = gone[number] == WHOLE or bool(named & set(gone[number]))
        else:
            hit = gone[number] == WHOLE
        where = sentence(text, said.start(), said.end())
        if hit and "supersed" not in where.lower():
            found.append(" ".join(where.split()))
    return found


def read() -> list[Path]:
    """The pages this scan reads."""
    return [page for page in prose() if page not in (SELF, NUMBER_0002)]


def test_no_superseded_decision_is_cited() -> None:
    loose = {
        page.relative_to(ROOT).as_posix(): where
        for page in read()
        if (where := stale(page.read_text()))
    }
    assert loose == {}, f"a superseded decision, cited as standing: {loose}"


def test_the_statuses_supersede_something() -> None:
    """Named so the check above cannot pass by reading nothing.

    Every superseded decision the records say today, in each form the
    statuses write one.
    """
    assert records() == {
        "0002": WHOLE,
        "0008": {5},
        "0011": {1, 2, 4},
        "0017": {1, 2, 3},
        "0018": {2},
        "0020": {2, 3},
    }


def test_the_status_forms_parse() -> None:
    forms: tuple[tuple[str, set[int] | str], ...] = (
        ("superseded by\n  [ADR-0003](0003-x.md), 2026-09-22", WHOLE),
        ("accepted; d.5 superseded by [ADR-0011](0011-x.md)", {5}),
        (
            "accepted; d.1, d.2 and d.4 superseded by\n  [ADR-0017](0017-x.md)",
            {1, 2, 4},
        ),
        ("d.2 amended by [ADR-0023](x); d.1, d.2 and d.3 superseded by\n", {1, 2, 3}),
        (
            "d.2, d.3 and d.6 amended (#207);\n  d.2 amended again; d.2 superseded by",
            {2},
        ),
        (
            "accepted; the build on the band (amendment of 2026-09-30) superseded by",
            set(),
        ),
        ("accepted, 2026-10-08; d.2 amended by [ADR-0023](x)", set()),
    )
    for status, said in forms:
        assert superseded(status) == said, status


def test_a_superseded_decision_in_a_page_module_is_red() -> None:
    page = ROOT / "ui" / "src" / "bus.ts"
    assert page in read()
    text = f"{page.read_text()}\n * the band sends `<1>` (ADR-0017 d.2).\n"
    assert stale(text) == ["* the band sends `<1>` (ADR-0017 d.2)"]


def test_a_superseded_decision_is_red_across_a_line_break() -> None:
    assert len(stale(" * the band sends `<1>` (ADR-0017\n * d.1).")) == 1
    assert len(stale("the band presses it (ADR-0011 d.3, d.4).")) == 1
    assert len(stale("the band presses it (ADR-0017 d.1–d.3).")) == 1


#: The number this repository's superseded record shares with the
#: organisation's, written apart as `tests/test_adr_numbers_resolve.py` writes
#: it: the module beside this one reads this one, and every citation of the
#: number here is test data.
TWO = "ADR-" + "0002"


def test_this_repositorys_superseded_record_is_red() -> None:
    for written in (
        f"a defect is fixed where it came from ({TWO}).",
        f"a defect is fixed where it came from (this repository's {TWO}).",
        f"a defect is fixed upstream ([{TWO}](docs/adr/0002-x.md)).",
    ):
        assert len(stale(written)) == 1, written


def test_another_owners_record_passes() -> None:
    org = f"{ORG_ADRS}0002-a-ui-talks-to-the-bus-the-store-and-its-own-apps-face.md"
    for written in (
        f"what the page talks to (the organisation's {TWO}).",
        f"what the page talks to (the organisation's\n * {TWO}).",
        f"what the page talks to (org {TWO}).",
        f"what the page talks to ([{TWO}]({org})).",
        "the link is the station answering (control ADR-0017 d.1).",
        f"the app flashes ([control\nADR-0017]({CONTROL_ADRS}0017-x.md) d.2).",
    ):
        assert stale(written) == [], written


def test_a_sentence_that_says_superseding_passes() -> None:
    page = ROOT / "ui" / "src" / "flash.js"
    assert "(ADR-0026 d.2, superseding ADR-0017 d.1)" in page.read_text()
    assert stale(page.read_text()) == []
    assert stale(f"superseding this repository's {TWO}). The commit") == []


def test_a_sentence_that_says_supersed_in_any_case_passes() -> None:
    for written in (
        "Superseded by ADR-0026, ADR-0017 d.1 no longer holds.",
        "SUPERSEDED BY ADR-0026: ADR-0017 d.1.",
    ):
        assert stale(written) == [], written
    assert len(stale("ADR-0017 d.1 no longer holds.")) == 1


def test_an_amended_or_standing_decision_passes() -> None:
    for written in (
        "red on the page is a stop or a fault (ADR-0017 d.6).",
        "the button is look's toggle (ADR-0017).",
        "the stash is cleared at boot (ADR-0018 d.3).",
        "the build is read off the banner (ADR-0008 d.3).",
    ):
        assert stale(written) == [], written


def test_the_records_and_this_module_are_not_read() -> None:
    """The exclusions, and that each carries something it would be red on."""
    pages = read()
    assert [page for page in pages if ADRS in page.parents] == []
    assert SELF not in pages
    assert NUMBER_0002 not in pages
    assert stale(NUMBER_0002.read_text()), f"nothing stale left in {NUMBER_0002.name}"
    superseding = ADRS / "0026-the-bands-power-control-is-controls.md"
    unsaid = re.sub("supersed", "", superseding.read_text(), flags=re.IGNORECASE)
    assert stale(unsaid), superseding.name
    assert stale(SELF.read_text()), "nothing stale left in this module"
