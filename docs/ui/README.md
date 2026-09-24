# The page

The UI for the command station: one page, served at `dccex.$BOX_DOMAIN` as a
label under the box's door, about the **station** at the end of the cable and
about nothing else.

**The page is here, the monitor is a full client of the mirror, and the page
says what the station is doing.** `ui/` holds the band, the rail and the work
pane, built and served the way this page says (#3) — which is the tracer
bullet, and it is the installation everything below rests on. What is in the
work pane is the **tile**s and the **monitor**, both halves of the monitor: the
station's conversation as it arrives, every line stamped with the time it
arrived, newest at the bottom (#4), and a box at the foot that types a whole
`<…>` message back (#6). The band carries its two readings and the tiles carry
the particulars, all of them made of what the station said and kept live by the
page's own polling (#7). The rest of the work pane — the releases — is still
written ahead of itself, as
[the cutover page](../cutover.md) was written ahead of its evening, because
what it says was decided in rails49/dccex#1 and the tickets under that spec are
each a part of it. What is already here besides is the other end: the
**mirror**'s **face**, which is the one thing the page talks to
([the mirror's page](../dccex_usb/README.md)).

## What it talks to

One counterparty: `dccex-usb`'s face, on the page's own origin, behind the same
door ([ADR-0004](../adr/0004-the-face-reaches-a-browser-through-the-door-and-never-the-lan.md),
[ADR-0008](../adr/0008-the-page-talks-to-the-face-and-reads-the-build-off-the-banner.md)).

```
https://dccex.$BOX_DOMAIN/                     this page
https://dccex.$BOX_DOMAIN/dccex-usb/releases   what the configured source carries
https://dccex.$BOX_DOMAIN/dccex-usb/flash      write one of them onto the station
https://dccex.$BOX_DOMAIN/dccex-usb/clients    how many are on the mirror's port
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

Two readings, and no controls (#7). Whether the station is answering — the
**link** — and whether the rails are hot: `link answering` and `rails hot`, or
`link not answering` and `rails unknown`, in the band's own ink. **The link
says so when the station stops answering**, rather than leaving the page
looking merely idle, which is the difference between a dead station and a quiet
one and the reason any of this exists. The rails go to `unknown` with it: what
the station last said about power is not a reading once it has stopped
talking.

**Nothing on this page commands track power.** `control`'s band presses ON,
STOP and OFF because `layout` checks the railroad is drained before anything
reaches the wire; this page is on no bus, so a press here would go down the
cable with nothing having checked (ADR-0008 d.5). The one caller that cuts
power is the flash sequence, which cuts it as its own step and asks the
operator first. The command box can still type `<0>`, which is what a raw
monitor is.

No emergency stop is drawn on the chrome, so the red token LOOK.md reserves for
the first UI to draw one stays unclaimed.

Below 560px the band drops the track reading and keeps the link. A station
that is not answering makes the other reading meaningless, and a band that kept
the rails instead would show a power state nothing has confirmed since the link
went. 560px is this page's own number rather than a look rule, written in
`dccex-band.styles.ts` beside the rule it is about.

### The tiles

Four readings of the station's particulars, at the top of the work pane (#7):

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
as the one on the board (ADR-0008 d.3). A blank tile keeps its height — three
of them blanking at once is exactly when somebody is looking, and a row that
collapsed as it happened would move the monitor under their thumb.

The count of clients is the one reading that is not the station talking, and a
face that could not be asked says nothing rather than nobody: `0` is what the
face answers when the port is empty, and a page drawing `0` for an app it could
not reach would be reporting an empty port nobody saw.

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
status and a sentence — a tag with no release, a source that could not be asked
about it at all or answered with something that is not a release, a release
with no asset or no digest, a digest that did not match, a station that is not
there, a flash already in flight — so a bad tag never looks like a slow one,
and a source that is away never looks like a bad tag: what the operator is told
is that the releases could not be read, and not to go and retype a tag that is
perfectly good (#46). A second flash asked for while one is running is refused
and not queued.

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

**What is built of it is the reading** (#4). The page opens the stream on its
own origin — the page's own address with the scheme swapped, under the prefix
the door strips (ADR-0004 d.2, d.3) — cuts what arrives at the newlines the
station writes, and shows each line stamped with the time it arrived. Four
things about that are the page's own and are decided here rather than in an
ADR, because none of them is about anything but how much of a conversation a
browser can hold:

- the bytes are read one byte to one character and never as UTF-8: a serial
  line promises no UTF-8, which is why they ride as binary frames at all, and a
  replacement character drawn on the page is a byte the page threw away
  (ADR-0007 d.5);
- a line the stream was cut off in the middle of is shown as far as it got —
  those bytes arrived, and the newline that would have finished them never
  will;
- the last two thousand lines are kept and the oldest are dropped. A monitor is
  what the station is saying now, and there is no history behind it to scroll
  into: the mirror keeps none (ADR-0010);
- a stream that closed is opened again after two seconds, because everything
  that ends one is something that ends — the cut-off, an outage past its grace,
  the app restarting (ADR-0007 d.2). Nothing is asked for on the new one and
  nothing is replayed on it, so what the station said while it was away is not
  in it.

**And what the page understood is beside it** (#5). A line the **decoder**
recognises whole carries one plain sentence, drawn quieter and smaller than the
bytes and in the page's own face rather than the monospace the station's words
are in; a line it does not recognise carries nothing at all. Five letters are
known so far — the banner the station comes up with, track power, a turnout
thrown or closed, the current on a track, and a command the station would not
take — and what it knows grows by adding a reader and a pair of strings
(ADR-0009 d.5). The component knows no protocol: it asks the pure function and
draws what comes back.

**And the page types** (#6). The box at the foot sends one whole `<…>` message
— buffered until complete and written in one write, so two people on the page
at once cannot interleave a command. A command typed without the angle brackets
is sent as if they were there: `s` and `<s>` do the same thing, because the
brackets are the station's rather than the operator's. Everything the station
understands can be typed, `<0>` included; that is what a raw monitor is, and
none of it is a named control on the page. Four more things about it are the
page's own:

- what is sent for what was typed is a pure function of the box's text
  (`ui/src/message.js`), and nothing typed sends nothing: a `<>` on the wire is
  a message the station would refuse, and a page sending one would be typing at
  the railroad on its own account;
- the line the page sent is drawn where the station's lines are, with a mark in
  a column they leave empty and in the page's own accent — two channels rather
  than a colour alone, because which of these lines the page put on the
  railroad is the thing a monitor must not be ambiguous about;
- a command that was not sent draws no line and leaves the typing in the box.
  Nothing typed and no stream open are the two ways that happens, and a line
  claiming the station was asked something it was never asked is the
  observation nobody made (ADR-0009 d.2);
- the box is thumb-sized and the field shrinks rather than pushing the send off
  the side, because the phone at the layout is where a command gets typed.

The framing that makes it a whole message at the device is the **mirror**'s and
is not written a second time here: the page writes one message in one frame and
the mirror reads for the `>`, exactly as it does for JMRI and a throttle
(ADR-0007 d.2, `framing.py`).

**The pairs are run rather than read.** Every other check of the page here
reads its sources, because the gate is Python and there is no browser in it.
Three of them cannot: a sentence an operator is shown is worth nothing asserted
against the source that would produce it — and so is a rule about what goes
down a cable to a command station, and so is what the band says about the
railroad's power — and ADR-0009 d.3 asks for the pairs themselves. So
`tests/ui/test_decoder.py` puts every line the page glosses and every near miss
through the real function under `node`, by way of `tests/ui/gloss.mjs`,
`tests/ui/test_message.py` puts every spelling an operator may type through the
real function the same way (`tests/ui/message.mjs`), and
`tests/ui/test_readings.py` puts whole conversations through the readings and
reads the band and the tiles back (`tests/ui/readings.mjs`). What that asks of
the machine the gate runs on is a node and nothing else — no packages, no
bundler, nothing fetched, no DOM — and a node that is not there is red rather
than skipped, as everything else the gate needs is. It is why
`ui/src/decoder.js`, `ui/src/message.js` and `ui/src/readings.js` are the three
modules of the page written as JavaScript with their types in JSDoc: `tsc`
checks them as strictly as the rest (`ui/tsconfig.json`), and a bare node can
still run them.

**What no check here reaches is Lit.** A bare node with no packages cannot
mount a component, so what the band and the tiles *draw* is asserted as the
words the readings produce and the drawing is held against the components'
sources (`tests/ui/test_band.py`, `tests/ui/test_tiles.py`). That is the same
cost the look values check names: the page is checked in a Python gate, and
that gate has no browser in it.

**Sending is held at the other end too.** What a page types is one more
client's bytes on the mirror's port, so two monitors typing at once is the
interleaving rule `tests/dccex_usb/test_face.py` runs against a pty — two whole
messages at the device, in one order or the other, on a machine with no command
station attached.

The pause and the clear are the rest of the monitor and land under their own
tickets.

**The page is what polls** (#7). The station volunteers a banner and a `<p…>`,
and an idle one says nothing; on a box with no **translator** running, nothing
else asks. So the page asks on its own schedule — `<s>` every five seconds, up
the stream, through the same send an operator's typing goes through, so the
polls are marked as this page's in the monitor — and the mirror goes on
originating nothing
([ADR-0010](../adr/0010-the-page-polls-and-the-mirror-originates-nothing.md)).
Fifteen seconds without a word, which is three polls, and the **link** is down.
The readings are worked out again on a one-second tick as well, because the
link going down is the absence of a line rather than the arrival of one; and a
page that has left stops asking, because a conversation that is quiet when
nobody is watching is the correct conversation (ADR-0010 d.4).

The page is one more client of the mirror's port and is subject to every rule
that port has, including being cut off once it falls too far behind and being
disconnected alongside the throttles when the device has been away past the
grace ([ADR-0007](../adr/0007-the-monitors-stream-is-one-more-client-of-the-mirrors-port.md)).

## How it looks

The look rules are the organisation's, in LOOK.md, and their values arrive here
as a verbatim copy at a fixed path with the commit it was taken at recorded
beside it: `ui/look/tokens.css`, with
[`ui/look/README.md`](../../ui/look/README.md) saying where it came from and at
which commit. That page is the one place the commit is written and this one
does not restate it: the "Taking a change" procedure there is the whole of
refreshing the copy, and a second pin it never mentions would be a line going
stale where no check can see it (#62). `control`'s `ui/look/README.md` is the
shape that follows. The copy is inert: nothing imports it, no build reads it
and the page does not link it.

What the page draws with is `ui/src/look.css`, a `:root` block of this UI's
own, and `tests/ui/test_look.py` asserts the two agree token for token — in
both directions, so a value that drifted here and a token that arrived over
there with nothing to spend it on both go red. It also holds that block to
being the only place a colour is written: a hex in a component stylesheet, in
`ui/src/page.css` or in the page's own markup is red, because each of those
paints and none of them is that one place (#60). It reads the copy and the
files beside it and nothing outside this repository, which is what lets it run
in this gate rather than somewhere that fetches
([org ADR-0010](https://github.com/rails49/.github/blob/main/docs/adr/0010-the-values-check-runs-in-the-consumers-gate-because-it-fetches-nothing.md)).
`--rail-turns` is the one value a stylesheet cannot read for itself — a media
query cannot take a custom property — so it reaches the two sheets that turn as
one number in `ui/src/look.ts`, and the test holds those two to it.

It takes the system's light or dark setting and offers no toggle, as the other
rails49 UIs do, and it works at the width of a phone held at the layout.

## How it is built and served

A multi-stage image, `deploy/ui.Dockerfile`: node to build the sources, nginx
to serve what came out. The box needs Docker and nothing else — no node
toolchain on a machine whose job is a command station — and the node that
builds the page is a container that lasts as long as the build. It installs
with **pnpm**, which is what the project builds pages with (#1, #58), at the
version `ui/package.json` names and from `ui/pnpm-lock.yaml`, frozen: the
image is the versions this repository was checked at, and a lock file that has
drifted stops the build. Nothing outside the image installs anything, so that
build is also the only place the drift is caught. No image is
published anywhere: the box clones and builds
([ADR-0005](../adr/0005-the-image-is-named-by-the-commit-it-was-built-from.md)).
It is named by the commit it was built from like everything else here, as
`dccex-ui:<commit>`; it is a second image rather than the mirror's, which shares
a lock file and an esptool pin with the translator and neither with a page.

**Both bases are pinned by digest, and the tag is kept in front of it.** A tag
is republished, so `node:22-alpine` and `nginx:alpine` are whatever was pushed
under those names this morning: two builds of one commit a month apart are two
different images, and
[ADR-0005](../adr/0005-the-image-is-named-by-the-commit-it-was-built-from.md)
d.7's rebuild of an older commit would not reproduce what shipped (#59). Each
`FROM` carries a digest with its tag in front of it, so what a commit was built
against is recorded in this repository at that commit and a rebuild resolves
the same two images. What a pin costs is that a base takes no security update
of its own until somebody moves it, and `deploy/ui.Dockerfile` is where the
procedure is written, beside the pins it is about: `docker buildx imagetools
inspect <tag>` on a machine that can reach a registry, and the digest it prints
goes into the file — a commit here like any other change to what the image is.
The gate has no registry and resolves nothing, so `tests/deploy/test_stack.py`
holds the shape rather than the values: neither line may name something that
can move. The mirror's image is still on tags and says so
(`deploy/Dockerfile`).

**And it carries that commit as well as being named by it.** The build takes it
as an argument and writes it on the image as
`org.opencontainers.image.revision`, so a `docker inspect` on the box says what
a container was built from even for an image somebody renamed — the name is not
the only copy of the fact, which is what
[ADR-0005](../adr/0005-the-image-is-named-by-the-commit-it-was-built-from.md)
d.4 asks for and what the mirror's image has had since #15. `compose.yaml`
hands the build the same variable it builds the name from, so the two cannot
name different commits. A build nobody gave a commit — which is what
`docker compose up --build` on a clean clone is — carries that label empty: the
name says `dev`, where it is true, and a revision that reads like a commit
reference and is none would be worse than none at all (#57).

`compose.yaml` at the root is the compose project: one service, the door route
as labels on its own container, and nothing more. `docker compose up --build`
from a clean clone serves the page. The stack a **box** runs — the mirror
beside it, the shared network the door dials containers on, the deploy and the
record it appends to — is that file and `compose.box.yaml` together, and the
overlay exists so that this file keeps the promise in the sentence before.

**It serves with no `control` clone present.** That is the installation this
repository exists for, and it is the first thing the first ticket proves.
`tests/ui/test_page_serves.py` is where it is proved: it builds the image, runs
it, and asks it for the page over HTTP, because a suite that reads the files
cannot tell two programs of the same name apart — which is how
`rails49/installation`'s `page/render.sh` ran green everywhere except the only
place it ran for real. It builds the way a clean clone builds, with no commit
passed, so it is also where the empty revision above is held: present, and
saying nothing. It is not part of the gate: it carries the `docker`
marker, and the workflow runs it in a job of its own that a pull request
requires, where a missing daemon is a failure (#54, #56). Run by hand where no
daemon answers it skips and says so.

**And it comes up as a project and not only as an image.** The sentence above —
`docker compose up --build` from a clean clone serves the page — is
`compose.yaml`'s own, and `tests/ui/test_compose_serves.py` is what runs it
rather than reading it (#53): `docker compose up -d --build` against this
repository's file with `DCCEX_UI_PORT=0` so the daemon picks the host port, the
page fetched over HTTP on the port `docker compose port web 80` says it got,
the image name, the commit the project handed the build, and the eight route
labels read back off the running container — which is where a door reads them
from — and `docker compose down` with its
volumes, its network and the image it built, in a `finally`, so a red assertion
leaves nothing behind either. It carries the same `docker` marker and the same
no-daemon rule as the check above it. Two things it does not hold: what a route
*does*, which wants a door and is #40's, and the shared network, which is
declared external in `compose.box.yaml` and deliberately not here, so that `up`
works on a clean clone at all. A project already up under the name the file pins — `name: dccex`
— fails the check with a sentence saying so, because taking down a project it
did not start is not its to do.

## What is not on it

- **Anything about a railroad.** No turnout names, no roster, no run state —
  none of them is a thing a command station says. Somebody wanting them wants
  `control`'s UI, which is next door on the layout box.
- **Commanding track power**, beyond the flash sequence's own step. The band
  presses nothing — there is no button on it, nothing listening for a press and
  no form — and no emergency stop is drawn on the chrome, so the red the look
  rules reserve for the first UI to draw one stays unclaimed.
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
  band drops the track reading below 560px, the tiles wrap onto a second row,
  the release rows wrap, and the command box is thumb-sized with a field that
  shrinks rather than pushing the send button off the side — and nobody has
  held a phone up to them.

What each tile reads while the link is down was the third and is settled above,
by ADR-0008 d.3.
