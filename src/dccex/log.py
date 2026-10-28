"""The log: what this process writes to stdout and stderr, kept in a file the
mirror's face serves (#364, `docs/dccex/README.md`).

`docker logs` is where the log has always gone, and it still does: `Tee`
writes each line to the stream it replaces first and to the file after. What
reaches the file is everything that reaches either stream — this app's own
`dccex:` lines, `lib`'s `mqtt:` lines, a logged warning or traceback, a
script's `print`, and the traceback of an exception nothing caught.

Each line is stamped with when it was written and flushed as it is written.
The file is appended to, so a process that comes back up adds to the log the
one before it ended.

**Nothing clears it, and it is kept to a size.** Above `TRIMMED_ABOVE` bytes
the oldest lines go, down to the newest `TRIMMED_TO` bytes at a line
boundary. The trim is written beside the file and renamed over it, as the
journal's is (`journal.py`), so the face serves the old file or the new one.

A file that cannot be written or trimmed does not stop the stream: the
line still reaches `docker logs`, and the first failure is said there once.
"""

import io
import os
import sys
import threading
from pathlib import Path
from typing import IO, TextIO, cast

from dccex.journal import Stamp, arrived

TRIMMED_ABOVE = 1_000_000
"""The log's size in bytes above which its oldest lines go."""

TRIMMED_TO = 800_000
"""The most bytes of newest lines a trim keeps."""


class Log:
    """The file the process's lines are appended to, open for as long as the
    process runs.

    Locked, because `lib`'s network thread writes to stderr beside the loop's
    thread.
    """

    def __init__(
        self,
        path: str | Path,
        *,
        at: Stamp = arrived,
        above: int = TRIMMED_ABOVE,
        to: int = TRIMMED_TO,
    ) -> None:
        self._path = Path(path)
        self._at = at
        self._above = above
        self._to = to
        self._lock = threading.Lock()
        self._file = self._opened()
        self._trimmed()
        self.failed = False
        """Whether a write or a trim has failed, which is said once."""

    @property
    def path(self) -> Path:
        return self._path

    def _opened(self) -> IO[str]:
        # Open until the next trim or the end of the process.
        return self._path.open("a", encoding="utf-8")

    def _trimmed(self) -> None:
        """The oldest lines gone where the file is over its size."""
        if os.fstat(self._file.fileno()).st_size <= self._above:
            return
        whole = self._path.read_bytes()
        cut = whole.find(b"\n", len(whole) - self._to - 1) + 1
        trimmed = self._path.with_name(self._path.name + ".trimmed")
        trimmed.write_bytes(whole[cut:])
        trimmed.replace(self._path)
        self._file.close()
        self._file = self._opened()

    def wrote(self, line: str) -> None:
        """One line, stamped and on the disk before this returns."""
        with self._lock:
            self._file.write(f"{self._at()} {line}\n")
            self._file.flush()
            self._trimmed()


class Tee(io.TextIOBase):
    """A stream that writes what it is given to the stream it replaces and to
    the log, a whole line at a time.

    The part of a line not yet ended is held until its newline arrives:
    `print` writes the text and the newline in two calls.
    """

    def __init__(self, stream: TextIO, log: Log) -> None:
        super().__init__()
        self._stream = stream
        self._log = log
        self._held = ""

    def write(self, s: str) -> int:
        self._stream.write(s)
        *ended, self._held = (self._held + s).split("\n")
        for line in ended:
            try:
                self._log.wrote(line)
            except OSError as error:
                if not self._log.failed:
                    self._log.failed = True
                    self._stream.write(
                        f"dccex: the log at {self._log.path} cannot be written:"
                        f" {error}\n"
                    )
        return len(s)

    def flush(self) -> None:
        self._stream.flush()

    def writable(self) -> bool:
        return True

    def fileno(self) -> int:
        return self._stream.fileno()

    def isatty(self) -> bool:
        return self._stream.isatty()

    @property
    def encoding(self) -> str:  # type: ignore[override]
        return self._stream.encoding


def teed(log: Log) -> None:
    """stdout and stderr written to `log` as well, for the rest of the
    process.

    Never undone: the traceback of an exception nothing caught is written
    after every `finally` has run.
    """
    sys.stdout = cast(TextIO, Tee(sys.stdout, log))
    sys.stderr = cast(TextIO, Tee(sys.stderr, log))
