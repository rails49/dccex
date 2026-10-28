"""The log: what the process writes to stdout and stderr, copied to a file
(#364).

What is here is the copy and the file: that a line reaches both the stream
and the file, stamped and flushed, and what a trim keeps. The lines the
process writes are `test_main.py`'s and `test_translator.py`'s.
"""

import io
import logging
import sys
from pathlib import Path
from typing import IO

import pytest

from dccex.__main__ import started
from dccex.log import Log, Tee, teed

AT = "2026-10-28T19:38:30.123+00:00"


class FullFile(io.TextIOWrapper):
    def write(self, s: str) -> int:
        raise OSError(28, "No space left on device")


class FullLog(Log):
    """A log on a disk with no space left."""

    def _opened(self) -> IO[str]:
        return FullFile(self._path.open("ab"), encoding="utf-8")


def test_a_line_reaches_the_stream_unchanged_and_the_file_stamped(
    tmp_path: Path,
) -> None:
    """What reaches `docker logs` does not change."""
    path = tmp_path / "log.txt"
    stream = io.StringIO()
    tee = Tee(stream, Log(path, at=lambda: AT))
    print("dccex: up", file=tee)
    assert stream.getvalue() == "dccex: up\n"
    assert path.read_text() == f"{AT} dccex: up\n"


def test_a_line_is_held_until_its_newline_arrives(tmp_path: Path) -> None:
    """`print` writes the text and the newline in two calls, and a traceback
    arrives in pieces: the file gets the line whole."""
    path = tmp_path / "log.txt"
    tee = Tee(io.StringIO(), Log(path, at=lambda: AT))
    tee.write("Traceback ")
    assert path.read_text() == ""
    tee.write("(most recent call last):\n  File")
    tee.write(' "x.py"\n')
    assert path.read_text().splitlines() == [
        f"{AT} Traceback (most recent call last):",
        f'{AT}   File "x.py"',
    ]


def test_every_line_is_on_the_disk_as_it_is_written(tmp_path: Path) -> None:
    path = tmp_path / "log.txt"
    log = Log(path, at=lambda: AT)
    for n in range(3):
        log.wrote(str(n))
        assert path.read_text().splitlines()[-1] == f"{AT} {n}"


def test_a_log_opened_on_a_file_that_is_there_appends_to_it(tmp_path: Path) -> None:
    """The file survives the process: the traceback from before a restart is
    often the one wanted."""
    path = tmp_path / "log.txt"
    path.write_text("before dccex: the script changed\n")
    Log(path, at=lambda: AT).wrote("dccex: starting")
    assert path.read_text().splitlines() == [
        "before dccex: the script changed",
        f"{AT} dccex: starting",
    ]


def test_a_file_over_its_size_keeps_its_newest_whole_lines(tmp_path: Path) -> None:
    path = tmp_path / "log.txt"
    log = Log(path, at=lambda: AT, above=500, to=400)
    for n in range(40):
        log.wrote(f"line {n}")
    assert path.stat().st_size <= 500
    kept = path.read_text().splitlines()
    assert kept == [f"{AT} line {n}" for n in range(40 - len(kept), 40)]
    assert not (tmp_path / "log.txt.trimmed").exists()


def test_a_file_over_its_size_is_trimmed_when_it_is_opened(tmp_path: Path) -> None:
    path = tmp_path / "log.txt"
    path.write_text("".join(f"old {n}\n" for n in range(100)))
    Log(path, at=lambda: AT, above=500, to=400)
    kept = path.read_text().splitlines()
    assert path.stat().st_size <= 400
    assert kept[-1] == "old 99"
    assert all(line.startswith("old ") for line in kept)


def test_a_log_that_cannot_be_written_is_said_once_on_the_stream(
    tmp_path: Path,
) -> None:
    path = tmp_path / "log.txt"
    stream = io.StringIO()
    tee = Tee(stream, FullLog(path, at=lambda: AT))
    print("dccex: up", file=tee)
    print("dccex: still up", file=tee)
    assert stream.getvalue().splitlines() == [
        "dccex: up",
        (
            f"dccex: the log file at {path} cannot be written:"
            " [Errno 28] No space left on device"
        ),
        "dccex: still up",
    ]


def test_a_trim_that_fails_leaves_the_caller_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unreadable(self: Path) -> bytes:
        raise OSError(5, "Input/output error")

    stream = io.StringIO()
    tee = Tee(stream, Log(tmp_path / "log.txt", at=lambda: AT, above=0, to=0))
    monkeypatch.setattr(Path, "read_bytes", unreadable)
    print("dccex: up", file=tee)
    assert stream.getvalue().startswith("dccex: up\n")


def test_a_file_that_cannot_be_opened_again_after_a_trim_leaves_the_caller_alone(
    tmp_path: Path,
) -> None:
    class Unopenable(Log):
        opened = 0

        def _opened(self) -> IO[str]:
            self.opened += 1
            if self.opened > 1:
                raise OSError(24, "Too many open files")
            return super()._opened()

    stream = io.StringIO()
    tee = Tee(stream, Unopenable(tmp_path / "log.txt", at=lambda: AT, above=0, to=0))
    print("dccex: up", file=tee)
    print("dccex: still up", file=tee)
    assert stream.getvalue().splitlines()[-1] == "dccex: still up"


def test_the_streams_teed_carry_print_logging_and_an_uncaught_exception(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Everything that reaches stdout or stderr: a `print`, a logged warning
    through the handler of last resort, and the hook that writes a traceback
    as the process dies."""
    monkeypatch.setattr(sys, "stdout", io.StringIO())
    monkeypatch.setattr(sys, "stderr", io.StringIO())
    path = tmp_path / "log.txt"
    teed(Log(path, at=lambda: AT))
    print("a script's print")
    monkeypatch.setattr(logging.getLogger(), "handlers", [])
    logging.getLogger("dccex.translator").warning("the link to the station is down")
    try:
        raise RuntimeError("the handler raised")
    except RuntimeError as raised:
        sys.excepthook(RuntimeError, raised, raised.__traceback__)
    said = path.read_text()
    assert f"{AT} a script's print\n" in said
    assert f"{AT} the link to the station is down\n" in said
    assert f"{AT} Traceback (most recent call last):\n" in said
    assert f"{AT} RuntimeError: the handler raised\n" in said


def test_the_first_line_says_the_process_is_starting_and_what_it_was_built_from(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """After the old run's last lines, so the file shows where one run ends
    and the next begins."""
    stderr = io.StringIO()
    monkeypatch.setattr(sys, "stdout", io.StringIO())
    monkeypatch.setattr(sys, "stderr", stderr)
    path = tmp_path / "log.txt"
    path.write_text(
        f"{AT} dccex: the script changed: the railroad is down and this"
        " process is ending\n"
    )
    started(str(path), "d97a0bc")
    said = path.read_text().splitlines()
    assert said[0].endswith(
        "the script changed: the railroad is down and this" " process is ending"
    )
    assert said[1].endswith(" dccex: starting, built from d97a0bc")
    assert len(said) == 2
    assert stderr.getvalue() == "dccex: starting, built from d97a0bc\n"


def test_with_no_log_the_start_line_reaches_stderr_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stderr = io.StringIO()
    monkeypatch.setattr(sys, "stderr", stderr)
    started(None, "")
    assert sys.stderr is stderr
    assert stderr.getvalue() == "dccex: starting, built from an unrecorded commit\n"
