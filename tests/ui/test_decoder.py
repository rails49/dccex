"""What the page makes of a line of the station's conversation.

Pairs: these bytes, this sentence. The **decoder** is a pure function of one
line (ADR-0009 d.1) — no socket, no state, no clock and no DOM — so every line
the page claims to recognise is held here as two strings, on a machine with
nothing plugged in.

**The function is run rather than read.** Every other check of the page in this
suite reads its sources, because the gate is Python and there is no browser in
it (`tests/ui/test_stream.py`). This one cannot: a sentence the page shows an
operator is worth nothing asserted against the source that would produce it,
and ADR-0009 d.3 asks for the pairs themselves. So the pairs go through the
real function under `node`, by way of `tests/ui/gloss.mjs`.

What that costs is a node on the machine the gate runs on, and no more than
that: no packages are installed, nothing is bundled and nothing is fetched.
It is why the decoder is the one module of the page written as JavaScript with
its types in JSDoc rather than as TypeScript — `tsc` still checks it
(`ui/tsconfig.json`), and a bare node can still run it.

A node that is not there is red rather than skipped, as everything else the
gate needs is: a check that skips itself leaves a required gate green while
proving nothing (`scripts/check.sh`).
"""

import json
import re
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

import pytest

from tests.ui.test_look import UI

#: The pure function, and the module it is the whole of.
DECODER = UI / "src" / "decoder.js"

#: What puts a line through it.
RUNNER = Path(__file__).resolve().parent / "gloss.mjs"

#: Every line the page glosses, and the sentence it reads it as. A case is two
#: strings (ADR-0009 d.3), and what the decoder knows grows by adding one.
CASES: dict[str, str] = {
    "<p0>": "track power is off",
    "<p1>": "track power is on",
    "<p1 MAIN>": "MAIN track power is on",
    "<H 12 1>": "turnout 12 is thrown",
    "<H 12 0>": "turnout 12 is closed",
    "<iDCC-EX V-5.0.7 / MEGA / STANDARD_MOTOR G-9db6d10>": (
        "the station came up running DCC-EX 5.0.7 on MEGA, build 9db6d10"
    ),
    "<c CurrentMAIN 123 C Milli 0 0 4000 1000>": (
        "the MAIN track is drawing 123 milliamps"
    ),
    "<X>": "the station rejected that command",
    " <p0> ": "track power is off",
}

#: The near misses: a line the decoder half-recognises, and gets nothing for.
SILENT: tuple[str, ...] = (
    "<p>",
    "<p3>",
    "<H 12>",
    "<H 12 2>",
    "<H twelve 1>",
    "<X 1>",
    "<c CurrentMAIN>",
    "<c CurrentMAIN 123 C Amps 0 0 4000 1000>",
    "<iDCC-EX V-5.0.7 / MEGA / STANDARD_MOTOR>",
    "<iDCC-EX V-5.0.7 / MEGA / STANDARD_MOTOR G-9db6d10",
    "<>",
    "",
    "p0",
    "<p0",
    "<p0><X>",
    "the station is not talking",
)


def asked() -> tuple[str, ...]:
    """Every line the suite puts through the decoder."""
    return (*CASES, *SILENT)


def run(lines: tuple[str, ...]) -> tuple[str | None, ...]:
    """What the decoder makes of `lines`, in one running of it."""
    node = shutil.which("node")
    assert node is not None, "no node on this machine to run the decoder with"
    ran = subprocess.run(
        [node, str(RUNNER)],
        input=json.dumps(list(lines)),
        capture_output=True,
        text=True,
        check=False,
    )
    assert ran.returncode == 0, f"the decoder did not run: {ran.stderr.strip()}"
    read: list[str | None] = json.loads(ran.stdout)
    return tuple(read)


@lru_cache(maxsize=1)
def glossed() -> dict[str, str | None]:
    """Every line the suite asks about, put through the decoder once."""
    return dict(zip(asked(), run(asked()), strict=True))


@pytest.mark.parametrize("line", CASES)
def test_a_line_the_page_glosses_reads_as_its_sentence(line: str) -> None:
    assert glossed()[line] == CASES[line]


@pytest.mark.parametrize("line", SILENT)
def test_a_line_the_page_half_recognises_says_nothing(line: str) -> None:
    """A known letter with the wrong arity, a truncated line, a line that is
    not a message at all: nothing back, and the monitor shows it raw (ADR-0009
    d.2)."""
    assert glossed()[line] is None


def reads() -> set[str]:
    """The letters the decoder says it knows, read off the table it dispatches
    on (`READS`)."""
    table = re.search(r"const READS = \{(.*?)\n\};", DECODER.read_text(), re.DOTALL)
    assert table is not None, "the decoder has no table of what it knows"
    return set(re.findall(r"^\s*(\S+):", table.group(1), re.MULTILINE))


def test_every_line_the_page_glosses_has_a_case() -> None:
    """The suite is the whole of what the page claims to recognise.

    A letter the decoder learns without a pair beside it is a sentence an
    operator can be shown that nobody ever read (ADR-0009 d.3, d.5).
    """
    asserted = {line.strip()[1:2] for line in CASES}
    assert reads() <= asserted, f"nothing asserts {sorted(reads() - asserted)}"


def test_the_decoder_holds_nothing() -> None:
    """No socket, no state, no clock and no DOM (ADR-0009 d.1).

    Held against the source because it is the import that would bring one in:
    a module of the page that reaches a clock can start being about more than
    the line it was handed, and then a gloss is no longer a fact about those
    bytes.
    """
    source = DECODER.read_text()
    assert "import " not in source, "the decoder imports something"
    for held in ("Date", "Math.random", "window", "document", "fetch", "WebSocket"):
        assert held not in source, f"the decoder reaches {held}"


def test_the_same_line_reads_the_same_whatever_came_before_it() -> None:
    """Given the same line it returns the same sentence for ever (ADR-0009
    d.1), so a gloss cannot depend on what the station said a moment ago."""
    twice = (*asked(), *asked())
    assert run(twice) == run(tuple(reversed(twice)))[::-1]
