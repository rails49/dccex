# Command station over USB

The command station is reached over USB, and one process can hold the device.
That process is the `dccex-usb` app, the **mirror**: it opens the serial device
and mirrors it on a TCP port, so everything else — the `dccex` translator,
JMRI, a hand-held throttle — is a client of the port and they coexist
([control ADR-0043](https://github.com/rails49/control/blob/main/docs/adr/0043-the-layout-interface-is-a-core-app-and-hardware-hangs-under-it-by-address.md)).
DecoderPro keeps working with every app of ours down.

It has no state of its own and, here, **nothing on either of its sides but its
own two ports**: the one the cable is mirrored on, and the one this app's own
face is answered on. In `control` it was an app on the bus, because of the one
thing it does that is not mirroring — **writing a released firmware build onto
the station**, which only the process holding the device can do
([control ADR-0065](https://github.com/rails49/control/blob/main/docs/adr/0065-the-app-that-owns-the-device-flashes-it.md)).
That ask arrived on a topic and a refusal went back as a row. Neither is here:
a command station is not a fact about a railroad, so the mirror answers to
this app's own face instead ([ADR-0001](../adr/0001-the-mirror-leaves-the-bus-for-a-face.md)).
The face answers what releases the configured source carries (#12), writes
one of them onto the station when a caller names its tag (#13), and carries
the station's conversation to the page and back (#14). All three are the app's
own business on the app's own interface, and none of them is a fact about a
railroad.

The code arrived as a copy of `control`'s at `deee7b6`, its file names kept
because that is where the code was written; [SOURCE.md](../../src/SOURCE.md)
says what came from where, and what has been fixed here since `control`'s copy
was deleted
([ADR-0003](../adr/0003-the-copy-has-no-original-left-and-is-fixed-here.md)).

## The command line

```
python -m dccex_usb --device /dev/dccex --port 2560
```

The device to open and the port to serve it on. Two more are optional:

- `--firmware-releases <url>`, where releases are read from, this
  installation's fork by default. It is **configuration and never payload** —
  the LAN carries no authentication on purpose, so a source named by a caller
  would let anyone on the wifi run an arbitrary binary on the command station.
- `--face-port <n>`, the port this app's own face is answered on, 8080 by
  default. A port of its own, because 2560 carries the station's conversation.

There is no broker argument and no identity argument. Both went with the bus:
there is nothing to dial and no row to key by a name.

There is no bind address either. Both servers bind every interface, and what
each of them can be reached from is what the stack publishes. **2560 is
published raw**: JMRI, a throttle and the translator reach the mirror as
`dccex-usb:2560`, and what limits their reach is the LAN, which is the trust
boundary
([control ADR-0042](https://github.com/rails49/control/blob/main/docs/adr/0042-the-edge-terminates-tls-and-the-lan-is-the-trust-boundary.md)).
For the same reason there is no authentication on that port and no limit on
the number of clients beyond the OS's — though there is a limit on how far
behind one may fall, which is a different question. **The face's port is not
published to the LAN at all**: the door reaches it on the box's own network,
and a browser reaches it through the door and never the LAN
([ADR-0004](../adr/0004-the-face-reaches-a-browser-through-the-door-and-never-the-lan.md)).

**A mirror that cannot serve its port exits**, and so does a face that cannot.
Something else on 2560 — a second copy of the app, a container that has not
finished going away — is not a state this app can mirror out of, so it ends
non-zero with the reason on stderr rather than staying up with no server
behind it; and an app whose face nobody can reach is an app the UI does not
have. `restart: unless-stopped` is what tries again, and a port that is busy
for a moment during a deploy comes good on the retry. The device is a
different matter: one that is not there yet is waited for, not exited on.

The device is opened raw at 115200 8N1 — no echo, no line editing, no flow
control — so what a client sends is what the station receives.

## What it does with the bytes

**From the device to the clients: every byte, to every one of them,
unchanged.** Replies are not routed to whoever asked, because one serial
stream cannot say who asked: a reply to a throttle and a broadcast to
everyone look alike on it. Each client hears the whole conversation and
ignores what is not its business, which is what a shared bus has always
asked of the things on it.

**A client that has stopped reading is cut off.** Nothing waits for a client
to take what was fanned to it, so one that never does — a sleeping laptop, a
throttle whose Wi-Fi dropped, a hung DecoderPro — would have bytes buffered
for it for as long as the railroad runs, until the process is killed for
memory and *every* client loses the command station because one of them
walked out of range. Once more than a megabyte is outstanding to a client,
about a minute and a half of everything the device has to say, its connection
is aborted and the log says it went too far behind rather than closing itself.
It may reconnect and pick the live conversation up. Not a bounded buffer that
discards instead: this direction is unframed, so dropping from the middle
hands the client half a message it reads as garbage, and not silence either —
if hardware or a peer breaks, the software says so
([control ADR-0050](https://github.com/rails49/control/blob/main/docs/adr/0050-broken-hardware-is-reported-never-worked-around.md)).

**From a client to the device: whole messages only.** A client's bytes are
buffered until a complete `<…>` message and then written in one write, so two
clients sending at once never interleave a command. Bytes outside a message —
before a `<`, after a `>` — are dropped; a second `<` starts the message over,
so `<<t 3 0 1>` is the one command `<t 3 0 1>`; a buffer that passes 1024
bytes without its `>` is discarded, and so are the bytes after it up to the
next `<`. A client that disconnects mid-message takes its partial message
with it. Nothing else of the protocol is read.

**While the device is away, what a client sends is dropped.** The app reopens
the device with backoff — it goes away when the command station is switched
off, or when the cable is pulled — and for the length of the grace below the
clients wait through it without noticing anything but that their commands did
nothing. A command is honored now or ignored: a queue that flushes on
reconnect is a train that moves minutes after someone asked for it. A message
the app is part way through writing when the device goes is dropped the same
way and at once, rather than waiting on a cable that is no longer there.

**An outage that outlasts the grace disconnects every client on the port.**
The grace is two reopens at the first backoff, about a second, counted off
the backoff rather than kept as a number of its own. A client cannot tell an
away device from a quiet one and this port has no way to tell it, so a mirror
that held its clients through a station switched off would leave the
translator reporting a link that is up over a railroad that cannot move. The
socket closing is the whole signal: the translator's session ends the way it
already ends, and nothing is inferred anywhere
([control ADR-0066](https://github.com/rails49/control/blob/main/docs/adr/0066-the-link-is-the-station-answering-not-the-socket-being-open.md)).
An outage the first reopen recovers is invisible to clients, which is what the
grace is for — a USB blip, not a flash — and a client that connects to an away
device is served the outage itself, its bytes dropped because a command is
honored now or ignored. The grace is the outage's and not each client's, so
one that arrives while an outage is being waited out leaves with the clients
already on it, and one that arrives after they are gone starts the next grace
and gets all of it. Falling too far behind is a different reason to disconnect
and keeps its own rule.

Every way the device can fail to be there is the same outage: a path that is
not there, a path that will not take the line discipline because it is no
tty, a device that is gone again the moment it is open. None of them ends the
retrying or holds a descriptor open, and a session that ends at once is
waited out rather than reopened straight away. Each outage says once that
what clients send is being dropped, and the next outage says it again.

**However a client goes, its connection is aborted rather than closed.**
There are four places it is: the handler that client arrived on, when its
read ends; the cut-off, when it has fallen too far behind; the grace, when an
outage has outlasted it; and the shutdown, when the app itself is going. The
first is the path every client leaves by, whichever of the other three sent
it there, and it is where the disconnect is logged. A polite close waits for
what is still outstanding to reach the client before the socket goes, which
for one that has stopped reading is never — a wait that hung the shutdown and
held the device with it. What an abort costs is bytes that client was not
taking: at the cut-off the megabyte it has not read, at the grace the tail of
a conversation it is about to be told it has lost, and at the handler next to
nothing, because a client that is reading has taken what was fanned to it and
leaves with at most the tail of one fan-out behind it.

**And to a page, by the same rules and none of its own.** The UI's monitor
cannot dial 2560 — a browser opens no TCP socket, and a page served over
`https` opens no plain one — so it asks the face for a **stream** and gets
exactly what is described above: every byte the station says, in step with the
throttles, and what it types reaching the device as whole `<…>` messages under
the same cap. It is **one more client of the port and not a second mirror**:
the face joins 2560 on the box itself and carries the bytes, so the fan-out,
the megabyte a client may fall behind by, the cut-off, the grace and the
framing are the ones on this page and there is not a second set of them
([ADR-0007](../adr/0007-the-monitors-stream-is-one-more-client-of-the-mirrors-port.md)).
A page that has stopped reading is cut off for being too far behind, an outage
past its grace disconnects it alongside the throttles, and the mirror cannot
tell it from DecoderPro. Where the stream is and how a page opens one is
[below](#the-monitors-stream).

It logs connects, disconnects — with the ones it made itself distinguishable
from the ones a client made — the device opening and closing, the first
message dropped in each outage, the grace ending one, and what a flash came
to, to stderr. A page on the stream is a client connecting from loopback and
is logged as one. Nothing else: a mirror that logged the traffic would log the
whole railroad.

## The face

The UI talks to one thing and this is it ([the page](../ui/README.md)): this
app's own face, on the UI's
origin and behind the same door, about the app rather than about a railroad
([ADR-0001](../adr/0001-the-mirror-leaves-the-bus-for-a-face.md),
[ADR-0002](https://github.com/rails49/.github/blob/main/docs/adr/0002-a-ui-talks-to-the-bus-the-store-and-its-own-apps-face.md)).
It is answered on `--face-port`, and **serving it takes nothing from the
mirror**: the device is not reached from here, and 2560 goes on carrying the
station's conversation while the face answers.

### Where it is

At the box's `dccex` label, under a path prefix, on the page's own origin:

```
https://dccex.$BOX_DOMAIN/                     the page
https://dccex.$BOX_DOMAIN/dccex-usb/           this face, which sees /… without it
wss://dccex.$BOX_DOMAIN/dccex-usb/stream       the monitor's stream, on that same router
```

**One label, one certificate, two routers.** The page's router takes the host
and the origin is the page's; the face's is the same host under `/dccex-usb`,
and it claims nothing on the origin but that. **The door strips the prefix
before the mirror sees it**, so the face answers `/releases` and never the
address a browser typed — a prefix arriving here is a door that did not strip
it, and a path this face does not answer. The monitor's stream rides the same
router, which is what makes it `wss://` on the page's own origin with no
second certificate anywhere.

**A browser reaches this through the door and never the LAN**
([ADR-0004](../adr/0004-the-face-reaches-a-browser-through-the-door-and-never-the-lan.md)).
Only the containers a browser reaches carry door labels — the page's and this
one — and the mirror goes on publishing 2560 raw beside them.

Three of the steps are the box's rather than this app's, and none of them is
code here:

- an `A` record for the `dccex` label, because the door issues a certificate
  per router through ACME DNS-01 and holds no wildcard;
- `dccex` in `BOX_UIS` in `/etc/rails49/box.env`, which is root-owned and
  edited by hand, so that the box's page links the UI;
- checking it once from a browser: the page loads over the door's
  certificate, the monitor's stream opens as `wss://`, and a fetch from
  another origin gets the face's `403`.

The face's router is code, and it is in `compose.box.yaml` on the mirror's
container: the page's host at priority 2 under `/dccex-usb`, stripped before
the face sees it, dialling 8080 and nothing else (ADR-0004 d.2, d.5).

What it answers, which is four things — three questions and a conversation:

```
$ curl http://dccex-usb:8080/releases
{"releases": [
  {"tag": "v5.6.4-rails49.1", "published": "2025-09-14T10:32:07Z", "flashable": true},
  {"tag": "v5.6.3-rails49.2", "published": "2025-08-02T18:05:44Z", "flashable": true}
]}

$ curl -X POST http://dccex-usb:8080/flash -d '{"tag": "v5.6.4-rails49.1"}'
{"flashed": "v5.6.4-rails49.1"}

$ curl http://dccex-usb:8080/clients
{"clients": 3}
```

The **release**s the configured source carries, in the order the release API
lists them, so nobody has to type a **tag** from memory. Three facts about
each: the tag it is named by, the moment the source published it, and whether
it carries the `firmware.bin` this app would write — with the digest the source
reports for it, because an asset the source reports no digest for is one this
app refuses to write, and a flag that said otherwise would send an operator
through the whole flash sequence for a refusal (#81). The last two are what a
page needs to say which release is newest and which one there would be nothing
to write for, and a release missing either is listed without it rather than
dropped — what the source carries is what a person is shown (#8). What is
*not* passed on is the rest of somebody else's entry: a page handed the whole
document would be a page reading the release API through a hole in the face.

A tag is still all a caller ever names: **where releases are read from is
`--firmware-releases`, this app's configuration, and no request can redirect
it.** The query string is dropped and the body is not read for a source,
because the LAN carries no authentication on purpose (control ADR-0042) and a
request that named a source would be a request that decides what the station
is offered to run.

Which of them is newest is the page's question rather than this app's: the
dates go back as the source stamped them and the ordering is done where the
list is drawn (docs/ui/README.md).

The third is how many **client**s are on 2560 at the moment it is asked, and
it is the one reading on the page that is not the station talking: a command
station knows nothing about who is listening to it, and the app holding the
port does ([ADR-0008](../adr/0008-the-page-talks-to-the-face-and-reads-the-build-off-the-banner.md)
d.4, #7). A count and not a list — clients are equal here and the mirror does
not know which of them is which (CONTEXT.md) — read off the fan-out at the
question rather than kept, so a throttle that has gone is not one a page goes
on being shown. Nobody on the port is `0` and an answer like any other: on the
box this UI exists for, a page and nothing else is the ordinary evening.

The second is [the flash](#writing-the-firmware), and the answer comes back
when it is over: a minute or two, because that is how long writing four
megabytes at 460800 baud takes. A caller is waited on for the whole of it —
what it asked is whether the station runs that build now, and esptool exiting
non-zero is not knowable before esptool has run. What bounds a request is the
caller: the head, the body and the answer being taken. A caller that goes away
mid-flash loses only the answer, because the station is being written by then
and stopping halfway is the one thing nobody can recover from.

**What it will not answer is a status and a sentence**, in a `reason` field,
so whoever asked can say what happened rather than sending somebody to read a
log on the box (control ADR-0050):

- `404` — a path this face does not answer, or a tag the source answered
  about and carries no release for. The tag is the thing to fix, which is why
  a source that was never asked is a `502` below and not this. A face is
  private to its app and is not somewhere else to get at the railroad.
- `405` — the releases and the count of clients are read, with `GET`; a flash
  is asked for, with `POST`. There is nothing at `/flash` to read, and a page
  that reloaded one would write the station again; there is nothing at
  `/clients` to change, because who is on 2560 is decided by who dialled it.
- `502` — the source could not be reached, or answered with something that
  cannot be used: not a list of releases, not JSON at all, a status other than
  the `404` above, a release carrying no `firmware.bin`, no digest for it, or
  bytes that are not what the digest says. It is the same answer whether the
  releases were being listed or a tag was being written, because it is the
  same outage and the same question. The release API is somebody else's
  service and the mirror keeps mirroring what it is doing rather than falling
  over with it. A source that has published nothing yet is not this: that is
  an answer, and the tags are empty.
- `400`, `413`, `431` — a request this face cannot read: not HTTP, a head or a
  body larger than a page asking a question has any use for, a body that names
  no tag, or `latest`, which is not a name for a build.
- `409` — a flash is already in flight. Refused and not queued, for the reason
  a client's bytes are dropped while the device is away: a queued flash is a
  station that reboots minutes after somebody asked.
- `503` — the command station is not there. Nothing is wrong with the request;
  the cable is out or the board is off, and it is fixed at the hardware.
- `500`, `504` — esptool exited non-zero, or outlived its timeout and was
  killed. The station may be half written; both are on the box's log as well,
  because neither is the caller's doing.
- `403` — a page on another origin. The page and the face share one origin
  behind the door, so a browser says which page asked and this face holds it
  to that ([ADR-0004](../adr/0004-the-face-reaches-a-browser-through-the-door-and-never-the-lan.md)).
  It is the stream's own guard as much as the other routes': a browser asks
  nobody before opening one.
- `503` — also the mirror's port not being there when a page opens a stream.
  Nothing is wrong with the request; the port is this app's own, so one that
  cannot be joined is an app on its way down.

Whoever asked is told, and the box's log is told only what is not the
caller's doing: a source that could not be read is a line on stderr as well,
and a path the face does not answer is the caller's own to read.

Of HTTP it reads the request line, the length of the body, the origin the
request was addressed to, the origin of the page that asked and the key a
browser names when it is opening a stream — nothing else — and it answers one
request per connection. This is a private origin spoken to by one page, so
negotiation and a connection kept open for the next request are protocol it
would carry without ever being asked for it. One request is bounded in time,
because the loop it is answered on is the one that holds the command station.
A stream is not: it is open for as long as somebody is watching the railroad,
and what lets go of one that has stopped reading is the mirror.

Nothing in the gate reaches the release API. What fetches a URL is injected
here exactly as it is for the flash, and the suite substitutes its own, so
every question about what the face says is asked of its routing directly —
a function of a method, a path and a body, answering with a status and a body,
with no socket anywhere near it.

### The monitor's stream

The third thing the face carries is the station's conversation, both ways, on
the same port and under the same prefix:

```
wss://dccex.$BOX_DOMAIN/dccex-usb/stream   the monitor's stream
```

A page opens it by upgrading — there is nothing at `/stream` to fetch, and a
`GET` that names no key is a `400` — and the door's prefix is off it by the
time the app sees it, exactly as for the other two. One router carries the
stream and the requests beside it, which is what makes it `wss://` on the
page's own origin with no second certificate anywhere (ADR-0004 d.3).

What rides on it is the bytes and nothing else. The station's go out as
**binary** frames, unchanged: a text frame has to carry valid UTF-8, a serial
line promises none, and one garbled byte would end a stream whose whole
contract is that every byte arrives as it was sent. What the page sends is read
the other way round — text, binary or a continuation, all of it payload —
because what ends a message is `>` and the mirror is what reads for it. There
is no protocol of our own on the stream: no progress, no status, no link. What
the link is doing is read off the conversation, as the translator reads it
([control ADR-0066](https://github.com/rails49/control/blob/main/docs/adr/0066-the-link-is-the-station-answering-not-the-socket-being-open.md)).

Nothing is buffered between the page and the port. What the browser has not
taken is waited on before more is read off the mirror, so a monitor that has
stopped reading fills the mirror's socket and is cut off by the megabyte rule
above — the mirror's own, in the mirror's own log line. A buffer here would
hold what the mirror believes it has handed over, and that rule would never
fire.

A frame larger than 64 KiB is refused on its header and the stream ends saying
so, as does one that breaks the framing rule — unmasked, reserved bits set, a
control frame split or overlong. A message the station answers to is a
kilobyte, so a frame that size is already not a command.

## Writing the firmware

The station's firmware is built elsewhere, against the station's own source.
What this app does is write a **release** onto the box when it is asked for by
`tag`, and never by a source. It is the only process that can — it holds the
serial device open, esptool cannot share it, and no container can stop a
sibling without the Docker daemon's socket, which is root on the box
(control ADR-0065).

**Who asks is the face** (ADR-0001, #13): `POST /flash` with the tag in its
body, answered when the writing is over. `Flasher` takes that tag as a call on
the mirror's own loop, and that call is the whole of the way in — there is no
topic, no second port and no command-line option that reaches it.

On the ask, in this order, and the order is the point:

1. Resolve the `tag` against the release API of `--firmware-releases`. The tag
   is escaped whole, so nothing in it can name a path of its own choosing.
2. Fetch `firmware.bin`.
3. Check it against the `digest` that API reports for the asset — a
   per-asset `sha256:…`, so a tag chosen at the moment of the ask is
   still checked. esptool verifies what it wrote, not what was fetched.
4. **Then** close the serial device.
5. Run esptool.
6. Reopen the device by the existing path — unless the app is being stopped
   meanwhile, in which case nothing takes the device back: a flash is shielded
   from the signal that ends the app, so it can outlive the mirror, and a
   mirror that has shut down has no port to mirror the cable on.

A network failure costs nothing that way. The reverse order leaves the
railroad with a closed port and no firmware.

esptool is a **subprocess with a timeout**, not a library call: this process
is the one every throttle, DecoderPro and the translator depend on, and
esptool manipulates the port and exits on error, so a subprocess is what buys
crash isolation, a timeout and a kill. It is this repository's one dependency,
pinned by `uv.lock`, so `uv run esptool` works on a laptop too. The command
line, against the device the container already maps:

```
esptool --chip esp32 --port /dev/dccex --baud 460800 \
  --before default-reset --after hard-reset write-flash -z \
  --flash-mode dio --flash-freq 80m --flash-size 4MB 0x0 firmware.bin
```

Flash mode, frequency and size are the station core's own upload settings.
Hyphenated throughout: esptool 5 renamed the entry point and the subcommands,
and the underscore forms are deprecated aliases a later major drops.

**While it writes, the device is away and clients on 2560 are served the
device-away behaviour above** — their bytes dropped, and their connections
closed once the grace passes, because for that minute or two the device
genuinely is away and a flash outlasts any grace. The railroad going dark for
the length of a flash is the correct outcome: nobody expects trains to run
while the station is being written, and the guard against a flash under a
moving train is the operator's, below. Progress needs nothing of its own: the
link is down and the translator that lost it says so, and when the station
answers again it reports the **build** it now runs.

**What it refuses**, each of them a status and a reason to whoever asked and a
line on the box besides: a tag the source carries no release for (`404`), a
source that could not be asked about it at all, a release carrying no
`firmware.bin` or no digest for it, and a digest that does not match (`502`),
esptool exiting non-zero (`500`), esptool outliving the timeout (`504`), the
device absent (`503`), and a second ask while a flash is in flight
(`409`) — refused, not queued, for the reason a client's bytes are dropped
rather than queued. `latest` is refused too (`400`): it names a different build
depending on when it is read, and what was written has to be sayable
afterwards. The statuses are listed with the rest of the face's
[above](#the-face). A refusal leaves the app able to take the next ask: the
flag falls whichever way a flash ended, and an app that refused everything
after one failure would be worse than the failure.

**Whether it is safe to reset the station is the operator's**, not this app's,
and that is where the obligation sits now that a page can ask
([ADR-0006](../adr/0006-the-operator-is-the-only-guard-on-a-flash.md)).
Flashing drops the rails and disconnects every throttle, and nothing between
the person and the station checks that a train is not moving: this app is not
on the bus, so it cannot read a run state or a track row, and the face is about
this app rather than about a railroad. The page sequences what it can and
confirms; what it cannot do is prevent, and none of the refusals above is a
safety mechanism — they are about tags, sources, digests and devices. It is the
rule cutting track power already has, on the other thing that stops a railroad
(control ADR-0051, control ADR-0062). Reading the dispatcher's state is the
coupling this app has never had and the reason it is trustworthy.

## Deploying it, and going back

The mirror runs on the box as a container of `dccex:<commit>`, the **image**
built from this repository's source at one commit and named by it
([ADR-0005](../adr/0005-the-image-is-named-by-the-commit-it-was-built-from.md)).
The name never moves: nothing runs `latest` and nothing runs `main`, because a
name that means a different commit next week is a name nothing can be gone
back to. The commit is on the image as `org.opencontainers.image.revision`
too, so `docker inspect` still answers the question for one somebody renamed.
**A tag is not what this is called** — a tag names a firmware release, which
is the thing that gets written onto the station, and the two sentences are one
`docker` command apart on the same box ([CONTEXT.md](../../CONTEXT.md)).

**A build nobody gave a commit claims none.** That is what `docker compose up
--build` on a clean clone is, and the label it writes is empty: `dev` is what
such a build is *named*, where it is true, and a revision that reads like a
commit reference and is none would send a reader of `docker inspect` looking
for a checkout that never existed (ADR-0005 d.4 as amended, #97). The stack
hands the build the same variable the name is built from, so the two cannot
name different commits. `tests/deploy/test_mirror_serves.py` is where this is
held rather than read: it builds the image with nothing passed and asks the
built artefact what it claims.

**What is under the name does not move either.** Both bases of
`deploy/Dockerfile` are pinned by digest with the readable tag in front of it,
so two builds of one commit a month apart are the same image and d.7's rebuild
of an older commit resolves the bases that commit was written against (#96).
The page's were pinned first and its image is where the argument is written,
including what the pin costs — a pinned base takes no security update of its
own until somebody moves the pin, and moving one is a commit here like any
other ([the page's page](../ui/README.md), `deploy/ui.Dockerfile`). What the
gate can hold is the shape and not the values, because resolving a tag needs a
registry it has not got: `tests/deploy/test_stack.py` reads both `FROM` lines
back and asks that neither names something that can be republished underneath
it.

**A deploy writes down what it replaced**, at
`/var/lib/rails49/deploys/dccex`: one line per deploy, newest last, appended
and never rewritten, plain text for somebody who has just been handed the box
and has nothing else on it. The commits are written in full; they are
abbreviated here to fit the page.

```
$ tail -2 /var/lib/rails49/deploys/dccex
2026-09-22T18:40:55Z  none            ->  dccex:8f2c1d4…
2026-09-23T09:14:02Z  dccex:8f2c1d4…  ->  dccex:acb08f5…
```

**Going back is one command naming the commit on the line before.** A deploy
keeps the image it replaced, so it is already on the box: nothing is rebuilt,
nothing is pulled, and no digest is recovered by hand.

```
$ cd ~/dccex
$ echo DCCEX_COMMIT=8f2c1d4… > .env
$ docker compose -f compose.yaml -f compose.box.yaml \
    --env-file /etc/rails49/box.env --env-file .env up -d --no-build
```

`--no-build` is there for the day the old image has been pruned after all.
Without it, compose would build the checkout the clone is on and name it after
the older commit; with it, the command fails and says the image is missing.

The stack's `.env` holds that one line, because the commit is the one thing
that differs between two deploys of this repository, and writing it there is
what makes `restart: unless-stopped` bring back what was rolled back *to*.
**One line and not two**: the commit names the mirror's image and the page's
both — `dccex:<commit>` and `dccex-ui:<commit>` — and ADR-0005 d.7 is amended
for it, because when d.7 was written the page was not here to be rolled back
with the mirror. Nothing about a rollback moves `main`: the box is behind the repository
until somebody commits the fix and deploys it, and the record above is where
that is visible. One step back is what is kept; older images are the box's to
prune, and what pruning them costs is a second step.

**A deploy that fails is a deploy that did not happen.** `.env` has to say the
new commit before the `up` — `--env-file .env` is how compose is told which one
— so an `up` that fails is a file naming a commit that was never brought up. It
is put back: the previous commit, or removed where a first deploy onto a box had
none, so that what the next deploy reads for its `went` is true (#83). Nothing
is appended to the record, which is right — nothing was replaced. The failure is
loud: the deploy exits non-zero and says which commit the box was left on. The
containers are not rolled back, and going back on a deploy that did happen is
the command above rather than something a failure does on its own.

All of this is code here now. `deploy/Dockerfile` is the image; `compose.yaml`
and `compose.box.yaml` are the project, the second being the box's half — the
mirror, the device, 2560 raw, the shared network external and the box's
declaration required rather than defaulted; `scripts/deploy.sh` is the deploy,
one ssh and one heredoc, which refuses a clone that is not clean and appends
the line above. The gate reaches no box and builds no image, so it is one
command with one exit status as it was: the check that starts the built image
and dials 2560 against it carries the `docker` marker, and the workflow runs
it in the job of its own that the page's two are already in (#54, #56). What
the deploy leaves behind either way is run rather than read, in
`tests/deploy/test_deploy_runs.py`: the heredoc is saved by a fake `ssh` and put
through `bash` here, against a clone the suite makes and a `docker` that fails
on purpose.

**The first one is a cutover and not a deploy.** 2560 is served on the layout
box today by `control`'s copy of this app, and the evening it changes hands is
#16: `control`'s deploy goes first, because that is what removes the orphaned
container and repoints the translator, and this stack's takes the port after
it. What that evening follows is [the cutover page](../cutover.md), written
beforehand and carrying the order, the abort signal, the checks, and a way back
that is not the rollback above — it puts `control`'s mirror on 2560 again,
named by a digest, because that image has no name that says what it is.

## Checking it against a real station

Nothing in the test suite needs the hardware — the tests use a pty as the
device, so the gate is green on a laptop with nothing plugged in. That holds
for the flash as well: esptool cannot write a pty and the gate reaches no
release API, so what fetches a URL and what runs a command are injected and
the suite substitutes its own. What the suite does hold is the ordering —
the device closed before the runner is called and reopened after. Verifying
the actual link is runtime's job, and it is one command:

```
$ nc gleis49.org 2560
<s>
<iDCC-EX V-5.4.16 / ESP32 / EXCSB1_WITH_EX8874 G-9db8d0e>
<p0>
<c CurrentMAIN 0 C Milli 0 0 4000 1000>
```

`<s>` asks the station for its status; the banner naming the firmware, the
board and the motor shield is the station answering through the mirror. Open
a second `nc` alongside the first and send `<s>` from one: both see the reply,
which is the fan-out. With DecoderPro connected as a third client, the same
holds — that is the point of the app.

A client that has **stopped** reading is `scripts/deaf_client.py`, because `nc`
reads and an `nc` that has been suspended is a thing somebody has to remember
how to do. It connects, sends `<s>` so there is something to fill with, reads
nothing, and says when its receive buffer has stopped growing — which is the
state the cut-off, the grace and the shutdown are all about, and the state the
cutover takes this app's SIGTERM in. It is not in the gate: it wants a mirror on
the other end of a socket, and the gate runs with nothing plugged in.
