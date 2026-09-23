# ADR-0001 — the mirror leaves the bus for a face

- **Status:** accepted, 2026-09-22
- **Ticket:** rails49/dccex#11, under #10
- **Related:** [ADR-0008](https://github.com/rails49/.github/blob/main/docs/adr/0008-the-dcc-ex-ui-and-its-python-share-a-repository-of-their-own.md)
  (why this repository exists),
  [ADR-0002](https://github.com/rails49/.github/blob/main/docs/adr/0002-a-ui-talks-to-the-bus-the-store-and-its-own-apps-face.md)
  (what a UI may talk to, and what a private face is),
  [control ADR-0065](https://github.com/rails49/control/blob/main/docs/adr/0065-the-app-that-owns-the-device-flashes-it.md)
  (the app that owns the device flashes it),
  [control ADR-0066](https://github.com/rails49/control/blob/main/docs/adr/0066-the-link-is-the-station-answering-not-the-socket-being-open.md)
  (what the link means)

## Context

In `control`, the mirror was an app on the bus. It was started with a broker
and an identity, it subscribed to `tc49/layout/firmware_wanted`, and when it
turned a flash down it published a row on
`tc49/layout/state/device/refused/<id>`. That was right there: everything in
`control` is about a railroad, and the bus is how things about a railroad
reach each other.

Here the subject is different. The mirror holds a cable to a command station.
A station is not a fact about a railroad — a box with a station and no layout
has one, and the layout box has exactly the same one. Nothing on the bus is
waiting to hear about it, and nothing on the bus should have to be running for
a cable to be mirrored. ADR-0002 already names what an app with its own
subject gets instead: a face, on the UI's origin, behind the same door.

The mirror also flashes, because writing flash means owning the port
(ADR-0065), and that was the one thing the bus was actually being used for.

## Decision

**d.1** The mirror is started with a serial device and a port. There is no
broker argument and no identity argument, and nothing in the package dials
anything or answers anything but its own port.

**d.2** The subscription goes, and so does the row published when a flash was
turned down. A refusal is logged and goes nowhere else: there is no railroad
here to tell, and until the face is there, nobody asked in a way that can be
answered.

**d.3** The flash stays, in the app that holds the device, because the port is
still what it needs. Everything under the six-step ordering stays with it —
resolving a release, checking its digest, the esptool command line — and what
fetches a URL and what runs a command stay injected *with the real
implementations as their defaults*, so the suite substitutes fakes and the
deployment substitutes nothing. That is what keeps the package on the standard
library with the flasher as its one dependency.

**d.4** What reaches the flash is this app's own face, and only that. Not the
bus, not a second port, not a command-line option. Until the face is written
(#12) the flash path has no caller at all — an app that can only be told
things by a face it does not have yet is expected to be quiet, not broken.

**d.5** The code lands under its own package name, `dccex_usb`, rather than
`control`'s namespace. With the bus gone there is nothing of `control`'s here
to share a namespace with.

**d.6** It lands as a copy and says so. `control`'s file names are kept and the
commit it was taken at is written down beside it ([SOURCE.md](../../src/SOURCE.md)),
so the next person can diff the two and see only the bus coming out. The way
the mirror behaves is not up for reconsideration here: the backoff, the grace,
the outstanding-bytes cut-off and the handover are what they were, down to
their numbers.

> **Amended 2026-09-22 (#23, [ADR-0003](0003-the-copy-has-no-original-left-and-is-fixed-here.md)):**
> one of those behaviours has moved, which this says at the time rather than
> leaving d.6 to read as though nothing did. A client's connection is now
> aborted wherever it is dropped — shutting down, and when the grace ends an
> outage, as it already was when the client fell too far behind — because
> closing it waits for a write buffer that a client which has stopped reading
> never drains, and that wait hung the shutdown and held the device. What is
> lost with the abort is bytes that client was not taking. The numbers are
> untouched: the backoff, the grace and the outstanding-bytes bound are what
> they were.

> **Amended 2026-09-22 (#24, [ADR-0003](0003-the-copy-has-no-original-left-and-is-fixed-here.md)):**
> and a second, on the handover itself. A client's message already being
> written when the device is let go is dropped now, where it used to wait for
> ever: closing the descriptor dropped it from the selector without waking
> what was parked on it, so that write kept the write lock and every message
> from every client queued behind it — the mirror stopped forwarding to the
> station, silently, until the process was restarted. The descriptor comes
> off the loop and the parked write is woken before it is closed, in that
> order, so nothing is written to and nothing unregistered from a descriptor
> number the OS may have handed on. What is lost is the tail of one message
> that was going into an outage, which is where the rest of that message was
> going anyway. The numbers are untouched again.

> **Amended 2026-09-22 (#26, [ADR-0003](0003-the-copy-has-no-original-left-and-is-fixed-here.md)):**
> and a third, on the handover again — this time on how it ends. A handover
> that finishes on a station which has been closed meanwhile no longer takes
> the device back: it used to start a fresh watcher whatever had become of the
> station, which reopens and holds the cable of a mirror nobody is using. That
> is reachable on a signal mid-flash, where the flash is shielded from the
> cancellation and the mirror is closed under it. What stopped it being a held
> device was the event loop's task cleanup happening to cancel that watcher,
> which is not a statement anything made; the station says it has been closed
> now, and the handover asks. Nothing a client can see changes, and the numbers
> are untouched once more.

> **Amended 2026-09-22 (#34, [ADR-0003](0003-the-copy-has-no-original-left-and-is-fixed-here.md)):**
> and a fourth, which is the #24 amendment above being held to what it claimed.
> It said nothing is written to or unregistered from a number the OS may have
> handed on. That was true of a write woken by the teardown and not of one the
> selector had already woken: waking does not resume a write, so a device found
> with room moments before it was let go left a write that took the number for
> its own. It is decided by the device now and not by the wake — the open
> device is an object that holds the descriptor, and what is parked on it asks
> whether the number is still the device's, however it came to be woken. What a
> client can see is unchanged, the two behaviours above stand as amended, and
> the numbers are untouched a fourth time.

**d.7** The words go with it. `station` here is the command station, which is
the opposite of `control`'s reservation for the same word, and
[CONTEXT.md](../../CONTEXT.md) is where that is written down rather than in a
docstring somebody has to find.

## Consequences

- The mirror runs on a box with no broker, and a station can be watched and
  typed at with nothing else up. That is also what makes it testable against a
  pty: there is nothing to stand up.
- Nothing can ask for a flash between this ticket and the face. Anything that
  wants to be able to is asking for #12.
- The reason a flash was turned down has nowhere to go but the log, and after
  #12 the face's answer to whoever asked. There is no row about it, and no
  railroad hears about it.
- The translator is a client of the mirror's port like JMRI and the throttles
  are. It keeps its own place on the bus, because what it is about — desired
  values on a layout — is a railroad's business. The mirror's is not.
