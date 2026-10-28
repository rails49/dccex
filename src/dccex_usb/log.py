"""The translator's **log** the face serves, which the translator writes
(#364, `dccex.log`).

The translator copies what it writes to stdout and stderr to a file on the
journal's volume, each line stamped, and trims it itself. This app mounts the
volume read-only and hands the bytes over as they are. A log that is not there
is no bytes. The file is opened by name on every read, so a trim, which the
translator renames over it, is served whole.
"""

import asyncio
from pathlib import Path


class Log:
    """The file the translator's log is copied to, served.

    Constructed with the path, which is `--log` on this app's command line.
    Nothing is opened until a caller asks.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    @property
    def where(self) -> str:
        """The path, for the sentence an answer carries where the file could
        not be read."""
        return str(self._path)

    async def served(self) -> bytes:
        """The file as it is, and no bytes where there is no file."""
        return await asyncio.to_thread(self._read)

    def _read(self) -> bytes:
        try:
            return self._path.read_bytes()
        except FileNotFoundError:
            return b""
