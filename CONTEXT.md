# dccex

The words this repository uses. Words used in more than one rails49 repository
are in the organisation's
[CONTEXT.md](https://github.com/rails49/.github/blob/main/CONTEXT.md). Every
entry links to the doc that owns it (org
[ADR-0017](https://github.com/rails49/.github/blob/main/docs/adr/0017-each-fact-has-one-owner-and-an-accepted-adr-does-not-change.md)).

## Language

**Station**:
The command station: the DCC-EX board at the end of the USB cable, the
firmware on it, and the `<…>` conversation it holds. `control` uses the bare
word for a place on a layout and says *command station* for this; here the
bare word is the hardware
([docs/dccex_usb/README.md](docs/dccex_usb/README.md#command-station-over-usb)).
_Avoid_: base station, the CS, the controller, the box (the machine the apps
run on), the device (the file the cable is)

**Mirror**:
`dccex-usb`: the app that holds the serial device and repeats it on a TCP
port, so every **client** hears the same conversation and can type into it. It
does not decide, rewrite or answer for the station
([docs/dccex_usb/README.md](docs/dccex_usb/README.md#what-it-does-with-the-bytes)).
_Avoid_: proxy, bridge, relay, multiplexer, hub, serial server, daemon

**Translator**:
`dccex`: the app that turns the layout interface's desired values into the
station's `<…>` messages and reports what it hears back. It is a client of the
mirror's port
([docs/dccex/README.md](docs/dccex/README.md#dcc-ex)).
_Avoid_: driver, adapter, gateway, bridge, the dccex service

**Script**:
A railroad's Python document in `control`'s store, one per railroad. It holds
the **handler**s, and it is where this railroad's `<…>` that the bus has no
word for is written
([docs/dccex/README.md](docs/dccex/README.md#the-script)).
_Avoid_: config, plugin, automation (EX-RAIL's word), the startup file (the
file it replaced)

**Handler**:
A function in the **script** that the translator runs when its **event**
happens
([docs/dccex/README.md](docs/dccex/README.md#the-script)).
_Avoid_: hook, rule, callback, listener, trigger

**Event**:
What a **handler** is keyed on: a desired value the translator is applying,
something the station reported, or `start`
([docs/dccex/README.md](docs/dccex/README.md#what-a-script-is-written-with)).
_Avoid_: message (one `<…>`), topic, trigger, signal (a lineside device)

**Trip**:
A district the station cut itself, after an overload or a fault on its driver
([docs/dccex/README.md](docs/dccex/README.md#the-mapping)).
_Avoid_: short (one cause of a trip), fault (`control`'s band's word), off (a
district someone turned off)

**Journal**:
The translator's record of what the station said about power, of the link
going down and of the station restarting, each line stamped with when it
arrived
([docs/dccex/README.md](docs/dccex/README.md#the-journal)).
_Avoid_: log (what the apps write to stderr), trace (`control`'s recording of
the bus), history, event log (an **event** is what a handler is keyed on)

**Incident**:
Something in the **journal** a person should look at, such as a trip, the link
going down or the station restarting. It is a reading of the journal and not
something written in it
([docs/ui/README.md](docs/ui/README.md#what-it-makes-of-the-journal)).
_Avoid_: error, fault, event, alarm, short (one cause of a trip)

**Face**:
The organisation's word
([CONTEXT.md](https://github.com/rails49/.github/blob/main/CONTEXT.md),
[ADR-0002](https://github.com/rails49/.github/blob/main/docs/adr/0002-a-ui-talks-to-the-bus-the-store-and-its-own-apps-face.md)).
The mirror's face is private to this UI; what it answers is in
[docs/dccex_usb/README.md](docs/dccex_usb/README.md#the-face).
_Avoid_: API, backend, endpoint, REST, web service

**Build**:
What the station says it is running, and what a **release** is compared
against: the `G-` field of the banner it sends when it comes up. It is empty
whenever the station is not answering. Nothing else here is called a build;
making the UI or an image is *building* it
([docs/ui/README.md](docs/ui/README.md#the-releases)).
_Avoid_: version, firmware version, the current release

**Release**:
A published release of our `CommandStation-EX`. It may carry a firmware to
write, with a digest to check the write against
([docs/dccex_usb/README.md](docs/dccex_usb/README.md#writing-the-firmware)).
_Avoid_: version, update, download, image (what the apps here run as), the
firmware (what is on the station, which is its build)

**Tag**:
The name a release is chosen by, and the only thing a caller names when it
asks for one to be written. `latest` is not a tag, and the part of an image's
name after the colon is a commit, not a tag
([docs/dccex_usb/README.md](docs/dccex_usb/README.md#writing-the-firmware)).
_Avoid_: version number, label, ref, latest, image tag

**Client**:
Anything connected to the mirror's port: the translator, JMRI, a hand-held
throttle, the face carrying the **stream**
([docs/dccex_usb/README.md](docs/dccex_usb/README.md#what-it-does-with-the-bytes)).
_Avoid_: subscriber, listener, consumer, session

**Stream**:
The station's conversation on the face: every byte the mirror hands a client,
reaching a page, and what the page types reaching the station. The face is one
more client of the mirror for it
([docs/dccex_usb/README.md](docs/dccex_usb/README.md#the-monitors-stream)).
_Avoid_: websocket (the transport it rides), feed, channel, socket (what a
client of the mirror's port opens), the monitor (the page it is shown on)

**Link**:
Whether the station is answering, which is not the same as whether a socket is
open. The build goes with it
([docs/dccex/README.md](docs/dccex/README.md#what-it-publishes-back)).
_Avoid_: connected, online, the connection, up

**Monitor**:
The page the **stream** is shown on and typed into. What makes it a monitor is
that a person reads it: a throttle on 2560 is a **client**, not a monitor
([docs/ui/README.md](docs/ui/README.md#the-stream)).
_Avoid_: console, terminal, serial monitor, log (what the apps write to
stderr), the stream (what a monitor shows), the UI (the whole page)

**Decoder**:
The UI's pure function from one line of the station's `<…>` to one reading or
nothing. The monitor's **gloss**, the **band** and the **tile**s are made of
its readings
([docs/ui/README.md](docs/ui/README.md#the-stream)).
_Avoid_: parser, interpreter, translator (`dccex`), protocol handler, renderer,
formatter

**Gloss**:
The plain sentence the monitor shows beside a line the **decoder** knows. A
line it does not know gets none
([docs/ui/README.md](docs/ui/README.md#the-stream)).
_Avoid_: description, explanation, translation, tooltip, annotation, comment,
label

**Band**:
The organisation's word ([CONTEXT.md](https://github.com/rails49/.github/blob/main/CONTEXT.md)).

**Rail**:
The organisation's word ([CONTEXT.md](https://github.com/rails49/.github/blob/main/CONTEXT.md)).

**View**:
`control`'s word, owned by its
[ADR-0038](https://github.com/rails49/control/blob/main/docs/adr/0038-the-ui-is-one-app-with-views-of-one-railroad.md).
This UI's views are in
[docs/ui/README.md](docs/ui/README.md#what-is-on-it).
_Avoid_: page (the whole UI), tab, screen, panel, mode (what a track is set
to)

**Editor**:
Where the **script** view shows a railroad's script and a person changes it
([docs/ui/README.md](docs/ui/README.md#the-script)).
_Avoid_: box (the machine the apps run on), textarea, code pane, IDE

**Tile**:
One track's readings on the **monitor** view, one per track the station names
([docs/ui/README.md](docs/ui/README.md#the-tiles)).
_Avoid_: card, widget, panel, badge, stat, metric, gauge

**Image**:
What the apps here run as on the box, built from this repository's source at
one commit and named by it: `dccex:<commit>` for the mirror and the
translator, `dccex-ui:<commit>` for the page
([docs/dccex_usb/README.md](docs/dccex_usb/README.md#deploying-it-and-going-back)).
_Avoid_: version, build (the station's), release (firmware), tag (names a
release), the container (one running of an image), latest

**Cutover**:
When 2560 moved from `control`'s mirror to this repository's stack on the
layout box
([docs/cutover.md](docs/cutover.md)).
_Avoid_: migration, the switch, the swap (one step of a cutover), the window,
deploy (replacing both images with newer ones, `scripts/deploy.sh`), rollback
(going back on a deploy, which is not going back on a cutover)
