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
  with a box to type into. **The page is here and nothing is on it** (#3):
  `ui/` holds the band, the rail and an empty work pane, built by node inside
  its own image and served by nginx out of it, drawing in the look rules from
  its first commit. What goes in the work pane is written down
  ([the page](docs/ui/README.md)), ahead of the tickets that build it. The
  mirror's face is what it will
  talk to, on that same label under `/dccex-usb` and behind the same
  certificate ([ADR-0004](docs/adr/0004-the-face-reaches-a-browser-through-the-door-and-never-the-lan.md)):
  that face carries the releases the configured source lists, writes one onto
  the station when the page names its tag, and carries the station's
  conversation both ways on a **stream** the page opens on its own origin —
  one more client of the mirror's port and not a second mirror
  ([ADR-0007](docs/adr/0007-the-monitors-stream-is-one-more-client-of-the-mirrors-port.md)). Whether the railroad can spare
  its station is the operator's to answer: the page sequences and confirms,
  and nothing in the app checks
  ([ADR-0006](docs/adr/0006-the-operator-is-the-only-guard-on-a-flash.md)).

The words this repository uses are in [CONTEXT.md](CONTEXT.md). The gate is
`./scripts/check.sh`, one command, and it needs no hardware and no Docker
daemon. The three checks that do need one — the page's image built and served,
the compose project brought up, served and taken down, and the mirror's image
run with a pty for a device and 2560 dialled against it — carry the `docker`
marker, which the gate does not collect; `uv run pytest -m docker` is how they
are run, and the workflow runs them in a job of its own that a pull request
requires, where a missing daemon is a failure rather than a skip (#53, #54,
#56, #15).

## What the UI talks to

One thing: `dccex-usb`'s own face, on the UI's origin, behind the same door.
Not the bus and not the store — its subject is the command station rather than
a railroad. So the page is the same on a box with a command station and no
layout as it is on the layout box, which is the installation this repository
exists for
([ADR-0008](docs/adr/0008-the-page-talks-to-the-face-and-reads-the-build-off-the-banner.md)).

Every reading about the station is made of what the station said, decoded on
the page: the **build** is the `G-` field of the banner and is blank whenever
the **link** is down, and a line the **decoder** does not know is shown raw
with no gloss rather than guessed at
([ADR-0009](docs/adr/0009-the-decoder-is-a-pure-function-and-an-unknown-line-gets-no-gloss.md)).
What asks an idle station to say any of it is the page, on its own schedule,
as a throttle would — the mirror gains a face and a page and still originates
nothing
([ADR-0010](docs/adr/0010-the-page-polls-and-the-mirror-originates-nothing.md)).
Nothing on the page commands track power but the flash sequence's own step.

One origin carries both: the page takes the label and the face is the same
label under a path prefix the door strips, so the monitor's stream is `wss://`
on the page's own origin and a page from anywhere else is refused. A browser
reaches the face through the door and never the LAN, which is what
[ADR-0004](docs/adr/0004-the-face-reaches-a-browser-through-the-door-and-never-the-lan.md)
decides; 2560 goes on being published raw for JMRI and the throttles, and the
page on the stream is one of its clients like they are
([ADR-0007](docs/adr/0007-the-monitors-stream-is-one-more-client-of-the-mirrors-port.md)).

## How it gets on the box

One **image**, built from this repository's source at one commit and named by
it, which the mirror runs as and the translator will. The name never moves, so
what a box is running is a commit anybody can read off it; a deploy writes
down what it replaced, where a person on the box can `tail` it; and going back
to the one before is a command naming that commit rather than a digest
recovered by hand
([ADR-0005](docs/adr/0005-the-image-is-named-by-the-commit-it-was-built-from.md),
[the mirror's page](docs/dccex_usb/README.md)). The UI is a second image and
not that one — `deploy/ui.Dockerfile`, node to build and nginx to serve, under
the same naming rule — because a page shares neither the lock file nor the
esptool pin the Python apps do, and the box that serves it has Docker and no
node. `compose.yaml` carries that one server and its door route and nothing
else, because the one thing it has to do is come up from a clean clone. The
stack a **box** runs is that file and `compose.box.yaml` together: the mirror
beside the page, the command station's device mapped in, 2560 published raw,
the shared network the door dials containers on declared external, and the
box's own declaration required rather than defaulted, so a box the
installation has not been run on stops with a sentence naming
`/etc/rails49/box.env`. `scripts/deploy.sh` is what brings the two up there —
one ssh, a pull, a clean tree, the image built under the commit, and a line
appended to the record.

The first time that happens on the layout box it is a **cutover** and not a
deploy: 2560 is served there today by `control`'s copy of the mirror, and the
evening the port changes hands is #16, which follows
[the cutover page](docs/cutover.md) — the order, the abort signal, going back,
and the checks, written down while the old mirror is still serving.

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
