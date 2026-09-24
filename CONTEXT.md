# CONTEXT

The words this repository uses, and the ones it refuses. A word listed under
**Not** is not a softer way of saying the entry it sits under; it is a word
that means something else here, or that once meant this and stopped. Use the
entry.

Two apps and a UI live here, and all three are about one piece of hardware at
the end of one cable. That is what makes the vocabulary worth writing down:
the same words are spoken next door in `control`, where the subject is a
railroad, and one of them is spoken about the opposite thing.

These are concepts and not modules. `mirror` is what the app is; the class it
is written as is `Station` and the file is `src/dccex_usb/station.py`, which is
what `control` called them, because that is where the code was written
([SOURCE.md](src/SOURCE.md)).

## station

The command station: the DCC-EX board at the end of the USB cable, the
firmware running on it, and the `<…>` conversation it holds. It is what
`dccex-usb` opens, what `dccex` translates for, and what the UI is a page
about.

`control`'s glossary makes the opposite reservation — there the bare word is
spoken for by a place on a layout, and this hardware has to say *command
station* in full. Nothing here is a railroad, so here the bare word is the
hardware, and a place on a layout is named in full if it ever comes up.

**Not:** *base station*, *the CS*, *the controller*, *the box* (the box is the
machine the apps run on), *the device* (the device is the file the cable is).

## mirror

`dccex-usb`: the app that holds the serial device and repeats it on a TCP
port, so the translator, JMRI and hand-held throttles can all watch the same
conversation and all type into it. It mirrors — it does not decide, rewrite or
answer on the station's behalf. Every byte the station sends reaches every
client; what a client sends reaches the station only as a whole `<…>` message.

**Not:** *proxy*, *bridge*, *relay*, *multiplexer*, *hub*, *serial server*,
*daemon*.

## translator

`dccex`: the app that turns the layout interface's desired values into the
station's `<…>` messages and reports what it hears back. It is a client of the
mirror's port like any other.

**Not:** *driver*, *adapter*, *gateway*, *bridge*, *the dccex service*.

## face

An app's own interface, served on the UI's origin and behind the same door,
about that app rather than about a railroad (the organisation's
[ADR-0002](https://github.com/rails49/.github/blob/main/docs/adr/0002-a-ui-talks-to-the-bus-the-store-and-its-own-apps-face.md)).
The UI talks to one face and nothing else. A face is private to its app: it is
not somewhere else to get at the railroad. Its address is a path prefix on the
page's own origin, which the door strips before the app sees it, and a page
from anywhere else is refused (ADR-0004). The mirror's face answers what
releases the source carries (#12), writes one of them onto the station when a
caller names its tag (#13), carries the station's own conversation to the page
and back (#14, the **stream** below), and says how many **client**s are on the
mirror's port (#7) — which is the one reading on the page the **station**
cannot make about itself. It guards nothing while it does: a face is about its
app, so whether a railroad can spare its command station for two minutes is the
operator's question and not this app's (ADR-0006).

**Not:** *API*, *backend*, *endpoint*, *REST*, *web service*.

## build

What the station says it is running: the `G-` field of the banner it sends
when it comes up. It is a fact reported by the hardware, so it is empty
whenever the station is not answering, and it is the thing a release is
compared against.

The word is spent on the station. Turning the UI's sources into something
servable is *building the UI*, as a verb; nothing in this repository is called
*the build* except the station's.

**Not:** *version*, *firmware version*, *the current release*.

## release

A published firmware in our `CommandStation-EX`, digest and all, that can be
written onto the station. A release exists whether or not any station is
running it.

**Not:** *version*, *update*, *download*, *image* (the image is what the
apps here run as on the box), *the firmware* (the firmware is what is on the
station, which is its build).

## tag

The name a release is chosen by, and the only thing a caller names when it
asks for one to be written. The mirror is configured with the source; a tag
picks among what is already published there. Nothing names a URL, and `latest`
is not a tag.

Docker calls the part of an image's name after the colon a tag too. Here that
part is a commit and is not called one (ADR-0005): a box is rolled back by
naming a commit and a station is written by naming a tag, and the two
sentences are one `docker` command apart on the same box.

**Not:** *version number*, *label*, *ref*, *latest*, *image tag*.

## client

Anything connected to the mirror's port: the translator, JMRI, a hand-held
throttle, the UI's monitor by way of the face. Clients are equal — the mirror
does not know which of them is which, and does not keep one waiting for
another.

**Not:** *subscriber*, *listener*, *consumer*, *session*.

## stream

The station's conversation on the face: every byte the mirror hands a client,
reaching a page, and what the page types reaching the device. It is **one more
client of the mirror and not a second mirror** — the same fan-out, the same
bound on how far behind a client may fall, the same outage — because the face
joins the mirror's port for it and carries the bytes
([ADR-0007](docs/adr/0007-the-monitors-stream-is-one-more-client-of-the-mirrors-port.md)).

It is opened by upgrading a request on the page's own origin, which is what a
browser can do where dialling 2560 is not, and it is served on the face's port
beside the face's other requests (ADR-0004 d.3).

**Not:** *websocket* (that is the transport it rides, and the word is the
protocol's rather than a name for what is on it), *feed*, *channel*, *socket*
(a socket is what a client of the mirror's port opens), *the monitor* (the
monitor is the page that shows this; the stream is what it is shown).

## link

Whether the station is answering, which is not the same as whether a socket
is open (`control` ADR-0066). The link is down when the cable is gone, when
the station is being written to, and when it has stopped talking; the build
goes with it.

**Not:** *connected*, *online*, *the connection*, *up*.

## monitor

The page the **stream** is shown on and typed into: the station's conversation
as it arrives, each line stamped with the time it arrived, the ones the
**decoder** knows carrying a **gloss**, and a box at the foot that sends one
whole `<…>` message. It is the UI's and not the mirror's — the mirror carries
the stream and reads nothing on it.

The word is the page's rather than the port's. A throttle watching the same
conversation on 2560 is a **client**, and so is the face carrying this one
(ADR-0007); what makes this a monitor is that a person is reading it.

**Not:** *console*, *terminal*, *serial monitor*, *log* (the log is what the
apps say on stderr), *the stream* (the stream is what a monitor is shown),
*the UI* (the UI is the whole page, and the monitor is the part of it the
conversation is on).

## decoder

The pure function the page reads the conversation with: one line of the
station's `<…>` in, one reading out or nothing — the **gloss** the monitor
draws beside the bytes, and the fact the **band** and the **tile**s are made of
where the line carries one. No socket, no state and no clock, so what it makes
of a line is asserted as that line and that reading on a machine with nothing
plugged in
([ADR-0009](docs/adr/0009-the-decoder-is-a-pure-function-and-an-unknown-line-gets-no-gloss.md)).

It is the UI's own, and it runs the opposite way from the **translator**,
which turns a layout's desired values into `<…>`. Neither of the apps here
decodes anything: the mirror reads `<` and `>` and no further, and the
translator's reading is its bus contract rather than a page's.

**Not:** *parser*, *interpreter*, *translator* (the translator is `dccex`),
*protocol handler*, *renderer*, *formatter*.

## gloss

The plain sentence the monitor shows beside a line the **decoder** knows, so
that `<H 12 1>` is something a person reads rather than remembers. A line the
decoder does not know is shown raw and gets none: a guess standing where a
reading goes is an observation the page did not make (ADR-0009,
[control ADR-0050](https://github.com/rails49/control/blob/main/docs/adr/0050-broken-hardware-is-reported-never-worked-around.md)).

**Not:** *description*, *explanation*, *translation*, *tooltip*,
*annotation*, *comment*, *label*.

## band

The chrome across the top of every rails49 UI, carrying what is true of the
whole system. Here that is two readings — the **link**, and whether the rails
are hot — and it presses nothing: `control`'s band commands track power
because `layout` checks the railroad is drained before the wire carries
anything, and this page is on no bus for anything to check
([ADR-0008](docs/adr/0008-the-page-talks-to-the-face-and-reads-the-build-off-the-banner.md)).
The **rail** down the side is its counterpart, and both are LOOK.md's rather
than this repository's.

**Not:** *header*, *top bar*, *nav*, *navbar*, *toolbar*, *title bar*,
*status bar*.

## rail

The chrome down the side of every rails49 UI, carrying what the view in front
of a person offers. Here it offers nothing yet: `dccex-rail` draws the column,
one button wide, and the run the first buttons will land in — the flash
sequence's, when it arrives. It is the **band**'s counterpart and LOOK.md's in
the same way, which is why its colour, the width of a button on it and the
window height it turns at are the `--rail*` tokens rather than numbers of this
page's (`ui/src/ui/dccex-rail.ts`, [ui/look/README.md](ui/look/README.md)).
Below `--rail-turns` it lies down along the top of the work pane, and a rail
lying down is still the rail.

It is not the steel. What the locomotives run on is the track, which this file
speaks of in the plural — the **band**'s second reading is whether the rails
are hot, and a **tile** carries the current on them — and never as *the rail*.
So the bare word here is the chrome, the way the bare **station** here is the
hardware: what is drawn down the side of a page, and never anything a train
touches.

**Not:** *sidebar*, *side nav*, *nav*, *navbar*, *drawer*, *menu*, *toolbar*,
*the rails* (the rails are the track's steel, and what they are is hot or
not), *strip* (the strip is the shape this takes on a short window and not a
second thing).

## tile

One reading of the station's particulars on the page's work pane. There are
four — the **build**, the current on the track, how many **clients** are on
the mirror's port, and how long ago the station last said anything — and three
of them blank together when the **link** goes down, because three of them are
the station talking.

**Not:** *card*, *widget*, *panel*, *badge*, *stat*, *metric*, *gauge*.

## image

What the apps here run as on the box: built from this repository's source at
one commit and named by it — `dccex:<commit>`, and the name never moves
([ADR-0005](docs/adr/0005-the-image-is-named-by-the-commit-it-was-built-from.md)).

There are two, and the second is the page's (#3). The apps do not get one
each: the mirror and, when it lands, the translator are the same image run
twice, because they share a lock file and the esptool pin, and a second image
of them would be a second answer to which esptool this repository was tested
at. The page shares neither — it is built by node and served by nginx — so
`dccex-ui:<commit>` is its own, and the single stage that would have held it
with them is the one carrying both toolchains, which is the second answer
rather than a way around it (`deploy/ui.Dockerfile`,
[docs/ui/README.md](docs/ui/README.md)). What divides images here is a
toolchain and never an app.

Both are named by the same commit, so what a box is running is a commit a
person can read off it, going back names it once and takes both (ADR-0005
d.7, as amended), and the deploy that replaced them wrote down which it
replaced.

**Not:** *version*, *build* (the build is the station's), *release* (a release
is firmware, published elsewhere), *tag* (a tag names a release), *the
container* (the container is one running of an image), *latest*.

## cutover

The evening 2560 changes hands: `control`'s mirror container comes off the
layout box, this repository's stack takes the port, and the translator is
repointed by `control`'s own deploy in the same step. It happens once, it is
followed from a page written beforehand
([docs/cutover.md](docs/cutover.md), #16), and what ends it is a person
accepting the railroad rather than a command returning.

A **deploy** is the other thing and happens whenever somebody merges: one image
of this repository replaced by another of its own, nobody watching a train, and
one step back kept by the deploy's own rule (ADR-0005). Going back on a cutover
is not that rollback — it puts `control`'s mirror back, named by a digest,
because that image has no name that says what it is.

**Not:** *migration*, *the switch*, *the swap* (the swap is one step of a
cutover, the container coming off and this one going on), *the window* (the
window is the evening the cutover is done in), *deploy*, *rollback* (going back
on a cutover and going back on a deploy name different things).
