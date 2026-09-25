"""The environment the docker checks run their commands in, held without one.

`tests/ui/test_compose_serves.py` and `tests/ui/test_page_serves.py` both carry
the `docker` marker, because what they are about is a daemon building and
running things. The helpers they run those commands through are not about a
daemon at all: `environment()` is a dict comprehension over `os.environ` and
what it drops decides which project every command below it acts on, and
`docker()` hands what it is given to the process it starts, whichever `docker`
the path finds. That is a `monkeypatch`, a program of this module's own and
some assertions, and a machine with no daemon can make them.

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

from pathlib import Path

import pytest

from tests.ui.test_compose_serves import DROPPED, environment
from tests.ui.test_page_serves import docker


def test_the_shell_cannot_point_these_commands_at_another_project(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The variables that outrank what `arguments()` passes, set and gone.

    `test_a_project_already_up_is_refused_with_a_sentence`, beside the compose
    check, is the guard against acting on a project somebody else brought up.
    This is the guard against acting on one nobody named at all:
    `COMPOSE_PROJECT_NAME` beats the file's `name: dccex`, and `COMPOSE_FILE`
    and `COMPOSE_ENV_FILE` beat the `-f` and the `--env-file`. A shell left
    over from a deploy has them, and the tear-down is where it would tell —
    `down --rmi all` against whatever else was named that, with the compose
    check's own containers left standing.

    What it is about is `environment()`, which is the compose check's; what it
    needs is a `monkeypatch`, which is any machine's. So it is asserted from
    here, where the gate collects it, against the function imported from
    there (#112).
    """
    # The three are written out rather than read off `DROPPED`, for the reason
    # `ROUTE` is written out in `tests/ui/test_compose_serves.py`: a check that
    # took its list from the thing it is checking would pass on whatever that
    # list happened to say.
    overriding = ("COMPOSE_PROJECT_NAME", "COMPOSE_FILE", "COMPOSE_ENV_FILE")
    for name in (*DROPPED, *overriding):
        monkeypatch.setenv(name, "somebody-elses")

    clean = environment()

    assert [name for name in overriding if name in clean] == []
    assert [name for name in DROPPED if name in clean] == []
    assert "PATH" in clean, "the environment was emptied rather than cleaned"
    # What the compose check's `up` fixture sets is set after the cleaning, so
    # a name on the list is still one that check can give a value to.
    assert environment(DCCEX_COMMIT="check-0")["DCCEX_COMMIT"] == "check-0"


def test_a_plain_docker_command_runs_in_the_environment_it_was_given(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`docker()`, asked in front of a program that says what it was handed.

    The compose check runs `docker compose` through `compose()`, which takes an
    environment, and four plain `docker` commands through the helper it imports
    from the page-serves check, which did not. So the sentence above `DROPPED`
    — the list is what is dropped from the environment *every* command below
    runs in — was false for those four: an `inspect` of the container, an
    `inspect` of its image and the two tear-down `ls` commands ran with
    whatever the shell had (#113).

    Nothing read one of the six, so nothing was broken; what was missing was
    the invariant. It is held here, where no daemon is needed to hold it: the
    `docker` on the path is a script of this check's own that prints one
    variable, so what the helper hands the process it starts is what comes
    back. Without `env` it inherits, which is what the page-serves and
    mirror-serves checks have always had.
    """
    saying = tmp_path / "docker"
    saying.write_text('#!/bin/sh\nprintf %s "${DCCEX_COMMIT-}"\n')
    saying.chmod(0o755)
    for name in DROPPED:
        monkeypatch.setenv(name, "somebody-elses")
    # The helper names `docker` and not a path, so the program it finds is the
    # one on this variable — which is the only reason this runs on a machine
    # with a daemon as safely as on one without.
    monkeypatch.setenv("PATH", str(tmp_path))

    assert docker("inspect") == "somebody-elses", "nothing passed, and none inherited"
    assert docker("inspect", env=environment()) == "", "the shell's value reached it"
