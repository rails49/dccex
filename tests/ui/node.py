"""Running one of the page's own modules, under a bare node.

Seven of the checks here put the page's real functions through themselves
rather than reading the source that would produce their answers (ADR-0009 d.3,
`tests/ui/test_decoder.py`), and every one of them needs the same few lines to
do it: find a node, hand a runner beside this file a JSON payload on stdin,
and read a JSON answer back off stdout. They were written one per issue, each
copying the last, until there were seven of them — a shape that guarantees the
eighth (#98).

This is the one of them, and it keeps the assertions that are worth keeping. A
node that is not there is red rather than a silent skip, as everything else the
gate needs is (`scripts/check.sh`, #101). A runner that exited non-zero is red
with its stderr in the message, because a JSDoc type error or a bad import is
what comes out on that stream and a reader of the failure needs it.

The `node` marker is not here. It is on the tests, where a machine without one
deselects them (`pyproject.toml`); this is what runs once the marker has
already let a test through. Every module keeps its own runner, its own cases,
its own docstring and its own word for what could not be run.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


def ran(runner: Path, asks: Any, what: str, *, zone: str | None = None) -> Any:
    """What `runner` printed for `asks`, in one running of it.

    `asks` goes up as JSON and what comes back is read as JSON: what a
    module hands this and what it gets back are its own business and not this
    function's.

    `what` is what a person is told could not be run — "the decoder", "the
    sequence". It is the calling module's word for the thing rather than the
    runner's file name, because the file is this suite's and the word is the
    page's.

    `zone` is the machine's own time zone for the running, for the one rule
    that is about it (`tests/ui/test_monitor.py`).
    """
    node = shutil.which("node")
    assert node is not None, f"no node on this machine to run {what} with"
    done = subprocess.run(
        [node, str(runner)],
        input=json.dumps(asks),
        capture_output=True,
        text=True,
        check=False,
        env=None if zone is None else {**os.environ, "TZ": zone},
    )
    assert done.returncode == 0, f"{what} did not run: {done.stderr.strip()}"
    return json.loads(done.stdout)
