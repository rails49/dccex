"""`python -m dccex_usb` — the command line the container runs.

The device to open and the port to serve it on are the mirror's own two flags
and the whole of what it was for a while (ADR-0043). What the third is for is
the one thing this app does that is not mirroring: writing a released build
onto the command station, which only the process holding the device can do
(ADR-0065, `firmware.py`). There is still no bind address, because the server
binds every interface and what limits its reach is the LAN (ADR-0042).

- `--device <path>`, the serial device to open.
- `--port <n>`, the TCP port to mirror it on.
- `--firmware-releases <url>`, where releases are read from, defaulting to
  this installation's fork. **Configuration and never payload**: the LAN
  carries no authentication on purpose, so a source on the wire would let
  anyone on the wifi run an arbitrary binary on the command station.

**There is no broker and no identity.** Both went with the bus (ADR-0001):
the flash was asked for on a bus in `control` and will be asked for on this
app's own face, and a name to key a refusal row by is a name for a row that no
longer exists. What is left is an app that dials nothing and answers nothing
but its own port — which is what lets a command station be mirrored on a box
with nothing else running.

**asyncio owns this process.** The mirror is a loop, the flash runs on it, and
the loop here is what carries a mirror that ended out to the exit status.
"""

import argparse
import asyncio
import contextlib
import signal
import threading

from dccex_usb.firmware import RELEASES, Flasher
from dccex_usb.station import Station, to_stderr

PERIOD_S = 0.5
"""How often the loop looks at `stop`. It waits on the mirror the rest of the
time, so this is the lag between a caller that is not a signal asking for the
end and the process taking it — and the deployment's way out is a signal,
which needs no turn of the loop at all."""


def serve(
    device: str,
    port: int,
    stop: threading.Event,
    releases: str = RELEASES,
    period_s: float = PERIOD_S,
) -> None:
    """The app: the mirror, and the flasher on the device it holds.

    `stop` is how a caller that is not a signal ends the loop, which is the
    suite. The deployment sets it never: a signal raises where the process
    happens to be, and `main` lets that out. So does a mirror that cannot
    serve — the port is taken, and this comes back raising rather than
    staying up with nothing behind it (#526).
    """
    station = Station(device, port)
    flasher = Flasher(station, releases)
    to_stderr(f"serving {device} on {port}, flashing from {releases}")
    asyncio.run(mirroring(station, flasher, stop, period_s))


async def mirroring(
    station: Station,
    flasher: Flasher,
    stop: threading.Event,
    period_s: float,
) -> None:
    """The mirror on a task of its own, until the process ends.

    **The mirror ending ends this**, which is why the loop waits on the task
    rather than on the clock alone: a port already taken raises out of the
    mirror, and a loop that went round anyway would leave a live process with
    no TCP server, no device and nothing said (#526). The failure is what the
    teardown's `await` carries out, so it reaches `main` and the exit status
    and `restart: unless-stopped` gets its turn — which is what a box whose
    2560 is busy for a moment during a deploy depends on.

    A flash in flight is waited out where there is still a loop to wait on:
    the mirror gives the device back when the flash is done with it, and
    ending in the middle of one leaves the station half written. A signal
    arriving mid-flash is not something this can hold off — the cancellation
    it raises is what ends the wait — and neither is the container's kill.
    """
    mirror = asyncio.create_task(station.run())
    try:
        while not stop.is_set() and not mirror.done():
            await asyncio.wait((mirror,), timeout=period_s)
    finally:
        with contextlib.suppress(asyncio.CancelledError):
            await flasher.settled()
        mirror.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await mirror


def command_line() -> argparse.ArgumentParser:
    """The three flags, which are the whole of the configuration."""
    parser = argparse.ArgumentParser(
        prog="python -m dccex_usb",
        description="Mirror the command station's serial device on a TCP port,"
        " and write a released firmware build onto it when asked.",
    )
    parser.add_argument("--device", required=True, help="the serial device to open")
    parser.add_argument("--port", type=int, required=True, help="the TCP port to serve")
    parser.add_argument(
        "--firmware-releases",
        default=RELEASES,
        metavar="URL",
        help="where releases are read from, this installation's fork by"
        " default; never taken from a payload",
    )
    return parser


def main() -> None:
    args = command_line().parse_args()
    # A signal is what ends this app, and SIGTERM is the one a container is
    # stopped with: given SIGINT's own handler it raises where the process
    # stands, and the mirror lets the device go on the way out either way.
    signal.signal(signal.SIGTERM, signal.default_int_handler)
    with contextlib.suppress(KeyboardInterrupt):
        serve(args.device, args.port, threading.Event(), args.firmware_releases)


if __name__ == "__main__":
    main()
