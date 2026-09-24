"""What the page makes of a line of the station's conversation.

Pairs: these bytes, this sentence, and the fact that came with it. The
**decoder** is a pure function of one line (ADR-0009 d.1) — no socket, no
state, no clock and no DOM — so every line the page claims to recognise is held
here as what it says and what it reads as, on a machine with nothing plugged
in.

**Both halves are the same reading** (#7). The sentence goes beside the bytes
on the monitor and the fact goes to the band and the tiles, and they come off
one line and one regular expression, so a page cannot show a reading it cannot
say or say something it has not read (ADR-0008 d.2).

**The function is run rather than read.** Every other check of the page in this
suite reads its sources, because the gate is Python and there is no browser in
it (`tests/ui/test_stream.py`). This one cannot: a sentence the page shows an
operator is worth nothing asserted against the source that would produce it,
and ADR-0009 d.3 asks for the pairs themselves. So the pairs go through the
real function under `node`, by way of `tests/ui/gloss.mjs`.

What that costs is a node on the machine the gate runs on, and no more than
that: no packages are installed, nothing is bundled and nothing is fetched.
It is why the decoder is written as JavaScript with its types in JSDoc rather
than as TypeScript — `tsc` still checks it (`ui/tsconfig.json`), and a bare
node can still run it. What the box at the foot sends and what the band and
the tiles read are the other two modules written that way, for the same reason
(`tests/ui/test_message.py`, `tests/ui/test_readings.py`).

A node that is not there is red rather than skipped, as everything else the
gate needs is: a check that skips itself leaves a required gate green while
proving nothing (`scripts/check.sh`).
"""

import json
import re
import shutil
import string
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

#: The lines that carry a fact as well as a sentence, and the fact they carry.
#: Every reading the **band** and the **tile**s are made of is off one of these
#: (ADR-0008 d.2); a line not named here says its sentence and nothing more.
FACTS: dict[str, dict[str, object]] = {
    "<p0>": {"hot": False},
    "<p1>": {"hot": True},
    "<p1 MAIN>": {"hot": True},
    " <p0> ": {"hot": False},
    "<iDCC-EX V-5.0.7 / MEGA / STANDARD_MOTOR G-9db6d10>": {"build": "9db6d10"},
    "<c CurrentMAIN 123 C Milli 0 0 4000 1000>": {"milliamps": 123},
}

#: The near misses: a line the decoder half-recognises, and gets nothing for.
#: A malformed payload, a truncated message, and a whole message the station
#: says in a letter the page has never learned — which is the common one. This
#: fork answers a subset of DCC-EX's vocabulary and upstream adds to it, so a
#: station saying something new degrades to a stream of raw lines rather than
#: to a page of confident nonsense (ADR-0009).
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
    "<l 3 0 128 0>",
    "<Q 12>",
    "<* Power overload *>",
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


def run(lines: tuple[str, ...]) -> tuple[dict[str, object] | None, ...]:
    """What the decoder makes of `lines`, in one running of it.

    A reading apiece, or nothing: the sentence under `say` and whatever fact
    the line carried beside it.
    """
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
    read: list[dict[str, object] | None] = json.loads(ran.stdout)
    return tuple(read)


@lru_cache(maxsize=1)
def readings() -> dict[str, dict[str, object] | None]:
    """Every line the suite asks about, put through the decoder once."""
    return dict(zip(asked(), run(asked()), strict=True))


def glossed() -> dict[str, str | None]:
    """The sentence half of every reading, which is what the monitor draws.

    A reading that is there says its sentence as a string, and the check is
    written out rather than cast: a decoder that answered with something else
    under `say` is a page drawing whatever that is beside the bytes.
    """
    said: dict[str, str | None] = {}
    for line, reading in readings().items():
        if reading is None:
            said[line] = None
            continue
        say = reading["say"]
        assert isinstance(say, str), f"{line!r} reads as {say!r} and not a sentence"
        said[line] = say
    return said


def facts() -> dict[str, dict[str, object]]:
    """The other half: what a line the decoder recognised says as a reading,
    with the sentence off it."""
    return {
        line: {name: was for name, was in reading.items() if name != "say"}
        for line, reading in readings().items()
        if reading is not None
    }


@pytest.mark.parametrize("line", CASES)
def test_a_line_the_page_glosses_reads_as_its_sentence(line: str) -> None:
    assert glossed()[line] == CASES[line]


@pytest.mark.parametrize("line", FACTS)
def test_a_line_that_carries_a_reading_carries_it(line: str) -> None:
    """The fact the band and the tiles are made of, off the same line as the
    sentence (ADR-0008 d.2)."""
    assert facts()[line] == FACTS[line]


@pytest.mark.parametrize("line", [line for line in CASES if line not in FACTS])
def test_a_line_that_reads_as_nothing_but_a_sentence_carries_no_fact(
    line: str,
) -> None:
    """A turnout thrown and a command refused are sentences and no reading.

    Nothing on this page is about a railroad (ADR-0008), so a field that is
    not on the line is absent rather than a zero somebody could draw.
    """
    assert facts()[line] == {}


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


def test_no_letter_the_decoder_does_not_know_is_glossed() -> None:
    """The other direction from the case above, over the whole alphabet.

    The station says far more than the page has learned, and what it says next
    is upstream's to decide (ADR-0009 d.5). A letter outside the table gets
    nothing back however well-formed the message around it is, which is what
    makes a firmware that has grown a stream of raw lines rather than a page of
    confident nonsense.
    """
    strangers = tuple(
        f"<{letter} 1 2 3>" for letter in string.ascii_letters if letter not in reads()
    )
    assert len(strangers) > 1, "the decoder claims most of the alphabet"
    assert run(strangers) == (None,) * len(strangers)


def test_every_fact_the_decoder_reads_is_one_the_readings_are_made_of() -> None:
    """The other direction from the cases above: the decoder reads what the
    band and the tiles are built out of and nothing besides.

    A field nobody draws is a field that drifts unseen, and one the page draws
    without a pair beside it is a reading nobody ever read (ADR-0009 d.3).
    """
    read = {name for fact in facts().values() for name in fact}
    asserted = {name for fact in FACTS.values() for name in fact}
    assert read == asserted


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


def test_the_decoder_is_the_one_place_a_line_is_read() -> None:
    """One place the protocol is known (ADR-0009 d.3), and it is not on the way
    in: the stream carries bytes and reads none of them (ADR-0008 d.2).

    Two modules ask it, and neither of them knows a letter of the station's
    vocabulary. The monitor asks for the sentence it draws beside the bytes,
    and `readings.js` asks for the fact and folds it into what the band and
    the tiles show (#7) — which is what keeps the vocabulary in one file when
    the page grew a second thing to do with it.
    """
    importers = {
        module.name
        for kind in ("*.ts", "*.js")
        for module in sorted((UI / "src").rglob(kind))
        if f'from "{"../" if module.parent.name == "ui" else "./"}decoder.js"'
        in module.read_text()
    }
    assert importers == {
        "dccex-monitor.ts",
        "readings.js",
    }, f"the decoder is read in {importers}"
