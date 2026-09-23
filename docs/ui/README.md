# The page

The UI for the command station: one page, served at `dccex.$BOX_DOMAIN` as a
label under the box's door, about the **station** at the end of the cable and
about nothing else.

**It is not built yet.** This page is written ahead of it, as
[the cutover page](../cutover.md) was written ahead of its evening, because
what it says was decided in rails49/dccex#1 and the tickets under that spec are
each a part of it. What is already here is the other end: the **mirror**'s
**face**, which is the one thing the page talks to
([the mirror's page](../dccex_usb/README.md)).

## What it talks to

One counterparty: `dccex-usb`'s face, on the page's own origin, behind the same
door ([ADR-0004](../adr/0004-the-face-reaches-a-browser-through-the-door-and-never-the-lan.md),
[ADR-0008](../adr/0008-the-page-talks-to-the-face-and-reads-the-build-off-the-banner.md)).

```
https://dccex.$BOX_DOMAIN/                     this page
https://dccex.$BOX_DOMAIN/dccex-usb/releases   what the configured source carries
https://dccex.$BOX_DOMAIN/dccex-usb/flash      write one of them onto the station
wss://dccex.$BOX_DOMAIN/dccex-usb/stream       the station's conversation, both ways
```

Not the bus and not the store. The organisation's ADR-0002 permits all three
and this page uses the third, because its subject is a command station rather
than a railroad — which is what makes it the same page on a box with a station
and no layout as on the layout box, with no branch between them. Every reading
about the station is made of what the station said on the **stream**; the one
that is not is how many **client**s are on the mirror's port, which is the
app's own business about itself.

It calls no third-party service. The releases are read by the app from its
configured source and handed on; the browser never reaches the release API
([the mirror's page](../dccex_usb/README.md#the-face)).

## What is on it

The **band** across the top, the rail down the side, and the work pane between
them. The band and the rail are LOOK.md's and do not vary between rails49 UIs.

### The band

Two readings, and no controls. Whether the station is answering — the **link**
— and whether the rails are hot.

**Nothing on this page commands track power.** `control`'s band presses ON,
STOP and OFF because `layout` checks the railroad is drained before anything
reaches the wire; this page is on no bus, so a press here would go down the
cable with nothing having checked (ADR-0008 d.5). The one caller that cuts
power is the flash sequence, which cuts it as its own step and asks the
operator first. The command box can still type `<0>`, which is what a raw
monitor is.

No emergency stop is drawn on the chrome, so the red token LOOK.md reserves for
the first UI to draw one stays unclaimed.

Below 560px the band drops the track reading and keeps the link.

### The tiles

Four readings of the station's particulars, at the top of the work pane:

| Tile | What it reads | While the link is down |
| --- | --- | --- |
| build | the `G-` field of the station's banner | blank |
| current | the milliamps on `<c …>` | blank |
| clients | how many are on the mirror's port | still read — it is the face's |
| last heard | how long ago the station last said anything | blank |

Three of the four blank together, which is correct rather than a gap: three of
them are the station talking and the station is not talking. The **build**
clears with the link and fills again by itself when the station comes back and
says which one it is running, so a build from before a flash is never reported
as the one on the board (ADR-0008 d.3).

### The releases

Every **release** the box is configured to read, newest first, each with its
publication date and whether it carries a flashable asset. The one whose
**tag** matches the build on the station now is marked as such, so being up to
date is something to see rather than to work out. The list is collapsed under
the tiles.

Choosing one flashes it, and the page sequences that itself:

1. Say plainly what is about to happen — the station resets, the rails drop,
   every throttle loses it, it takes a minute or two — and get a yes.
2. Send the emergency stop.
3. Cut track power.
4. Ask the face to write the tag.
5. Show which step is running, so a minute of silence is not a hang.

**Nothing behind the page guards this.** The mirror checks the tag, the
release, the digest, the device and whether it is already writing, and it
checks nothing about a railroad, because on a box with a command station and no
layout there is no dispatcher to ask
([ADR-0006](../adr/0006-the-operator-is-the-only-guard-on-a-flash.md)). The
sequence above is where the care lives and the operator is the guard.

**A flash that cannot start says why.** The face answers a refusal with a
status and a sentence — a tag with no release, a release with no asset or no
digest, a digest that did not match, a station that is not there, a flash
already in flight — so a bad tag never looks like a slow one. A second flash
asked for while one is running is refused and not queued.

**A flash that started is not replied to; it is observed.** The stream drops as
the device goes, the tiles blank, and when the station comes back its banner
says which build it is running. That is how the page learns the write landed,
and nothing has to be reloaded.

### The stream

The station's conversation, below the releases, with a box to type into at the
foot.

- Every line is stamped with the time it arrived.
- A line the **decoder** knows carries a **gloss** — one plain sentence beside
  it. A line it does not know is shown raw with no gloss, because a guess
  standing where a reading goes is an observation nobody made
  ([ADR-0009](../adr/0009-the-decoder-is-a-pure-function-and-an-unknown-line-gets-no-gloss.md)).
- The lines this page sent are marked differently from the lines the station
  said, so an operator can tell their own traffic from the railroad's.
- It follows the newest line while the view is at the bottom and stays put once
  it has been scrolled up, so reading back does not fight the feed. It can be
  paused, and it can be cleared.

The box at the foot sends one whole `<…>` message — buffered until complete and
written in one write, so two people on the page at once cannot interleave a
command. A command typed without the angle brackets is sent as if they were
there: `s` and `<s>` do the same thing.

**The page is what polls.** The station volunteers a banner and a `<p…>`, and
an idle one says nothing; on a box with no **translator** running, nothing else
asks. So the page asks on its own schedule, up the stream, as a throttle would
— and the mirror goes on originating nothing
([ADR-0010](../adr/0010-the-page-polls-and-the-mirror-originates-nothing.md)).

The page is one more client of the mirror's port and is subject to every rule
that port has, including being cut off once it falls too far behind and being
disconnected alongside the throttles when the device has been away past the
grace ([ADR-0007](../adr/0007-the-monitors-stream-is-one-more-client-of-the-mirrors-port.md)).

## How it looks

The look rules are the organisation's, in LOOK.md, and their values arrive here
as a verbatim copy of `tokens.css` at a fixed path with the commit it was taken
at recorded beside it — inert, read by nothing at runtime except as the
stylesheet it is. This repository's own test asserts that what the page draws
with equals that copy, so drift is caught in this gate rather than noticed
later. `control`'s `ui/look/README.md` is the shape that follows.

It takes the system's light or dark setting and offers no toggle, as the other
rails49 UIs do, and it works at the width of a phone held at the layout.

## How it is built and served

A multi-stage image: node to build the sources, nginx to serve what came out.
The box needs Docker and nothing else — no node toolchain on a machine whose
job is a command station. The compose project declares the server and its door
route as labels on its own containers, and no image is published anywhere: the
box clones and builds (#15,
[ADR-0005](../adr/0005-the-image-is-named-by-the-commit-it-was-built-from.md)).

**It serves with no `control` clone present.** That is the installation this
repository exists for, and it is the first thing the first ticket proves.

## What is not on it

- **Anything about a railroad.** No turnout names, no roster, no run state —
  none of them is a thing a command station says. Somebody wanting them wants
  `control`'s UI, which is next door on the layout box.
- **Commanding track power**, beyond the flash sequence's own step.
- **Station configuration.** There is none at runtime: the fork sets
  `DISABLE_EEPROM` so the station persists nothing, the translator drives
  points with raw accessory packets so the station holds no definitions, and
  `config.rails49.h` is compile-time and changed by flashing a build. What is
  left is `<D …>` and track mode, which the command box types.
- **Scripting.** EX-RAIL is not compiled into this fork's firmware and nothing
  on this railroad scripts anything.
- **Authentication.** The LAN is the trust boundary, as everywhere else
  (control ADR-0042).

## What is still open

Two things the prototype left open and the tickets settle while building:

- whether the release list stays a collapsed row once it grows past four
  entries;
- narrow widths were never confirmed in a browser. The rules are written — the
  band drops the track reading below 560px and the release rows wrap — and
  nobody has held a phone up to them.

What each tile reads while the link is down was the third and is settled above,
by ADR-0008 d.3.
