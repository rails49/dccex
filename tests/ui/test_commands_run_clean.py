"""The environment the docker checks run their commands in, held without one.

`tests/ui/test_compose_serves.py` and `tests/ui/test_page_serves.py` both carry
the `docker` marker, because what they are about is a daemon building and
running things. The helpers they run those commands through are not about a
daemon at all: `environment()` is a dict comprehension over `os.environ`, and
what it drops decides which project every command below it acts on. That is a
`monkeypatch` and an assertion, and a machine with no daemon can make it.

**So it lives here, in the gate.** A check under the `docker` marker is a check
`scripts/check.sh` does not collect, and the gate's own rule is that a
daemonless machine — the agent sandbox is one — must be able to run all of it
(`scripts/check.sh`, `tests/deploy/test_deploy_runs.py` argues the same rule
from the other side). A daemonless check filed under that marker runs only in
the workflow's docker job, which is the slow half of the split and not the half
this belongs in (#112).

What is *not* here is anything that reads a daemon's answer. Those stay beside
the project they bring up.
"""

import pytest

from tests.ui.test_compose_serves import DROPPED, environment


def test_the_shell_cannot_point_these_commands_at_another_project(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The variables that outrank what `arguments()` passes, set and gone.

    The one above is the guard against acting on a project somebody else
    brought up. This is the guard against acting on one nobody here named:
    `COMPOSE_PROJECT_NAME` beats the file's `name: dccex`, and `COMPOSE_FILE`
    and `COMPOSE_ENV_FILE` beat the `-f` and the `--env-file`. A shell left
    over from a deploy has them, and the tear-down is where it would tell —
    `down --rmi all` against whatever else was named that, with this check's
    own containers left standing.

    It needs no daemon and asserts nothing about one. It sits here rather than
    in a module the gate collects because what it is about is this module's own
    `environment()`, and the docker job the workflow requires runs it.
    """
    # The three are written out rather than read off `DROPPED`, for the reason
    # `ROUTE` is written out: a check that took its list from the thing it is
    # checking would pass on whatever that list happened to say.
    overriding = ("COMPOSE_PROJECT_NAME", "COMPOSE_FILE", "COMPOSE_ENV_FILE")
    for name in (*DROPPED, *overriding):
        monkeypatch.setenv(name, "somebody-elses")

    clean = environment()

    assert [name for name in overriding if name in clean] == []
    assert [name for name in DROPPED if name in clean] == []
    assert "PATH" in clean, "the environment was emptied rather than cleaned"
    # What the fixture sets is set after the cleaning, so a name on the list is
    # still one this check can give a value to.
    assert environment(DCCEX_COMMIT="check-0")["DCCEX_COMMIT"] == "check-0"
