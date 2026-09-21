# dccex

The dcc-ex project: the UI for the command station, and the two processes that
talk to it.

`CommandStation-EX` is the firmware, a fork of upstream DCC-EX's. This is ours.

## What is here

Nothing yet but this file. The repository was stood up on 2026-09-21 for the
effort that moves `src/tc49/dccex` and `src/tc49/dccex_usb` out of `control`
and writes the UI on top of them.

What arrives, in order:

- **`dccex-usb`**, the process that holds the serial device. It opens the cable
  and mirrors it on TCP 2560, so the translator, JMRI and hand-held throttles
  are all clients of the port and coexist. It is also the only thing that can
  write firmware onto the station, because writing flash means owning the port.
- **`dccex`**, the translator. It turns the layout interface's desired values
  into the station's `<…>` bytes and reports what it hears back on the bus.
- **The UI**, served at `dccex.$BOX_DOMAIN` as a label under the box's door. It
  lists the firmware releases, flashes one, and shows the serial conversation
  with a box to type into.

## What the UI talks to

One thing: `dccex-usb`'s own face, on the UI's origin, behind the same door.
Not the bus and not the store — its subject is the command station rather than
a railroad. So the page is the same on a box with a command station and no
layout as it is on the layout box, which is the installation this repository
exists for.

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
