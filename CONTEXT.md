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
about that app rather than about a railroad (ADR-0002). The UI talks to one
face and nothing else. A face is private to its app: it is not somewhere else
to get at the railroad. Its address is a path prefix on the page's own origin,
which the door strips before the app sees it, and a page from anywhere else is
refused (ADR-0004). The mirror's face answers what releases the source
carries (#12) and writes one of them onto the station when a caller names its
tag (#13). It guards nothing while it does: a face is about its app, so
whether a railroad can spare its command station for two minutes is the
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

## link

Whether the station is answering, which is not the same as whether a socket
is open (`control` ADR-0066). The link is down when the cable is gone, when
the station is being written to, and when it has stopped talking; the build
goes with it.

**Not:** *connected*, *online*, *the connection*, *up*.

## image

What the apps here run as on the box: one image, built from this repository's
source at one commit and named by it — `dccex:<commit>`, and the name never
moves ([ADR-0005](docs/adr/0005-the-image-is-named-by-the-commit-it-was-built-from.md)).
One for the repository and not one per app, so the mirror and, when it lands,
the translator are the same image run twice. What a box is running is
therefore a commit a person can read off it, and the deploy that replaced one
wrote down which it replaced.

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
