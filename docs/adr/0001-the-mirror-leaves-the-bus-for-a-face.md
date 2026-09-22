# ADR-0001 — the mirror leaves the bus for a face

**Amended by
[ADR-0003](0003-the-copy-has-no-source-and-station-py-is-ours.md),
2026-09-22:** d.6 below is half retired. The code did land as a copy and this
is still where it came from, but `control` deleted its side, so there is
nothing to stay diffable against and the numbers d.6 pinned are ordinary code
now. Everything else here stands.

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
