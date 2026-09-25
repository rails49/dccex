# The page

The UI for the command station: one page, served at `dccex.$BOX_DOMAIN` as a
label under the box's door, about the **station** at the end of the cable and
about nothing else.

**The page is here, the monitor is a full client of the mirror, the page says
what the station is doing, it lists what the station could be written with, and
it writes one of them.** `ui/` holds the band, the rail and the work pane, built and served the
way this page says (#3) — which is the tracer bullet, and it is the
installation everything below rests on. What is in the work pane is the
**tile**s, the **release**s under them and the **monitor** under those: the
station's conversation as it arrives, every line stamped with the time it
arrived, newest at the bottom (#4), and a box at the foot that types a whole
`<…>` message back (#6). The band carries its two readings and the tiles carry
the particulars, all of them made of what the station said and kept live by the
page's own polling (#7). The releases are listed newest first with the one on
the station marked (#8), and choosing one writes it onto the station — which is
the last thing here that needed a terminal (#9). What it says was decided in
rails49/dccex#1 and the tickets under that spec are each a part of it, as [the
cutover page](../cutover.md) was written ahead of its evening. What is already here besides is the other end: the
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
on the page is made of what the station said on the **stream**. How many
**client**s are on the mirror's port was the one that was not, and the page no
longer draws it, so what it asks the face for is the releases and a flash
rather than a reading (#111). The count is still the app's own business about
itself and the face still answers it at the address above.

It calls no third-party service. The releases are read by the app from its
configured source and handed on; the browser never reaches the release API, and
no module of the page names one — not a host, not a repository and not a query
([the mirror's page](../dccex_usb/README.md#the-face),
`tests/ui/test_releases.py`). Neither do the face's own sentences: a flash
turned down because the source could not be read says so without spelling it,
so the source does not arrive in the words the page shows either
(`tests/dccex_usb/test_firmware.py`, #94).

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

No emergency stop is drawn on the chrome. The one red on it is the link while
the station is not answering: LOOK.md keeps red on the chrome for stop or a
fault, and that is a fault. It wears `--stop` and `--stop-ink` and still says
`not answering` in words (#138).

Below 560px the band drops the track reading and keeps the link. A station
that is not answering makes the other reading meaningless, and a band that kept
the rails instead would show a power state nothing has confirmed since the link
went. 560px is this page's own number rather than a look rule, written in
`dccex-band.styles.ts` beside the rule it is about, and a browser is what does
it: `tests/ui/test_page_at_a_phones_width.py` loads the built page at 375px and
reads back a link with a size and a track reading with none (#127).

### The tiles

The station's particulars, at the top of the work pane (#7):

| Tile | What it reads | While the link is down |
| --- | --- | --- |
| link | a light: green while the station answers, red when it does not | red |
| build | the `G-` field of the station's banner | blank |
| track A · MAIN, … | the track's current in mA, or `off` | gone |

The light is the band's **link** reading made visible at a glance; it is in
the work pane because the chrome's red means a fault and nothing else, and a
green light has no token there.

**A tile per track the station uses**, by letter, with its mode (`<=>` →
`<= A MAIN>`). A track set to `NONE` gets no tile. A track reads `off` when the
station says its power is off (`<p0 A>`), whatever current was last measured
on it, and its current otherwise. The current is the station's own measure
(`<JI>` → `<jI 120 2 0 0>`, A first), asked four times a second and shown as
the mean of the last eight readings. The station reports one instantaneous
ADC sample per track, and with a loco running those scatter between under 20
and over 100 mA; their mean over two seconds is the current. A track the station has named but not measured reads blank, not
`0 mA`.

The build and the tracks go together when the link goes down, which is correct
rather than a gap: they are the station talking and the station is not
talking. The **build** fills again by itself when the station comes back and
says which one it is running, so a build from before a flash is never reported
as the one on the board (ADR-0008 d.3).

The page no longer shows how many **client**s are on the mirror's port. The
face still answers that at `/dccex-usb/clients`.

### The releases

Every **release** the **mirror** is configured to read, newest first, each
with its publication date and whether it carries a flashable asset — one with
a digest to check it against, which is what the face answers `flashable` for
(#8, #81). The one whose **tag** matches the build on the station now is
marked as such, so being up to date is something to see rather than to work
out. The list is collapsed under the tiles.

**The app fetches and the browser does not.** A UI talks to the bus, the store
and its own app's face and nothing else (the organisation's ADR-0002), so the
list is read by `dccex-usb` from its configured source and handed to the page,
which asks its own face for it on its own origin. **Where releases are read
from is that app's configuration and cannot be set from here**: the LAN carries
no authentication on purpose, and a payload naming a repository would let
anyone on the wifi choose what the command station is offered to run (control
ADR-0042). No module of the page names a host, a repository or a query, and
`tests/ui/test_releases.py` holds that shut. The sentences the face answers
with name none either — this page shows a refusal word for word (#66), so one
that spelled the source would be the URL on the page by another road; what a
turned-down flash says is which thing went wrong and which **tag** it was, and
where releases are read from is left on the box's log
(`tests/dccex_usb/test_firmware.py`, #94).

It is asked for once, when the page opens, and not on the poll. What the
station is doing changes under the eye and that is what the five-second `<s>`
is for; what the source carries changes when somebody publishes, and a page
that asked the release API through the face every five seconds would spend
somebody else's rate limit on an answer that is the same all evening. What does
change — which release is on the station — arrives on the banner and is read
off the **build**.

Three things about the list are the page's own and are decided here:

- **newest first is the page's ordering.** The face passes the source's list on
  as it came, because which one is newest is a question about the dates; the
  stamps are compared whole, so two releases published in one afternoon keep
  the order they were published in, and a release the source stamped nothing on
  goes under the ones that can be ordered and is drawn with no date;
- **the date is the day and not the moment.** A stamp is UTC and a reader is at
  the layout, so an hour drawn here would be an hour in a zone nobody asked
  about; it is `2025-09-14` rather than a month's name because this page is read
  in more than one country;
- **nothing is marked while the station is quiet.** The build goes with the
  **link** (ADR-0008 d.3), so a page that held one over would be claiming to
  know what is on a board it cannot see. A build the source does not carry marks
  nothing either: that is a station running something nobody published here,
  which is a true thing to show and not an error.

A release there is nothing to write from says so — *nothing here to write and
check* — and is listed all the same: a release exists whether or not anything
can be written from it, and a row that looked like the others would send an
operator to a tag the mirror would refuse. The row does not say which of the
two it is, because the face does not: `flashable` is false for a release
published with no firmware on it and for one whose firmware the source reports
no digest for (#81), and one sentence that holds for both is what the page can
say truthfully about either (#109). Whoever asks for the tag to be written
anyway is told which by the mirror's refusal (`firmware.py`).

A face that could not be asked says the releases could not be read, which is a
different sentence from a source that has published nothing — nothing said is
not nothing published (ADR-0009 d.2). An answer that carries entries and names
no release among them is the first of those and not the second: it is a
document the page could not read rather than a source with nothing on it, and
the app draws the same line on the same document at the other end of the wire
(`face.ts`, `face.py`, #95).

Choosing one flashes it, and the page sequences that itself (#9).

1. Say plainly what is about to happen — the station resets, the rails drop,
   every throttle loses it, it takes a minute or two — and get a yes.
2. Send the emergency stop.
3. Cut track power.
4. Ask the face to write the tag.
5. Show which step is running, so a minute of silence is not a hang.

**The order is the whole of it.** The stop goes first because a locomotive
coasting on dead rails is what is left if the power is cut under it, and the
write goes last because it is the step the station does not come back from for a
minute or two. A step that did not leave the page stops the sequence where it
is: the stream is the only way anything reaches the station from here, so a stop
that did not go is a railroad nobody stopped, and nothing is written after one.
What the operator is told names the step that did not go and is right about the
one before it: a stop that did not go leaves the railroad untouched, and a cut
that did not go leaves the locomotives stopped and the power still on, which is
a railroad nobody should walk up to thinking it is dead (#93).

The control is on the release's own row and only on the releases that carry a
firmware with a digest to check the write against (#81, #109) — a tag the
mirror would refuse is not a thing to offer. The warning opens under it and the yes is a press of its own
beside a cancel, because a sequence the operator declines is a flash that was
not asked for rather than one that was refused. The step is drawn under the row
rather than inside it, since the row can be shut while the station is away. And
while a sequence is running there is nothing to press: a second flash is a
second station reset.

What goes down the cable, in what order, and what is said at each step is
`ui/src/flash.js`'s — a module with no socket, no face and no DOM of its own, so
the whole of it runs under a bare node (`tests/ui/test_flash.py`). The drawing
is `ui/src/ui/dccex-releases.ts`'s, and what it flashes with is handed down from
the page: the same `send` an operator's typing goes up, so the stop and the cut
are marked as the page's in the monitor, and the face's own `flash`.

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
is that the release source could not be read, and not to go and retype a tag
that is perfectly good (#46). A second flash asked for while one is running is
refused and not queued.

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
  it has been scrolled up, so reading back does not fight the stream — including
  across a trim, where the lines it is measured from are the ones that go. It
  can be paused, and it can be cleared.

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
- a status line — the banner, the power on a track or on all of them, the
  display, a track's mode — is shown only when it says something different
  from the last one about the same thing. The measured currents (`<jI …>`,
  `<jG …>`) are never shown: they move on nearly every poll, and the tiles are
  where they are read. Every poll is
  answered with the same eight lines, and every open page polls. The readings
  still hear every line; it is only the monitor that leaves the repeats out;
- a stream that closed is opened again after two seconds, because everything
  that ends one is something that ends — the cut-off, an outage past its grace,
  the app restarting (ADR-0007 d.2). Nothing is asked for on the new one and
  nothing is replayed on it, so what the station said while it was away is not
  in it.

**The busiest line is the cheapest drawing of it** (#74). Two thousand lines
kept and the oldest dropped means that at capacity every arriving line shifts
the whole conversation up by one, and a list matched by position re-commits
every binding on all two thousand rows for that — per frame the station sends,
which is the case the monitor exists for. So every line carries a key the page
gives it when it keeps it, assigned once and never reused, and the rows are
drawn under those keys: the shift moves the rows the page already drew. The
key is the page's own and is nothing the line carries — a line and the
millisecond it arrived in are both ordinary to see twice on a serial port, and
two rows keyed the same would be one row. The drawing itself waits for the
frame the browser is going to paint, so everything that arrived before it is
drawn once, which is as often as a reader can see it. None of it changes what
is on the page: the monitor drew the right thing before and draws the same
thing now.

**And the reader who has scrolled up keeps their place across a trim** (#75).
The oldest lines are dropped at capacity, so what a trim takes is the top of
the list a scroll position is measured from: a reader holding still is holding
a distance from a front that just got shorter, and the line they were reading
comes up under them by the height of whatever went. Below capacity nothing is
removed and nothing moves, which is why this is the one thing about the view
that only goes wrong on a page that has been open a while — which is when
somebody is most likely to be reading back. So what the monitor holds across an
update is a row and where in the view that row sat, and it puts the view back
to wherever that row has got to: a row is carried up along with everything
below what went, so it is the same line in front of the reader afterwards for a
trim of any size, and for none at all the correction is zero. Browsers have
scroll anchoring that would do some of this — it is best-effort, it is off in
cases of its own, and the monitor turns it off on the scroller rather than rest
a promise on it (`overflow-anchor`, `ui/src/ui/dccex-monitor.styles.ts`). The
measuring is the monitor's and not the page's: the page decides how much
conversation to keep and the monitor is what has a viewport.

**And it can be held still, and emptied** (#125, stories 12 and 13). Scrolling
up already holds the view, but at capacity the page goes on dropping the oldest
lines, so on a busy station the line a reader is reading goes off the front
while they read it. **Pause** is what scrolling cannot do: while it is held
nothing on screen is trimmed. What arrives goes to a queue out of sight, with a
count on the monitor — "137 waiting" — and the queue has a cap of its own, a
quarter of what is kept, which is five hundred because two thousand are kept:
the quarter is arithmetic in the one module both numbers live in rather than a
sentence in three places and a sum nowhere (#152). Past it the oldest *queued*
lines go and the count says how many — "500 waiting, 12 dropped" — because a
gap is shown and never hidden: a queue that quietly forgot what it was holding
would be the page pretending the station was quiet
([ADR-0009](../adr/0009-the-decoder-is-a-pure-function-and-an-unknown-line-gets-no-gloss.md)).
Resuming appends the queue in the order it arrived and the usual capacity trim
applies from there. A line typed at the box while the view is held goes up the
stream like any other and waits behind the pause with the rest: the view is one
thing, and letting the operator's own line through would be the trim the pause
exists to stop. **Clear** empties the conversation, and any queue behind
it, and nothing else. Neither of them stops the stream, the polling or the
tiles, and neither of them says anything to the station: they are the view and
not the conversation, so the band and the tiles go on saying what the station
is doing while a reader holds the monitor still.

Two things a full queue is owed, and did not get until #144. **A line the
queue drops is forgotten as well as counted.** A status line is shown only when
it says something new, and one that was pushed off the front of the queue never
reached the conversation at all — so a `<p1>` dropped while the view was held
left every later answer about the power looking like a repeat, and the monitor
never said the power came on (#142). What went is forgotten, and the next poll
that answers for that subject is news again. **And the gap is marked where it
is.** The "500 waiting, 12 dropped" count goes away with the pause that made
it, so a resume used to leave twelve lines missing out of the middle of a
conversation with nothing at all saying so; now one note goes in where the gap
is — *12 lines dropped while paused* — ahead of the lines that survived. It is
the page's own note and is drawn as such, in the page's face and with no stamp,
no mark and no gloss, because none of those would be true of it; it is trimmed
and cleared like any other entry, and a resume that dropped nothing adds none.

The conversation is the page's — the band and the tiles are made of the same
bytes — and everything that happens to it is `ui/src/monitor.js`'s: what is on
screen, what waits behind a pause, what the queue dropped and what each subject
last said are one value there, and a line arriving, a press of the pause and a
press of the clear are three pure functions of it, run rather than read (#144).
The page holds the value, hears every line into the readings whether the view
is held or not, and calls them; the monitor draws the two controls and is
handed what they do the way it is handed its lines and its sending.

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

**The pairs are run rather than read.** What is still read off the sources is
read there because the gate is Python and has no browser in it. These cannot
be: a sentence an operator is shown is worth nothing asserted
against the source that would produce it — and so is a rule about what goes
down a cable to a command station, and so is what the band says about the
railroad's power, and so is the order the releases an operator picks from come
out in, and so is the order a flash does things to a railroad in before it
writes — and ADR-0009 d.3 asks for the pairs themselves. So
`tests/ui/test_decoder.py` puts every line the page glosses and every near miss
through the real function under `node`, by way of `tests/ui/gloss.mjs`,
`tests/ui/test_message.py` puts every spelling an operator may type through the
real function the same way (`tests/ui/message.mjs`), and
`tests/ui/test_readings.py` puts whole conversations through the readings and
reads the band and the tiles back (`tests/ui/readings.mjs`), and
`tests/ui/test_releases.py` puts a `releases` document through the reader that
answers whether the page could read it at all and what the face answered
through the listing, and reads the release rows back (`tests/ui/releases.mjs`),
and
`tests/ui/test_flash.py` puts a flash through the sequence and reads back what
went down the cable, in what order, and what the page said while it did
(`tests/ui/flash.mjs`), and `tests/ui/test_stream.py` puts a page's own address
and a conversation arriving on the socket through the rules that answer where
the stream is and where a line ends (`tests/ui/framing.mjs`), and
`tests/ui/test_monitor.py` puts a scroller, a time and whole conversations —
lines arriving, a pause, a resume, a clear — through the rules that answer
whether the reader is at the bottom, what the stamp beside a line reads and
what is on the screen afterwards (`tests/ui/monitor.mjs`). The last two cannot
either, and were read off
their sources only for as long as there was no node here to run them with: a
framing that kept its delimiter, a scheme picked the wrong way round and a
stamp an hour out all leave a module saying every right word, which is what
reading one can be held to (#78). What that asks of a machine is a node and
nothing else — no packages, no bundler, nothing fetched, no DOM — and it is not
asked of every machine the gate runs on: these checks carry the `node` marker,
`scripts/check.sh` does not collect them, and the workflow runs them in a job a
pull request requires (#101). Where they do run, a node that is not there is red
rather than skipped, as everything else a gate needs is. It is why
`ui/src/decoder.js`, `ui/src/message.js`, `ui/src/readings.js`,
`ui/src/releases.js`, `ui/src/flash.js`, `ui/src/framing.js` and
`ui/src/monitor.js` are the seven modules of the page written as JavaScript
with their types in JSDoc: `tsc` checks them as strictly as the rest
(`ui/tsconfig.json`), and a bare node can still run them.

What is left in the modules those came out of is what needs a browser — the
socket, its timer and `window.location` in `ui/src/stream.ts`, the rows, the
box at the foot and the rectangles a held row is measured with in
`ui/src/ui/dccex-monitor.ts`, and the `fetch`, the status and the envelope in
`ui/src/face.ts` — and that is still read rather than run, for the reason the
next paragraph gives. Reading a `releases` document is not part of it and came
out to `ui/src/releases.js` for that reason: which of two sentences an answer
gets is a rule, and a rule is worth nothing asserted against the module that
would apply it (#95).

**And the components are mounted** (#126). What the band, the tiles, the
release rows and the monitor *draw* was read off their sources for as long as
there was nothing here to mount them in — and a source-text check passes on a
page that never rendered and goes red on a harmless rename, which is the
opposite of what a check is for. So `vitest` and `happy-dom` are dev
dependencies of `ui/`, the five cases #1 named are asserted against a DOM
(`ui/test/band.test.ts`, `ui/test/tiles.test.ts`, `ui/test/releases.test.ts`,
`ui/test/flash.test.ts`, `ui/test/monitor.test.ts`), and each source-text check
they replace went with them. **That DOM is not in the gate.** It is an install,
and `scripts/check.sh` runs with no node on the machine at all; these run in the
workflow's `node` job beside the modules a bare node runs, which is the same
split and the same reason (#101, `.github/workflows/ci.yml`).

What a mounted component still cannot answer is layout: happy-dom draws no
boxes. So the widths the band drops a reading at, the `min-height` a blank tile
keeps and how loud a **gloss** is beside the bytes are held against the
stylesheets as before (`tests/ui/test_band.py`, `tests/ui/test_tiles.py`,
`tests/ui/test_monitor.py`), which is the same cost the look values check names.

**A browser answers it, for the width it matters at** (#127). The rules that
are about a phone were written and never rendered, so the built page is loaded
in a real Chromium at 375px and at a desktop width and measured there:
`tests/ui/test_page_at_a_phones_width.py`, under the `docker` marker, in the
job that already builds and serves that image. It is not a second toolchain
here either — the browser is a container beside the page's, handed a driver,
and nothing is added to `pyproject.toml` or installed on the machine. What it
does not reach is what is not about a width: a stylesheet check is still where
a rule is held as written, and this is where it is held as drawn.

**Sending is held at the other end too.** What a page types is one more
client's bytes on the mirror's port, so two monitors typing at once is the
interleaving rule `tests/dccex_usb/test_face.py` runs against a pty — two whole
messages at the device, in one order or the other, on a machine with no command
station attached.

The pause, the clear and the queue behind a pause are held the same way and in
the same place: what the queue holds, what it drops and what it says, that the
page queues rather than trims while it is paused, that resuming appends through
the one trim there is and marks the gap a full queue left, and that a clear
empties the conversation and the queue and forgets nothing else are all run
under a node (`ui/src/monitor.js`, `tests/ui/monitor.mjs`). They were read off
`ui/src/ui/dccex-app.ts` until #144, which is what let two of them be wrong in
the source while every word of it read true. What is left to read there is
where the rules live and what the two controls reach, which no DOM and no
conversation can answer; the controls themselves are pressed on a mounted
monitor (`ui/test/monitor.test.ts`), handed the facts a page would hand it.

**The page is what polls** (#7). The station volunteers a banner and a `<p…>`,
and an idle one says nothing; on a box with no **translator** running, nothing
else asks. So the page asks on its own schedule — `<JI>` four times a
second, and `<s>` and `<=>` every fifteen seconds, because every client on the port receives
the eight lines `<s>` is answered with — up the stream, through the same send an operator's typing goes through, though
the poll itself is not written to the monitor — and the mirror goes on
originating nothing
([ADR-0010](../adr/0010-the-page-polls-and-the-mirror-originates-nothing.md)).
Five seconds without a word, which is twenty polls, and the **link** is down.
The readings are worked out again on a one-second tick as well, because the
link going down is the absence of a line rather than the arrival of one; and a
page that has left stops asking, because a conversation that is quiet when
nobody is watching is the correct conversation (ADR-0010 d.4).

**The first one is asked when the stream is open, not when the page joins**
(#82). Opening a stream dials a socket, and a socket that is connecting cannot
be written to: the poll that used to go in the line after `open()` was refused
and went nowhere, so nothing had been asked and nothing had answered until the
interval came round, and every load of the page spent its first five seconds
saying a healthy station was not answering with the **build** tile blank. The
stream hands the open up the way it hands a line up, and the page asks there —
which covers a reopen too, since the socket the reopen timer dials says it is
open like any other. The schedule is untouched and is started once, where the
page joins the document, so a stream that drops and comes back leaves one
poller and not two.

**No reading the poll feeds is a request** (#111). The count of **client**s
was the one that was: it came off the face rather than off the stream, and
which order a browser hands back the answers to a dozen requests in is the
browser's, so an answer from an older ask could put a count from a minute ago
on the tile and leave it there until another happened to arrive in order.
During a flash it was a dozen — the face sits inside esptool for the length of
a write while the schedule goes on firing. The asks were numbered for it and an
answer that was not the newest ask's was dropped where it arrived (#88). The
page stopped drawing that count and the numbering went with the ask it
guarded: every reading here is now made of lines off the stream and of the
clock, and both of those only go forward. What the page asks the face for is
the releases, once where it joins the document, and a flash, on a press —
neither of them on the schedule (`tests/ui/test_releases.py`).

**Nothing typed is held for it.** A message an operator typed while the stream
was down is a command to a command station, and one arriving seconds later,
after the page has moved on, is worse than one that never went: `send` returns
nothing, the box at the foot says so, and the stream keeps no queue (#6). The
poll is the exception because it is not held either — it is stateless, so the
page asks again rather than the stream remembering.

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
a component's own template, in `ui/src/page.css` or in the page's own markup is
red, because each of those paints and none of them is that one place (#60,
#85). It reads the copy and the
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
can move. The mirror's image is pinned the same way and points here for the
argument rather than repeating it (`deploy/Dockerfile`, #96).

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
did not start is not its to do. The other guard — that nothing left in a shell
can point those commands at a project nobody here named — is a `monkeypatch`
over the environment the commands are run in and needs no daemon at all, so it
is asserted in `tests/ui/test_commands_run_clean.py`, which the gate does
collect (#112). That environment is on every command the check runs and not
only on the `docker compose` ones: the plain `docker` helper the two checks
share takes an environment, the compose check hands it one at each call, and
the same daemonless module holds that what the helper is handed is what the
process it starts runs in (#113).

**And it is laid out at a phone's width.** The page is read on a phone held at
the layout, and until #127 nothing here had drawn it at one:
`tests/ui/test_page_at_a_phones_width.py` runs the image this section is
about, loads it in a Chromium at 375px and at 1280px, and holds five things
there — no horizontal scroll at either width, the band keeping the **link** and
dropping the track reading below 560px, the command box inside the viewport and
a line typed into it coming back out of it, a release row with a long **tag**
wrapping with nothing off the side of it, and the track reading back at a
desktop width, which is what keeps the narrow claims from passing on a page
that drew no band. There is no face behind the page in that job, so the
**stream** never opens and the link reads as not answering — the state a page
with nothing behind it draws, and enough for layout. The one thing stood up is
the release list, because rows are what the wrap rule is about and that state
has none: the browser answers that one request, and the rows go in through the
page's own fetch. It carries the same `docker` marker and the same no-daemon
rule as the two checks above it.

## What is not on it

- **Anything about a railroad.** No turnout names, no roster, no run state —
  none of them is a thing a command station says. Somebody wanting them wants
  `control`'s UI, which is next door on the layout box.
- **Commanding track power**, beyond the flash sequence's own step. The band
  presses nothing — there is no button on it, nothing listening for a press and
  no form — and no emergency stop is drawn on the chrome. Its one red is the
  link while the station is not answering, which is a fault (#138).
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
  entries. It is a collapsed row as of #8, and what would change it is somebody
  reading a long one on the box;
- narrow widths are drawn in a browser as of #127, and not all of them are
  asserted there. What is: no horizontal scroll, the band dropping the track
  reading below 560px, the command box on screen and typed into, and a release
  row wrapping rather than running off the side. What is not: the tiles onto a
  second row, and the flash's warning taking its own line above the two presses
  that answer it. And what the check drives is a Chromium at a phone's width
  rather than a phone — a real one was considered for #127 and left out, so the
  thing that is still open is somebody holding one up to it. Mounting the
  components settled none of it and could not: happy-dom does no layout
  (#126).

What each tile reads while the link is down was the third and is settled above,
by ADR-0008 d.3.
