# dccex

The dcc-ex project: the UI for the command station, and the two processes that
talk to it.

`CommandStation-EX` is the firmware, a fork of upstream DCC-EX's. This is ours.

## What is here

The repository was stood up on 2026-09-21 for the effort that moves
`src/tc49/dccex` and `src/tc49/dccex_usb` out of `control` and writes the UI on
top of them.

- **`dccex-usb`**, the mirror: the process that holds the serial device. It
  opens the cable and mirrors it on TCP 2560, so the translator, JMRI and
  hand-held throttles are all clients of the port and coexist. It is also the
  only thing that can write firmware onto the station, because writing flash
  means owning the port. **It is here** — `src/dccex_usb`, copied out of
  `control`, off the bus and answering on its own face
  ([the page](docs/dccex_usb/README.md),
  [ADR-0001](docs/adr/0001-the-mirror-leaves-the-bus-for-a-face.md),
  [SOURCE.md](src/SOURCE.md)).
- **`dccex`**, the translator. It turns the layout interface's desired values
  into the station's `<…>` bytes and reports what it hears back on the bus.
  Not here yet.
- **The UI**, served at `dccex.$BOX_DOMAIN` as a label under the box's door. It
  lists the firmware releases, flashes one, and shows the serial conversation
  with a box to type into. Not here yet. The mirror's face is what it will
  talk to, on that same label under `/dccex-usb` and behind the same
  certificate ([ADR-0004](docs/adr/0004-the-face-reaches-a-browser-through-the-door-and-never-the-lan.md)):
  that face carries the releases the configured source lists already, and
  asking for a flash is still to come.

The words this repository uses are in [CONTEXT.md](CONTEXT.md). The gate is
`./scripts/check.sh`, one command, and it needs no hardware.

## What the UI talks to

One thing: `dccex-usb`'s own face, on the UI's origin, behind the same door.
Not the bus and not the store — its subject is the command station rather than
a railroad. So the page is the same on a box with a command station and no
layout as it is on the layout box, which is the installation this repository
exists for.

One origin carries both: the page takes the label and the face is the same
label under a path prefix the door strips, so the monitor's stream is `wss://`
on the page's own origin and a page from anywhere else is refused. A browser
reaches the face through the door and never the LAN, which is what
[ADR-0004](docs/adr/0004-the-face-reaches-a-browser-through-the-door-and-never-the-lan.md)
decides; 2560 goes on being published raw for JMRI and the throttles.

## How it gets on the box

One **image**, built from this repository's source at one commit and named by
it, which the mirror runs as and the translator will. The name never moves, so
what a box is running is a commit anybody can read off it; a deploy writes
down what it replaced, where a person on the box can `tail` it; and going back
to the one before is a command naming that commit rather than a digest
recovered by hand
([ADR-0005](docs/adr/0005-the-image-is-named-by-the-commit-it-was-built-from.md),
[the mirror's page](docs/dccex_usb/README.md)). The stack that builds it and
the deploy that runs it are not here yet — they are #15's, built in that
shape.

## Licence

MIT. The Python moves in from `control` unchanged, and the firmware's GPLv3
stays in `CommandStation-EX` where it belongs.

## The decisions

- [ADR-0008](https://github.com/rails49/.github/blob/main/docs/adr/0008-the-dcc-ex-ui-and-its-python-share-a-repository-of-their-own.md) —
  why this repository exists and what builds it
- [ADR-0002](https://github.com/rails49/.github/blob/main/docs/adr/0002-a-ui-talks-to-the-bus-the-store-and-its-own-apps-face.md) —
  what a UI may talk to, and what a private face is
- [ADR-0001](https://github.com/rails49/.github/blob/main/docs/adr/0001-a-ui-of-its-own-is-about-something-other-than-the-loaded-railroad.md) —
  why this is a UI of its own and not a view of `control`'s
- [control ADR-0065](https://github.com/rails49/control/blob/main/docs/adr/0065-the-app-that-owns-the-device-flashes-it.md)
  and [ADR-0066](https://github.com/rails49/control/blob/main/docs/adr/0066-the-link-is-the-station-answering-not-the-socket-being-open.md) —
  flashing, and what the link means
