"""The deploy, run rather than read: what it leaves behind when the `up` fails.

`test_stack.py` reads `scripts/deploy.sh`, because most of what a box needs of
it is a claim about what is written down. This does not: what a failed `up`
leaves in `.env` is a sequence — a file written before compose is told to read
it, and put back afterwards — and reading the lines in order is how the bug
this is about (#83) was written in the first place.

**So the box's half is run here.** The script is one ssh and one heredoc, and
what goes over the wire is a program: a fake `ssh` on `PATH` saves the heredoc
instead of carrying it, and it is run under `bash` on this machine against a
clone this module makes, a fake `docker` that fails or does not, and a fake
`box.env`. Nothing here needs a daemon, a network or a box, which is what keeps
it in the gate — a `bash` and a `git`, which is what a gate that is a bash
script over a git checkout has already asked of the machine, so neither is a
marker of its own (`pyproject.toml`). A machine without either is red here
rather than skipped.

**Two absolute paths and the origin are pointed at what this machine has.**
`/etc/rails49/box.env` is root-owned and `/var/lib/rails49/deploys/dccex` is the
box's record, and neither is this suite's to make; the origin is this
repository on GitHub, which the script writes down as a constant of its own and
no variable can move (#102), and fetching from it would be a gate that reaches
the network. So each is replaced in the saved program with something under
`tmp_path` — the two paths once each, the origin in all three places it is
named — and every replacement is asserted to have matched as many times as it
is written: a substitution that silently found nothing would run a script that
refuses at its first guard and prove nothing. That these three are the ones
written down is `test_stack.py`'s claim and stays there.

**What the clone's own origin says before the run is this module's to vary.**
A clone with no remote named `origin` is the one `git remote set-url` fails on
(#119), and a clone somebody repointed by hand is the one the setting is there
for at all, so `Remote` below names the three boxes deployed onto here and the
end state each reaches is asserted rather than read off the script.

**What is not held here** is the exit status reaching the person who typed the
command: `ssh` carries it back from a box and the fake one does not, so what is
asserted is that the program exits non-zero, which is the half of it that is
this repository's.
"""

import os
import stat
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from tests.deploy.test_stack import DECLARATION, DEPLOY, ORIGIN, RECORD

#: The commit a box is on before the deploy under test — a full-length one,
#: because that is what `git rev-parse HEAD` gives the script and what the
#: record's column is written for.
RUNNING = "8f2c1d4bd9a0e6c5f3a71b28e40d9c6b5a3f7e11"

#: What the fake `docker` says when it is the one that fails. The deploy's own
#: sentence has to be findable underneath compose's.
DAEMON = "the daemon has gone away"


class Remote(Enum):
    """What the clone's `origin` says before the deploy is run."""

    #: Pointed at the origin this module made, which is where `git clone` left
    #: it and what every check that is not about the origin deploys onto.
    AS_CLONED = "as cloned"

    #: Pointed somewhere else by hand, which is the clone the origin is set
    #: rather than believed for (control#541). It is a path on this machine
    #: that does not exist, so a deploy that fetched from it instead of
    #: correcting it fails here rather than reaching the network.
    REPOINTED = "repointed by hand"

    #: No remote named `origin` at all, which `git remote set-url` fails on and
    #: `set -e` stopped the deploy over (#119).
    MISSING = "no origin"


@dataclass(frozen=True)
class Box:
    """A box the deploy has been run against on this machine."""

    #: The clone the program brought up, which is where `.env` is.
    clone: Path

    #: What stands in for `/var/lib/rails49/deploys/dccex`.
    record: Path

    #: The commit the deploy was bringing up: the clone's `HEAD`.
    commit: str

    #: What stands in for the script's own `ORIGIN` in the program that ran:
    #: the bare repository under `tmp_path` a clone here can fetch from.
    points_at: str

    #: What `.env` said when compose was called, saved by the fake `docker`.
    told: str | None

    #: How compose was called, as one line of arguments.
    called: str

    #: The program's own exit status, standard output and standard error.
    ran: "subprocess.CompletedProcess[str]"

    @property
    def env(self) -> str | None:
        """What `.env` says now, or `None` where there is no such file."""
        env = self.clone / ".env"
        return env.read_text() if env.exists() else None

    @property
    def origin(self) -> str | None:
        """What the clone's remote named `origin` is now, or `None` where the
        clone has no such remote."""
        got = subprocess.run(
            ("git", "-C", str(self.clone), "remote", "get-url", "origin"),
            capture_output=True,
            text=True,
            check=False,
        )
        return got.stdout.strip() if got.returncode == 0 else None

    @property
    def lines(self) -> list[str]:
        """What the record says, one line per deploy (ADR-0005 d.5)."""
        return self.record.read_text().splitlines()


def executable(path: Path, script: str) -> None:
    """One of the two commands the program reaches for, written and made
    runnable."""
    path.write_text(script)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def a_clone(tmp_path: Path, home: Path) -> str:
    """A clean clone of a repository on a box, with an origin to fetch from.

    The bare repository returned is what the script's own origin is pointed at
    in the program below, in place of this repository on GitHub.

    `.gitignore` carries `.env`, as this repository's does and for the reason
    written there: the deploy writes that file into the clone, and a clone the
    file made dirty is one the very next deploy refuses (ADR-0005 d.4).
    """
    origin = tmp_path / "origin.git"
    seed = tmp_path / "seed"
    git = ("git", "-c", "user.name=a box", "-c", "user.email=box@example.invalid")
    subprocess.run(("git", "init", "--bare", "-b", "main", str(origin)), check=True)
    subprocess.run(("git", "init", "-b", "main", str(seed)), check=True)
    (seed / ".gitignore").write_text(".env\n")
    subprocess.run((*git, "-C", str(seed), "add", "."), check=True)
    subprocess.run((*git, "-C", str(seed), "commit", "-m", "a commit"), check=True)
    subprocess.run(
        (*git, "-C", str(seed), "push", "--quiet", str(origin), "main"), check=True
    )
    subprocess.run(
        ("git", "clone", "--quiet", str(origin), str(home / "dccex")), check=True
    )
    return str(origin)


def deployed(
    tmp_path: Path,
    *,
    env: str | None,
    comes_up: bool,
    remote: Remote = Remote.AS_CLONED,
) -> Box:
    """The deploy, run against a box made here.

    `env` is what `.env` says before the run, or `None` for a box that has
    never had one — the first deploy onto a fresh box. `comes_up` is whether
    the `up` succeeds. `remote` is what the clone's `origin` says before the
    run.
    """
    home = tmp_path / "home"
    home.mkdir()
    binaries = tmp_path / "bin"
    binaries.mkdir()
    origin = a_clone(tmp_path, home)
    clone = home / "dccex"
    if remote is Remote.REPOINTED:
        subprocess.run(
            (
                "git",
                "-C",
                str(clone),
                "remote",
                "set-url",
                "origin",
                str(tmp_path / "somebody-elses.git"),
            ),
            check=True,
        )
    elif remote is Remote.MISSING:
        subprocess.run(
            ("git", "-C", str(clone), "remote", "remove", "origin"), check=True
        )
    if env is not None:
        (clone / ".env").write_text(env)

    declaration = tmp_path / "box.env"
    declaration.write_text("BOX_DOMAIN=box.example.invalid\n")
    record = tmp_path / "var" / "lib" / "rails49" / "deploys" / "dccex"

    saved = tmp_path / "remote.sh"
    told = tmp_path / "told"
    called = tmp_path / "called"
    executable(
        binaries / "ssh",
        "#!/usr/bin/env bash\n"
        "# The box, on this machine: the heredoc is saved rather than carried.\n"
        f'cat > "{saved}"\n',
    )
    executable(
        binaries / "docker",
        "#!/usr/bin/env bash\n"
        "# Compose, as far as what it is told and whether it comes up.\n"
        f'printf "%s\\n" "$*" > "{called}"\n'
        f'cp .env "{told}"\n'
        f'echo "{DAEMON}" >&2\n'
        f"exit {0 if comes_up else 1}\n",
    )

    reached = {
        **os.environ,
        "PATH": f"{binaries}{os.pathsep}{os.environ['PATH']}",
        "HOME": str(home),
        "DCCEX_BOX": "somebody@box.example.invalid",
        "DCCEX_STACK": "dccex",
        "DCCEX_BRANCH": "main",
    }
    subprocess.run((str(DEPLOY),), env=reached, capture_output=True, check=True)

    here = saved.read_text()
    for named, times, stands_in in (
        (DECLARATION, 1, str(declaration)),
        (RECORD, 1, str(record)),
        (ORIGIN, 3, origin),
    ):
        assert here.count(named) == times, (
            f"{named} is named {here.count(named)} times in the program the box"
            f" runs rather than {times}, and pointing it at what this machine"
            " has would run a script this module has not checked"
        )
        here = here.replace(named, stands_in)
    saved.write_text(here)

    ran = subprocess.run(
        ("bash", str(saved)),
        env=reached,
        capture_output=True,
        text=True,
        check=False,
    )
    return Box(
        clone=clone,
        record=record,
        points_at=origin,
        commit=subprocess.run(
            ("git", "-C", str(clone), "rev-parse", "HEAD"),
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip(),
        told=told.read_text() if told.exists() else None,
        called=called.read_text().strip() if called.exists() else "",
        ran=ran,
    )


def test_the_up_is_reached_and_is_told_the_commit_being_brought_up(
    tmp_path: Path,
) -> None:
    """Named first, because every claim below is about what happens around the
    `up` and a harness that never got there would make all of them true.

    It is also the reason `.env` cannot simply be written after the `up`:
    `--env-file .env` is how compose is told which commit, so the file has to
    say the new one by the time this call is made.
    """
    box = deployed(tmp_path, env=None, comes_up=True)
    assert "up -d --build --remove-orphans" in box.called
    assert box.told == f"DCCEX_COMMIT={box.commit}\n"


def test_a_failed_up_leaves_env_naming_the_commit_that_is_running(
    tmp_path: Path,
) -> None:
    """The bug (#83). What the next deploy reads off this file becomes the
    `went` of the line it appends, so a commit that was never brought up would
    be written down as the one that was replaced."""
    box = deployed(
        tmp_path,
        env=f"DCCEX_COMMIT={RUNNING}\n",
        comes_up=False,
    )
    assert box.env == f"DCCEX_COMMIT={RUNNING}\n"


def test_a_failed_up_on_a_box_that_had_no_env_leaves_none(tmp_path: Path) -> None:
    """The first deploy onto a fresh box, which has no `.env` and whose record
    says it replaced nothing. Putting it back means removing it.

    What compose was told is asserted with it, because a box with no `.env` also
    has none if the deploy stopped before writing one — which is what a
    `sed` over a file that is not there used to do under `pipefail`.
    """
    box = deployed(tmp_path, env=None, comes_up=False)
    assert box.told == f"DCCEX_COMMIT={box.commit}\n"
    assert box.env is None


def test_a_failed_up_appends_nothing_to_the_record(tmp_path: Path) -> None:
    """Which is right: nothing was replaced (ADR-0005 d.5)."""
    box = deployed(
        tmp_path,
        env=f"DCCEX_COMMIT={RUNNING}\n",
        comes_up=False,
    )
    assert box.told is not None, "the up was never reached"
    assert box.lines == []


def test_a_failed_up_exits_non_zero_and_says_what_it_put_back(tmp_path: Path) -> None:
    """The failure stays loud, and whoever ran it is told which commit the box
    is on — underneath compose's own output, which is where the reason is."""
    box = deployed(
        tmp_path,
        env=f"DCCEX_COMMIT={RUNNING}\n",
        comes_up=False,
    )
    assert box.ran.returncode != 0
    assert DAEMON in box.ran.stderr
    assert f"Put .env back to dccex:{RUNNING}" in box.ran.stderr
    assert box.commit not in box.ran.stdout


def test_a_failed_up_says_it_removed_the_env_where_there_was_none(
    tmp_path: Path,
) -> None:
    """The other sentence, because "put it back to none" would read as a box
    on no commit rather than a box that has never had one."""
    box = deployed(tmp_path, env=None, comes_up=False)
    assert "Removed .env again" in box.ran.stderr


def test_a_deploy_that_comes_up_writes_the_commit_and_appends_one_line(
    tmp_path: Path,
) -> None:
    """The happy path, unchanged (ADR-0005 d.8): `.env` names the new commit,
    one line says what went and what came, and the tail is printed."""
    box = deployed(
        tmp_path,
        env=f"DCCEX_COMMIT={RUNNING}\n",
        comes_up=True,
    )
    assert box.ran.returncode == 0
    assert box.env == f"DCCEX_COMMIT={box.commit}\n"
    assert len(box.lines) == 1
    assert box.lines[0].split()[1:] == [f"dccex:{RUNNING}", "->", f"dccex:{box.commit}"]
    assert f"deployed dccex:{box.commit}" in box.ran.stdout
    assert box.lines[0] in box.ran.stdout, "the tail of the record is not printed"


def test_a_first_deploy_that_comes_up_records_that_it_replaced_nothing(
    tmp_path: Path,
) -> None:
    """A box with no `.env`, which is the first line of a box's record (d.5)."""
    box = deployed(tmp_path, env=None, comes_up=True)
    assert box.ran.returncode == 0
    assert box.env == f"DCCEX_COMMIT={box.commit}\n"
    assert box.lines[0].split()[1:] == ["none", "->", f"dccex:{box.commit}"]


def test_a_clone_with_no_origin_is_given_one_and_the_deploy_goes_on(
    tmp_path: Path,
) -> None:
    """The bug (#119). `git remote set-url` fails on a clone with no remote
    named `origin`, and `set -e` stopped the deploy there — on git's terse
    message rather than on one of this script's own sentences, which is what
    every other guard in it is written to give.

    Nothing is wrong with such a clone, so nothing is said about it: it is
    given the origin the script names and the deploy carries on. What the `up`
    was told is asserted with the origin, because a program that stopped at the
    fetch or the fast-forward would never have reached compose and would leave
    the origin right anyway.
    """
    box = deployed(tmp_path, env=None, comes_up=True, remote=Remote.MISSING)
    assert box.ran.returncode == 0, box.ran.stderr
    assert box.origin == box.points_at
    assert box.told == f"DCCEX_COMMIT={box.commit}\n"


def test_a_clone_somebody_repointed_by_hand_ends_at_the_scripts_origin(
    tmp_path: Path,
) -> None:
    """The case the setting is there for (control#541), and the one the
    fallback above must not have taken over: an origin that is somebody else's
    is set to the script's rather than left and pulled from.

    The clone is pointed at a path that does not exist, so a deploy that
    believed it would fail at the fetch instead of quietly bringing up
    somebody else's commits.
    """
    box = deployed(tmp_path, env=None, comes_up=True, remote=Remote.REPOINTED)
    assert box.ran.returncode == 0, box.ran.stderr
    assert box.origin == box.points_at
    assert box.told == f"DCCEX_COMMIT={box.commit}\n"
