"""What the box at the foot sends for what was typed into it.

Pairs: this typing, this message. What leaves the page for the station is a
pure function of the text in the box (`ui/src/message.js`) — no socket, no
state, no clock and no DOM — so every spelling an operator may use is held
here as two strings, on a machine with nothing plugged in.

**The function is run rather than read**, for the reason `tests/ui/test_decoder.py`
gives and with more at stake: these bytes go down the cable to a command
station, and a rule about what goes down a cable asserted against the source
that would produce it is not asserted. So the pairs go through the real
function under `node`, by way of `tests/ui/message.mjs`, and what that asks of
the machine is a node and nothing else. The `node` marker is what asks it: the
gate does not collect these and the workflow runs them, where a node that is
not there is red rather than skipped (`scripts/check.sh`, #101).

It is why this and the decoder are written as JavaScript with their types in
JSDoc: they are two of the five run under a bare node, because they are what
decides what a person reads and what reaches the station. `tsc` checks them as
strictly as the rest (`ui/tsconfig.json`).

**Sending is exercised without a command station attached** twice over. Here,
as the page's own rule; and at the other end, where a page on the stream types
at a pty and the device gets whole messages
(`tests/dccex_usb/test_face.py`).
"""

import json
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

import pytest

from tests.ui.test_look import UI

#: The pure function, and the module it is the whole of.
MESSAGE = UI / "src" / "message.js"

#: What puts what was typed through it.
RUNNER = Path(__file__).resolve().parent / "message.mjs"

#: What an operator types, and the one whole message that goes up the stream
#: for it. The brackets are the station's rather than the operator's: `s` and
#: `<s>` are the same command, which is what the box promises (#6).
CASES: dict[str, str] = {
    "s": "<s>",
    "<s>": "<s>",
    " s ": "<s>",
    " <s> ": "<s>",
    "0": "<0>",
    "<0>": "<0>",
    "1 MAIN": "<1 MAIN>",
    "<1 MAIN>": "<1 MAIN>",
    "t 3 50 1": "<t 3 50 1>",
    "<t 3 50 1>": "<t 3 50 1>",
    # Half-typed brackets are the same command as none and as both. A person
    # who reached for the shift key once is not asking for a different message.
    "<s": "<s>",
    "s>": "<s>",
    # What is inside is the station's and is not read here: the station is
    # what refuses a command it does not know, and it says so with `<X>`.
    "D ACK ON": "<D ACK ON>",
    "nonsense": "<nonsense>",
    # Two messages typed at once go up as they were typed, in the one write.
    # The mirror's framing reads them as two whole messages and neither is
    # interleaved with anybody else's, which is the whole of what one write
    # buys (`framing.py`, ADR-0007 d.2). Nothing is swallowed and nothing is
    # rewritten: what an operator typed is what the station is asked.
    "<s><X>": "<s><X>",
}

#: What is typed when nothing is: an empty box, a box of spaces, and brackets
#: with nothing between them. A `<>` on the wire is a message the station would
#: refuse, and a page sending one would be typing at the railroad on its own
#: account.
SILENT: tuple[str, ...] = ("", " ", "   \t ", "<>", "< >", "<", ">", "<   >")


def asked() -> tuple[str, ...]:
    """Everything the suite types into the box."""
    return (*CASES, *SILENT)


def run(typed: tuple[str, ...]) -> tuple[str | None, ...]:
    """What the page sends for `typed`, in one running of the function."""
    node = shutil.which("node")
    assert node is not None, "no node on this machine to run the page's rule with"
    ran = subprocess.run(
        [node, str(RUNNER)],
        input=json.dumps(list(typed)),
        capture_output=True,
        text=True,
        check=False,
    )
    assert ran.returncode == 0, f"the rule did not run: {ran.stderr.strip()}"
    sent: list[str | None] = json.loads(ran.stdout)
    return tuple(sent)


@lru_cache(maxsize=1)
def sent() -> dict[str, str | None]:
    """Everything the suite types, put through the function once."""
    return dict(zip(asked(), run(asked()), strict=True))


@pytest.mark.node
@pytest.mark.parametrize("typed", CASES)
def test_what_is_typed_is_sent_as_one_whole_message(typed: str) -> None:
    assert sent()[typed] == CASES[typed]


@pytest.mark.node
@pytest.mark.parametrize("typed", CASES)
def test_what_is_sent_is_opened_and_closed_and_nothing_is_outside_it(
    typed: str,
) -> None:
    """A `<` at the front, a `>` at the back, and no stray byte either side.

    The mirror's framing drops what falls outside a message and starts one over
    at a `<` (`framing.py`), so a page that sent stray bytes would be relying on
    the other end to tidy up after it. Doubling a bracket is the way that
    happens: `<<s>` reaches the device as `<s>` and is a page that got lucky.
    """
    written = sent()[typed]
    assert written is not None
    assert written.startswith("<") and written.endswith(">")
    assert "<<" not in written and ">>" not in written


@pytest.mark.node
@pytest.mark.parametrize("typed", SILENT)
def test_nothing_typed_sends_nothing(typed: str) -> None:
    assert sent()[typed] is None


@pytest.mark.node
def test_the_brackets_are_the_stations_and_not_the_operators() -> None:
    """The criterion in one line: `s` and `<s>` do the same thing (#6).

    Everything the station understands is typed here, `<0>` included, because
    that is what a raw monitor is — and nothing on the page is a named control
    for any of it (docs/ui/README.md).
    """
    for bare, wrapped in (("s", "<s>"), ("0", "<0>"), ("1 MAIN", "<1 MAIN>")):
        assert sent()[bare] == sent()[wrapped] == wrapped


@pytest.mark.node
def test_the_same_typing_sends_the_same_message_whatever_came_before_it() -> None:
    """A pure function of the box's text (`message.js`), so what is sent cannot
    depend on what was sent a moment ago."""
    twice = (*asked(), *asked())
    assert run(twice) == run(tuple(reversed(twice)))[::-1]


def test_the_rule_holds_nothing() -> None:
    """No socket, no state, no clock and no DOM.

    Held against the source because it is the import that would bring one in: a
    module that decides what reaches a command station and can also reach a
    clock is one whose output is no longer a fact about what was typed.
    """
    source = MESSAGE.read_text()
    assert "import " not in source, "the rule imports something"
    for held in ("Date", "Math.random", "window", "document", "fetch", "WebSocket"):
        assert held not in source, f"the rule reaches {held}"
