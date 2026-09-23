#!/usr/bin/env python3
"""A client of the mirror's port that reads nothing and fills its buffer.

The mirror cuts a client off once more than a megabyte is outstanding to it,
and aborts its connection rather than closing it — at the cut-off, at the
grace ending an outage, and when the app itself is going
(`docs/dccex_usb/README.md`). Every one of those is about a client that has
stopped reading, so checking any of them by hand means having one.

This is that client. It connects, sends nothing but `<s>`, never reads a byte,
and says when its receive buffer has filled — so the cutover's SIGTERM check
(#16) is driven by something repeatable rather than an `nc` reconstructed at
midnight, which is the version that accidentally reads.

It is **not in the gate.** The gate is one command on a laptop with nothing
plugged in; this wants a mirror on the other end of a socket, and with
`--prompt 0` it wants a command station behind that.

    python3 scripts/deaf_client.py --host dccex-usb --port 2560

The only bytes it sends are `<s>`, which asks the station what it is running
and changes nothing on the railroad, so it is safe to run while trains are
moving. Its receive buffer is made small on purpose: a few kilobytes fill in
seconds and the size is the same on every box, where the kernel's own
auto-tuned buffer is neither.

Once it says it is full it stops asking and holds the connection open, still
reading nothing, until it is interrupted. That is the state to take the
mirror's SIGTERM in: if the shutdown waits for this client to take what is
outstanding to it, it waits forever.

**Whether the mirror exited is watched where the mirror runs, not here.** The
abort throws away what the mirror had buffered for this client and closes the
socket; what the kernel had already sent is still in flight to a receiver that
is not taking it, and the close is at the end of that. So this end goes quiet
rather than hearing anything. It says so when it does notice the other end go,
and its silence says nothing either way.
"""

from __future__ import annotations

import argparse
import array
import fcntl
import select
import socket
import sys
import termios
import time

STATUS = b"<s>"

# Linux rounds a requested receive buffer up and doubles it, so what is asked
# for here is a floor and the size actually got is reported rather than
# assumed.
SMALL = 4096


def queued(sock: socket.socket) -> int:
    """How many bytes have arrived and not been read. Reads none of them."""
    count = array.array("i", [0])
    fcntl.ioctl(sock.fileno(), termios.FIONREAD, count, True)
    return count[0]


def gone(sock: socket.socket) -> bool:
    """Whether the other end has been noticed going, without reading a byte.

    A reset arrives as an error on the socket and a close as a read hangup.
    Neither needs the data to be taken first, but a close behind bytes this
    end is not taking is behind bytes that cannot be delivered, so it does not
    arrive at all — which is the usual case here and why this is how the tool
    notices rather than how the mirror's end is established.
    """
    poller = select.poll()
    poller.register(
        sock.fileno(),
        select.POLLERR | select.POLLHUP | getattr(select, "POLLRDHUP", 0),
    )
    return bool(poller.poll(0))


def say(line: str) -> None:
    print(line, flush=True)


def fill(sock: socket.socket, prompt: float, poll: float, still: int) -> int:
    """Let the buffer fill, reading nothing, and return what it filled with.

    Full is what a buffer that has stopped growing means: the kernel has
    stopped taking what the mirror is sending, because nothing here is taking
    what the kernel already has. Returns the number of bytes queued and
    unread, or 0 if the mirror let go first.
    """
    started = time.monotonic()
    asked = 0.0
    standing = 0
    unchanged = 0
    while True:
        if gone(sock):
            return 0
        now = time.monotonic()
        if prompt > 0 and now - asked >= prompt:
            try:
                sock.sendall(STATUS)
            except OSError as error:
                say(f"the mirror stopped taking what we send: {error}")
                return 0
            asked = now
        waiting = queued(sock)
        if waiting > standing:
            say(f"{waiting:>9} bytes queued and unread")
            standing = waiting
            unchanged = 0
        elif standing > 0:
            unchanged += 1
            if unchanged >= still:
                say(
                    f"full: {standing} bytes queued, none of them read,"
                    f" after {now - started:.1f}s"
                )
                return standing
        time.sleep(poll)


def hold(sock: socket.socket, poll: float) -> None:
    """Keep the connection open, still reading nothing, until it goes.

    Where the mirror's SIGTERM is taken: a shutdown that waited for this client
    would wait forever, so what the mirror does next is the check. It is read
    off the mirror and not off this end, for the reason in `gone`.
    """
    say("holding it open and still reading nothing — Ctrl-C to let go")
    started = time.monotonic()
    while not gone(sock):
        time.sleep(poll)
    say(f"the other end was noticed going {time.monotonic() - started:.1f}s later")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Connect to the mirror's port, read nothing, fill the buffer."
    )
    parser.add_argument("--host", default="localhost", help="default: localhost")
    parser.add_argument("--port", type=int, default=2560, help="default: 2560")
    parser.add_argument(
        "--prompt",
        type=float,
        default=0.1,
        metavar="SECONDS",
        help="how often to send <s> so there is something to fill with;"
        " 0 fills with what the railroad is already saying (default: 0.1)",
    )
    parser.add_argument(
        "--poll", type=float, default=0.2, metavar="SECONDS", help="default: 0.2"
    )
    parser.add_argument(
        "--still",
        type=int,
        default=10,
        metavar="POLLS",
        help="polls with the queue unchanged before it is called full (default: 10)",
    )
    parser.add_argument(
        "--rcvbuf",
        type=int,
        default=SMALL,
        metavar="BYTES",
        help=f"receive buffer to ask for, small so it fills fast (default: {SMALL})",
    )
    args = parser.parse_args(argv)

    sock = socket.socket()
    if args.rcvbuf > 0:
        # Before connect: a size set afterwards is a window the other end has
        # already been told about.
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, args.rcvbuf)
    try:
        sock.connect((args.host, args.port))
    except OSError as error:
        say(f"cannot reach {args.host}:{args.port}: {error}")
        return 1

    got = sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
    say(f"connected to {args.host}:{args.port}, receive buffer {got} bytes")
    if args.prompt > 0:
        say(f"asking {STATUS.decode()} every {args.prompt}s, reading nothing")
    else:
        say("sending nothing, reading nothing")

    try:
        if not fill(sock, args.prompt, args.poll, args.still):
            say("the buffer never filled: the mirror let go first")
            return 1
        hold(sock, args.poll)
    except KeyboardInterrupt:
        say("let go, having read nothing")
    finally:
        sock.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
