"""The one place a module of the page is run under a node.

What `tests/ui/node.py` is for is the duplication it ended: seven checks that
run the page's functions rather than reading them, each with its own copy of
the same few lines (#98). What is held here is the two assertions that copy was
worth keeping — a node that is not there and a runner that did not run are both
red, and both say what could not be run — and that no module has a copy of them
left.

The runners used here are written for the assertion and thrown away. The seven
real ones are each their own module's, and what they answer is that module's
claim rather than this one's.
"""

import shutil
from pathlib import Path

import pytest

from tests.ui.node import ran
from tests.ui.test_look import ROOT

#: The suite's own directory: where the runners are, and where a copy of what
#: `node.py` does would show up.
HERE = Path(__file__).resolve().parent

#: What the scans below walk past: the one module allowed to run a runner,
#: and this one, which has to spell what it is looking for to look for it.
SPELT = {HERE / "node.py", Path(__file__).resolve()}

#: Finding the node, and starting it. The two halves that were copied.
FINDS = 'shutil.which("node")'
STARTS = "subprocess"


def test_a_node_that_is_not_there_says_what_could_not_be_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Red rather than skipped, and naming the thing rather than the file.

    A machine with no node deselects these checks by the `node` marker
    (`pyproject.toml`); one that got past the marker and has no node is a
    broken machine, and a gate that shrugged at it would be green while
    running nothing.
    """

    def nowhere(name: str) -> str | None:
        return None

    monkeypatch.setattr(shutil, "which", nowhere)
    with pytest.raises(AssertionError, match="no node on this machine to run"):
        ran(HERE / "gloss.mjs", [], "the decoder")


@pytest.mark.node
def test_a_runner_that_did_not_run_says_so_with_its_stderr(tmp_path: Path) -> None:
    """The stderr is the message, because that is where the reason is.

    A JSDoc type error, a bad import or a module that threw all come out
    there, and a failure that said only that the exit status was 1 would send
    a reader back to run it by hand.
    """
    runner = tmp_path / "broken.mjs"
    runner.write_text('import { nothing } from "node:fs";\nnothing();\n')
    with pytest.raises(
        AssertionError,
        match=r"(?s)the decoder did not run: .*does not provide an export named",
    ):
        ran(runner, [], "the decoder")


def test_a_node_is_found_in_one_place() -> None:
    """The whole suite's, and not this directory's alone.

    It is one line and it is the kind of line that gets copied to wherever the
    next runner is written, which is how there came to be seven of it (#98).
    """
    found = sorted(
        str(module.relative_to(ROOT))
        for module in ROOT.glob("tests/**/*.py")
        if module not in SPELT and FINDS in module.read_text()
    )
    assert found == [], f"a node is found in {found} as well"


def test_a_runner_is_started_in_one_place() -> None:
    """A module that names a runner does not start one.

    Said of the modules that name a `.mjs` rather than of every module here,
    because `tests/ui/test_page_serves.py` runs `docker` and shares none of
    this (#98).
    """
    started = sorted(
        str(module.relative_to(ROOT))
        for module in HERE.glob("*.py")
        if module not in SPELT and ".mjs" in module.read_text()
        if STARTS in module.read_text()
    )
    assert started == [], f"a runner is started in {started} as well"
