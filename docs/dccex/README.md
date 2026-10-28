# DCC-EX

The first translator under `layout`
([ADR-0043](https://github.com/rails49/control/blob/main/docs/adr/0043-the-layout-interface-is-a-core-app-and-hardware-hangs-under-it-by-address.md)):
a thin app, `dccex`, that subscribes to the **device vocabulary** and turns it
into the DCC-EX command station's own language, and publishes back what the
station reports. It is the one app in this repository on the bus.

**This page is the only place in the repository where that language meets the
bus**: what this app sends and reads for each row of the device vocabulary. What
a command or a line means is in the rails49 fork's [command
reference](https://github.com/rails49/CommandStation-EX/blob/HEAD/docs/commands.md).
Every other component is oblivious to what powers the layout: nothing above the
layout interface expects DCC-EX, or Lenz, or NCE, or anything else — those are
one family of devices among many. The `<…>` syntax appears on no bus topic, in
no other package and in no normative document
([BUS.md](https://github.com/rails49/control/blob/main/docs/BUS.md#device-vocabulary)
is the contract, and a test keeps protocol names off the pages that are not
about hardware). A different command station gets a different translator, or
reaches the system through JMRI, and nothing else moves.

Getting the mapping below wrong is a bug in this app and nowhere else.

## What it connects to

TCP **2560**, which the `dccex-usb` mirror serves from the USB device
([docs/dccex_usb/README.md](../dccex_usb/README.md), the other app in this
repository and the service beside this one on the box). Not the USB device
directly: `dccex-usb` owns it, and the port is what lets JMRI and hand-held
throttles share the same command station. This app is one client of that port
beside the others, and every client is a peer — nothing in the firmware ranks
them.

*Subscribes* `tc49/layout/state/wanted/#`, `tc49/layout/alive_confirmed` and
`tc49/layout/state/clock`. *Publishes*
`tc49/layout/state/device/track` and `tc49/layout/state/device/link/<id>`,
where the id is the one this app is started with — `dccex`, the package's
name, where it is given no other. The id is whatever the publisher calls
itself, a value and not a contract: it appears in no drawing, no configuration
and no list of ours (control ADR-0059). A script posts on
`tc49/ui/state/text/<name>` ([below](#what-a-script-is-written-with)).

**It acts on every address it hears**, and there is no ownership table
anywhere. An address names no system — it is the string the drawing carries
and the hardware answers to
([ADR-0059](https://github.com/rails49/control/blob/main/docs/adr/0059-the-bus-is-a-broker-each-app-is-its-own-process-and-the-bridge-is-deleted.md))
— so every point and signal address is this app's, as every traction and
function address is, a decoder answering to the number it was programmed with
whoever sends the packet
([ADR-0045](https://github.com/rails49/control/blob/main/docs/adr/0045-the-railroad-owns-cars-and-a-train-is-an-ordered-list-of-them.md)).
What this station has no packet for — a turnout numbered outside the accessory
range — falls away in the mapping below. An address nothing answers to does no
harm, as a packet nobody picks up does.

**On connect it runs the script's `start`, then applies the retained desired
state, power excepted.** The desired values are the whole picture, so there is
no handshake and no session state to agree. The power is the one value a
connect does not carry out: after a station or a translator restart the rails
stay as the station reports them and come back when a person presses ON
(ADR-0013 d.6). Every other value replays through its handler, in the order
the topics were first heard.

**Between the two it asks `<=>` and `<JG>`, once.** What each track is set to
and the most each may draw, which are the two fields a **journal** line about
a district carries beside it (below). After `start`, because `start` is where
a railroad sets both: asking before it would read back the picture the script
has just replaced. Neither is in the poll — the station broadcasts a mode the
moment it changes, and a limit changes when a script does.

**A station restart is handled as a connect.** On every connect this app sets
stash `32000` with `<JM 32000 1>`, before `start` and the replay, and the poll
reads it back. A boot clears the stash, so `<jM 32000 0>` is a station that
has restarted and runs `start` and the replay again — a reset can be shorter
than the ten polls that lower the link, so the link going down is not what
says it
([ADR-0021](../adr/0021-a-restart-is-a-stash-the-boot-has-cleared.md)). The
boot line is not read: its text, row and port are part of no documented
interface, and a firmware that printed another form left a restart unseen. A
station whose firmware has no `<JM>` answers nothing, and ten polls of a link
with no answer are logged once (ADR-0021 d.5).

## The script

**`--store <url>`** is where `control`'s store serves the documents, and the
one route this app reads is the **script**: a railroad's Python document,
one per railroad, at `GET /scripts/<railroad>`, answering
`{"script": "<railroad>", "text": "..."}`
([ADR-0015](../adr/0015-the-script-is-a-railroads-document-in-the-store.md),
[control#586](https://github.com/rails49/control/issues/586)). Which railroad
that is comes off the retained `tc49/layout/state/railroad` and never off a
flag: the station this app holds is the same station whichever railroad is
loaded on it, and the script is the one thing about it that is the railroad's.
The row's `built` changes nothing here: on `built: false` this app runs the
named railroad's script as on `built: true`
([ADR-0028](../adr/0028-a-railroad-that-is-not-built-still-runs-its-script.md)).

The script is where this railroad's `<…>` that the bus has no word for is
written — which mode each track is set to, what current each may draw, what a
turnout throwing does to a track or a signal
([ADR-0013](../adr/0013-a-railroads-own-station-commands-are-a-script-in-the-translator.md)).
It replaced the startup file, which could only send raw commands after the
first `<1>` of a session (ADR-0013 d.9).

A **handler** is a function in it, run when its **event** happens. Three
kinds, and they are never confused. A handler keyed on a **desired value** runs
in place of the command this app would have sent for it, and sends that too
only by asking. A handler keyed on something the **station reported** runs
after the fact and replaces nothing. A handler keyed on **`start`** runs on a
connect and after the station restarts, before the replay, and sets what a
restart loses: track modes and current limits (ADR-0018).

### The sample

This is the interface, and it is `dccex/sample.py` in this repository: the
tests load it, fire events and assert the bytes sent, and it is what a
railroad with no script of its own opens with on the page, commented out, so
that applying it unchanged is a railroad whose script does nothing
([#185](https://github.com/rails49/dccex/issues/185)).

```python
# Handlers for this railroad's DCC-EX station (ADR-0013, ADR-0015, ADR-0018).

'''
Event listeners:
* `on(row, address=None)` keys a handler on an event.
* Valid rows are
    start, (connected, or the station restarted)
    power,
    point,
    signal,
    traction,
    function,
    reported_power, (reported by station)
    reported_point,
    reported_district, (a district's state, mode and limit)
    reported_message. (every message the station sends)

Handlers:
* ordinary Python functions
* run in place of the command the translator would have sent;
  `t.default()` sends that command as well.
* `t.send(text)` sends one raw message.
* `t.text(name, value)` sets the text the widget `name` shows.
* `t.point(address, position)` reports where a point lies.
* `t.desired(row, address=None)` reads the desired value.
* `t.reported(row, address=None)` the last reports;
* `t.message` is the message on reported_message.
* a value the bus has not given reads None.
* return quickly: a handler that blocks holds up the translator.
'''


@on("start")
def configure(t):
    # configure tracks:
    #      A Claro
    #      B Programming
    #      C Auto reverse section in ramp
    #      D Airolo (switches polarity depending on how wx310 crossing is set)
    for district, mode in {"A": "MAIN", "B": "PROG", "C": "MAIN_AUTO", "D": "MAIN_AUTO"}.items():
        t.send(f"<= {district} {mode}>")
    # set current limits
    # B at 250 mA is NMRA's limit for service mode (S-9.2.3)
    for district, ma in {"A": 2000, "B": 250, "C": 500, "D": 1500}.items():
        t.send(f"<JG {district} {ma}>")


@on("point", "12")
def wx310_crossing(t):
    # set correct track polarity depending on turnout position
    t.default()
    if t.desired("point", "12") == "thrown":
        t.send("<= D MAIN_AUTO_INV>")
    else:
        t.send("<= D MAIN_AUTO>")


CURRENT = {}  # mA per district, from the station's <jI ...>
ASKED = [False]  # whether the next <jI ...> is the answer to our <JI>


def show(t, district):
    # show a district on the text widget track-<district>:
    #      green on, amber near its limit, bold red tripped,
    #      and the current while it is powered
    d = t.reported("district", district)
    if d is None:
        return
    state = "?" if d.state in (None, "unknown") else d.state
    shown = f"{district} {state}"
    if d.state in ("on", "alert") and district in CURRENT:
        shown += f" {CURRENT[district]} mA"
    if d.mode and d.mode.endswith("_INV"):
        shown += " inverted"
    colour = {"on": "32", "alert": "33", "tripped": "1;31"}.get(d.state)
    if colour:
        shown = f"{chr(27)}[{colour}m{shown}{chr(27)}[0m"
    t.text(f"track-{district}", shown)


@on("reported_district")
def show_district(t):
    show(t, t.address)


@on("reported_message")
def currents(t):
    if t.message.startswith("<jM 32000"):
        # the answer to the translator's poll, once a second
        t.send("<JI>")
        ASKED[0] = True
    elif t.message.startswith("<jI ") and ASKED[0]:
        # the dccex page asks <JI> too; take one answer a second
        ASKED[0] = False
        for district, ma in zip("ABCDEFGH", t.message[4:-1].split()):
            CURRENT[district] = int(ma)
            show(t, district)


# @on("point", "20")
# @on("point", "21")
# def signal_5(t):
#     t.default()
#     closed = t.desired("point", "20") == t.desired("point", "21") == "closed"
#     t.send("<A 5 2>" if closed else "<A 5 0>")
```

**The values in it are this installation's**, not defaults and not a
recommendation: what a district can take is what is wired to it, and which
track the reversing loop is on is this railroad's wiring. The command
spellings are the station's. `<JG district mA>` is in the rails49 firmware
([rails49/CommandStation-EX](https://github.com/rails49/CommandStation-EX)).

### What a script is written with

`on(row, address=None)` registers a handler. The rows are `start` for the
station as this app has not set it, `power`, `point`, `signal`, `traction` and
`function` for the desired values, and `reported_power`, `reported_point`,
`reported_district` and `reported_message` for what the station said. The
address is the string the bus carries and the hardware answers to; left out,
the handler runs for **every** address of its row, which is the only form
`start`, `power` and `reported_message` have. Two of these stack on one
function, which is how one signal is set from two turnouts. A row that is no
event, or an address that is not a string, is a script that does not load.

The handler is handed one argument, the event, and may do six things with
it:

| written | does |
| --- | --- |
| `t.default()` | sends this app's own command for the value that fired, once per firing whoever asks; nothing at all for `start` or a report |
| `t.send(text)` | sends one raw `<…>` message, as typed |
| `t.text(name, value)` | posts `value` as the text widget `name` shows, on `tc49/ui/state/text/<name>`: raw UTF-8, retained, and only where it differs from the last text posted under that name. A name that is empty or holds `/`, `+` or `#` raises |
| `t.point(address, position)` | reports that the point lies `closed` or `thrown`, on `tc49/layout/state/device/point/<address>`: retained, and only where it differs from the last position reported for that address. It sends nothing to the station, and `t.reported` still reads what the station said. An address that is empty or holds `/`, `+` or `#` raises, and so does any other position |
| `t.desired(row, address=None)` | reads the desired picture: a position, an aspect, a speed, a function's bit, or the word the power is wanted in. `None` where the bus has not said |
| `t.reported(row, address=None)` | reads the last reports: `power` by the track the station named — the empty address on the line that names none — `point` by the id it named, and `district` by its letter. `None` where the station has not said this session |

`t.address` is the address the event fired for, and `t.message` the station's
message on `reported_message`. The text row and the point row are the two
things a handler publishes on the bus (ADR-0013 d.4 as amended by
[ADR-0029](../adr/0029-a-script-posts-text-and-hears-what-the-station-says.md)
d.1 and [ADR-0030](../adr/0030-a-script-reports-where-a-point-lies.md) d.1).
The rows `reported` reads are `power`, `point` and `district`, the verb
carrying what the event names spell out.

**A district's record** is what `reported_district` fires on a change of and
`t.reported("district", X)` reads: `state`, `mode` and `limit`, each `None`
where the station has not said (ADR-0029 d.2). `state` is `on`, `off`,
`tripped`, `alert` or `unknown`, with a trip and an alert read as
[the mapping](#the-mapping) reads them. `mode` is the word `<=` takes, so a
reversed auto-reverse district reads `MAIN_AUTO_INV` and a joined PROG track
`MAIN`. `limit` is in mA. When the link goes and when the railroad stands down,
every district a record was reported for reads `unknown`, so a widget does not
go on showing a reading nobody can take.

**`reported_message` fires on every message**, the poll's answers included,
about seven a second on this railroad (d.3). A need the other rows do not
cover is a script reading the station's own words. The sample reads each
district's current this way: it sends `<JI>` on each answer to the poll's
`<JM 32000>` and reads the first `<jI …>` after it (#345).

**A handler must return quickly** (d.4). It runs on this app's loop, which
also sends the `<G 3>` the station needs every 3 s to keep the power on.
Nothing stops a handler that blocks.

**A handler sets everything it depends on each time it runs, from the desired
picture** (d.5). Point 12's handler above sets district D's whole mode and
turns D back on where the station last reported it on, rather than relying on
what `start` or an earlier handler left. A restart forgets the station's
reports, so a replay after one leaves D off (ADR-0018 d.3).

**`start` runs before the replay**, on a connect, on `<jM 32000 0>`, and when a
first script loads with the link up
([ADR-0024](../adr/0024-a-script-that-arrives-after-the-connect-runs-start.md)),
so a point handler that sets a district's mode runs after `start` set them all
(ADR-0018 d.3). `<JM 32000 1>` goes out before `start` itself, so a station that
restarts in the middle of those lines is one the next poll still reads as
restarted ([ADR-0021](../adr/0021-a-restart-is-a-stash-the-boot-has-cleared.md)
d.2).

**The power handler runs on every value of the row** — `on`, `off` and the
stop — and on every ON rather than only on a change from off (d.7). There is
no transition kept here; a handler that wants only the ON reads
`t.desired("power")` and says so itself.

**A report fires on a change.** The poll below makes the station restate
every track's power once a second, and a handler on every one of those
answers would be a handler on the clock; it runs where the value differs from
the last one heard (d.3). Everything the station told us goes with the link,
so the first thing said on the next one is a change. Power, turnouts and a
district's record are the reports that fire on a change. A turnout's report
is the station's own faked answer to a throw
([ADR-0022](https://github.com/rails49/control/blob/main/docs/adr/0022-a-symbol-carries-its-hardware-address.md)),
read for a script and for nothing else — it reaches no bus row — and it is
how a throw from JMRI or a hand-held throttle reaches a railroad's own
commands at all.

**A handler that raises is logged, and the default is sent** unless the
handler had already called it (d.8, as extended by ADR-0015 d.4). A script is
a person's Python and anything at all comes out of it; the turnout the layout
asked for is thrown either way, and whoever has to fix the script reads the
log.

### A script that is not there, and one that will not load

**No script (`404`): the defaults.** A railroad whose store has no document
for it sends exactly what this app sent before there were scripts.

**A script that raises on load, or a store that has not answered: no
handlers.** OFF, STOP and speeds are carried out; **power ON is refused**;
and the link row's `detail` says why, beside what the station is doing
(ADR-0015 d.4). Track modes and current limits are the script's, so a
railroad whose script this app has not got is one whose rails may not be made
live. It keeps asking, and the reason leaves the row when a script loads.

**Once a script is loaded, a fetch that fails changes nothing.** The script
keeps running. A store that goes away does not take the railroad with it.

**A new text ends the process.** The script for the current railroad is
fetched again every few seconds and compared with the one running; a text
that differs stands the railroad down, as every exit does, and the process
ends for compose to restart (ADR-0015 d.3). So a script applied on the page
takes effect from power off at the next ON, which is what a track mode and a
current limit have to be set from. Nothing is reloaded in place. A railroad
change that gives the same text, or no script both times, changes nothing:
the comparison is the text and never the name.

## The mapping

| desired | sent |
| --- | --- |
| `wanted/traction/<addr>` `speed` | `<t addr step dir>` — the fraction scaled to 0–126 and the sign taken as the direction; `speed 0.0` sends step 0 |
| `wanted/point/<addr>` `position` | `<a addr sub act>`, a stateless accessory packet; `thrown` writes `1` |
| `wanted/signal/<addr>` `aspect` | `<A addr aspect>`, the extended accessory packet the head's wiring expects |
| `wanted/track` `on` | `<1>`, which reaches every track the station has |
| `wanted/track` `off` | `<0>` |
| `wanted/function/<addr>/<n>` `value` | `<F addr n 0\|1>`, the boolean as the bit — every value the row carries is one the station can be told |
| `state/clock` `time`, `speed_up` | `<JC m r>`: `m` is `time // 60`, the minute of the day, and `r` is `speed_up` rounded and held to 1–63 |
| `alive_confirmed` | `<G 3>`, once each time it is published while the link is up |

Every row but the last is a pure function in `dccex/commands.py`, asserted as
"this value in, these bytes out" with no socket and no hardware. The last is
the constant `commands.HOST_TIMEOUT`.

The station cuts track power 3 s after the last `<G 3>`
([rails49/CommandStation-EX#5](https://github.com/rails49/CommandStation-EX/issues/5)).

**A speed is a fraction and a step never leaves this app.** The magnitude is
the fraction of that locomotive's maximum and the sign is which way it runs
along the track, so `1.0` and `-1.0` are one step and two direction bits, and
a fraction past the range is full speed and never more — there is nothing
above a maximum to ask for. The station remembers the speed in a slot and
re-sends it forever as a reminder packet, which is why the lock below matters.

**A point address is the accessory number a throttle shows**, `1` upward, and
this app splits it into the packet's decoder address and sub-address, four to
a decoder. It is sent as `<a>` and never as `<T>`: `<T>` would put a turnout
table inside the station and answer with a position the station faked, and
`align` carries the points its transit needs every time so that a translator
throws what it is told and holds no table
([ADR-0031](https://github.com/rails49/control/blob/main/docs/adr/0031-the-layout-carries-the-points-a-transit-needs.md)).

**What an aspect is worth to a head is wiring**, not contract: `stop` is `0`,
which the extended accessory packet reserves for stop, and `caution` and
`clear` are `1` and `2`. An aspect this table does not name is one no head
here is wired for and sends nothing.

**A function is a switch.** The station's `<F>` takes `0` or `1`, so the two
values a model may leave unstated are the two that reach the wire; a value from
a longer list — the `low` and `high` of a three-position vacuum — names a
state this hardware has no packet for, and nothing is sent.

**The fast clock is sent once a fast minute.** `layout` says it once a real
second; `<JC>` goes out only where the minute or the rate differs from the last
one sent. The station holds the rate in an `int8` and RCN-122 allows 0–63, 0
being stopped, so a running clock is never sent as stopped. On connect and
after a restart the clock the bus holds goes out after the replay; with none
held, nothing does. A railroad load clears the row, and nothing is sent for
that; the next railroad's first clock is sent whatever the last one was. The
clock goes one way: the `<jC>` the station broadcasts, for this
app's `<JC>` or another client's, publishes nothing on the bus. No script
handler is keyed on the clock; a `<jC>` reaches a script as `reported_message`,
as every message does. The journal and the monitor treat `<jC>` as any other
line, and the page glosses `<jC 390 4>` as `fast clock 06:30 ×4` (#348).

Two rules are not a row of the table.

**No lock is asked for.** The station has an emergency-stop lock in later
firmware, `<!P>` until `<!R>` with `<!Q>` to ask, and this app sends none of
them. Below the version that has the lock, the `!` opcode takes no suffix, so
`<!P>`, `<!R>` and `<!Q>` are all read as `<!>` and none of them says so. That
is what made a `<!Q>` in the poll an emergency stop once a second, and every
train move a few centimetres and stand
([control#463](https://github.com/rails49/control/issues/463)).

**A trip is read from the station's diagnostics.** The station cuts a district
and prints `<* TRACK B FAST OVERLOAD … *>`, `<* TRACK B POWER OVERLOAD … *>`
or `<* TRACK B FAULT PIN detected … *>` to USB, and the mirror passes every
USB line to every client. The first is the Guard's cut, and on rails49 it is
most of them: every DCC track is guarded while powered, and that line comes with
no `ALERT` before it (#251). The district is tripped until `<* TRACK B NORMAL
… *>` or `<p1 B>`, which the station prints only for a district that is on; a
commanded OFF and a lost link end every trip. Against the station's own TCP port
no such line arrives
([ADR-0016](../adr/0016-a-trip-is-read-from-the-stations-diagnostics.md) d.3 as
amended).

**The station is polled with `<s>` and `<JM 32000>` and nothing else**, and
the answers are what the link is measured by. Once a second `<s>` makes the
station restate every track's power and `<JM 32000>` reads the stash a restart
is read off (above); ten of those questions going unanswered is what says the
station has stopped answering at all, below. Nothing else goes in the poll, and
both of these only ask. A poll runs for as long as the link does, so a command
in it that a station acts on rather than answers is acted on for as long as the
railroad is up, and a station says nothing about a command it does not know.

## What it publishes back

**`device/track`** is folded from what the station says and never from what
this app commanded. `on` where at least one district is powered and not
tripped; a district that is off, such as one this railroad does not use, says
nothing about the rest. A district near its limit (`ALERT`) counts as powered
until `NORMAL`; otherwise its digit decides. The row is `on` or `off` and
nothing else. A lock the station reports (`<!PAUSED>`) does not change it;
`reason` names it, `emergency stop locked at the station`, after any tripped
districts. A station that has said nothing reads `off`, which is the
direction a state topic must fail in
([control#181](https://github.com/rails49/control/issues/181)), and a link
that goes takes the reading with it: a district that tripped while this app
was away would otherwise stand as an observation nobody made.

**`device/link`** is `up` while the station **is answering**, `down`
otherwise, with `detail` carrying what a person would want to read, on the row
the app's id keys. An open socket is not a command station — `dccex-usb`
accepts a client with the serial cable unplugged — so the link is not called
good until something has come back on it. It goes on saying `down` for the
whole outage, which is where a broken link becomes visible: at runtime, to a
person who can act on it, and not in a gate that would need a powered layout
to pass
([ADR-0050](https://github.com/rails49/control/blob/main/docs/adr/0050-broken-hardware-is-reported-never-worked-around.md)).
The same words go on `device/track` as its `reason` while the station is
unreachable, so a person reading why the railroad is dark reads it off the
supply itself rather than off a second row. Otherwise, while a district is
tripped, the `reason` names it: `district B tripped`, `districts B, C
tripped` (ADR-0016 d.5).

**A script that will not load rides on the same `detail`**, said beside what
the station is doing, and leaves the word alone: the link is the station
answering, and a document that will not compile is not the station being away
([ADR-0066](https://github.com/rails49/control/blob/main/docs/adr/0066-the-link-is-the-station-answering-not-the-socket-being-open.md),
ADR-0015 d.4). That is where a person reading why the
railroad will not come on reads it — on the row, in `control`'s UI, and in
this app's log.

**Ten unanswered polls lower it, with the session still open.** The socket
closing is not the only way a station goes away and is not the usual one:
`dccex-usb` holds its clients through an outage it thinks is brief and drops
their bytes, and a station that is powered, enumerated and mute — wedged
firmware — leaves the mirror a device it holds and nothing to report. So the
far end counts: ten intervals of `poll_s` with nothing read at all says the
station has stopped answering, and the row goes `down` naming it and how long
it has been silent. Everything the station told us goes with it, exactly as
it does when a link closes: a reading nobody can take is not the last one
taken. Nothing is torn down for it: the connection stays, the poll goes on
asking, and the next message read raises the link by the path every message
raises it. Ten is counted off the poll rather than kept as a second number, so
the two cannot drift apart, and it is generous on purpose — `layout` folds any
`down` to `state/power: off`, so a timeout that fires early stops a railroad
mid-session, and the mirror closing its clients is what reports the outages
that actually happen
([ADR-0066](https://github.com/rails49/control/blob/main/docs/adr/0066-the-link-is-the-station-answering-not-the-socket-being-open.md)).

**The banner raises the link and reaches no row.** It is what `<s>` is
answered with, so a station that sends one is a station answering. Which build
is on the box rode on this row until control#567 and does not any more: the
flash gesture went with the mirror, onto the face this repository serves, and a
microcontroller's firmware is not the railroad (the organisation's ADR-0002).
The `G-` field is read all the same, for the **journal**, which carries the
**build** on every line (below); nothing published here says it. A banner this
app can read no field off raises the link just the same, a message this app
reads nothing out of being the station answering as much as one it does.

**`device/point` only from a script.** This railroad's turnouts have no
feedback and the station's answer to a throw is one it faked
([ADR-0022](https://github.com/rails49/control/blob/main/docs/adr/0022-a-symbol-carries-its-hardware-address.md)),
so the station's answer is never published. A faked observation is worse than
silence. A script reports where a point lies with `t.point`, for an address
the drawing lists as `reported`
([ADR-0030](../adr/0030-a-script-reports-where-a-point-lies.md)).

**No `device/refused`.** The station answers a command it rejects with a bare
`<X>`, and the mirror passes every line to every client, so an `<X>` cannot be
told apart from one answering another client's command. A refusal this app
cannot attribute is not published (control `tc49.lib.inventory`).

Everything else on the port is another client's conversation — a slot's speed,
a turnout the station keeps of its own, a sensor it polls, a fast clock — and
is passed over unread. Parsing what the mapping does not need is work with
nobody to read it.

## The journal

**What the station said about power, kept on the box**, whether or not anyone
is watching: one JSON object per line, appended to a file on a volume
([ADR-0022](../adr/0022-the-journal-is-what-the-station-said.md) d.1). Shorts
should not happen on this railroad except where a reverser flips a district,
and finding the ones that do needs a record kept while nobody is looking. It
is `--journal <path>` and nothing is written without one.

**A line is written for** every `<* TRACK … *>` the station sends, every
`<p…>` that says something different from the last `<p…>` about the same
district, the link going down and the link coming up, and a station restart
(d.2 as amended). Nothing else: a mode, a limit and the banner are read for
the fields a line carries rather than kept as lines of their own.

**A `<p…>` that says what the last one did is no line**, and one that names
no district — the bare `<p0>` and `<p1>`, and `MAIN`, `PROG` and `JOIN` — is
no line at all. The station answers the one-second `<s>` with a line per
district, so a line for each of them was half a million a day on a railroad
where nothing happened, and the page reads the whole file to open the view
(#269). What is held is the line and not the station's words alone: a
district set to another mode is a line, the mode being part of what a line
says. What the journal last kept goes with the link and with a restart, so
the first `<p…>` after either says what the railroad is in rather than
nothing.

**Every line carries** `at`, when it arrived, ISO 8601 in UTC to the
millisecond — the station cuts a district and retries it inside one second, so
a stamp to the second would put a trip and its retry at the same moment — and
`railroad` and `build`, so that a file read a week later needs nothing beside
it. The build is empty whenever the station is not answering, which is what
the word means (GLOSSARY.md, **build**).

A line about something the station said carries `said`: the whole message
verbatim, `<` and `>` included. Where it names a district it carries
`district`, and that district's `mode` and `limit` as the station last
reported them — the one thing a reader of the file cannot get back afterwards.
Either is `null` where the station has not said yet, which is an ordinary
state of the first second of a link; a field absent is a reading nobody took,
never a number somebody could count.

```json
{"at":"2026-10-12T18:00:12.345+00:00","railroad":"gleis49","build":"v5.6.4-rails49.1","said":"<* TRACK C INVERT (fast) *>","district":"C","mode":"MAIN_AUTO","limit":500}
{"at":"2026-10-12T18:00:12.361+00:00","railroad":"gleis49","build":"v5.6.4-rails49.1","said":"<p0 C>","district":"C","mode":"MAIN_AUTO","limit":500}
{"at":"2026-10-12T18:00:19.004+00:00","railroad":"gleis49","build":"","link":"down"}
{"at":"2026-10-12T18:00:21.118+00:00","railroad":"gleis49","build":"v5.6.4-rails49.1","link":"up"}
{"at":"2026-10-12T18:02:03.772+00:00","railroad":"gleis49","build":"v5.6.4-rails49.1","restart":true}
```

A link line carries `link`, `down` or `up`, and is written where the word
moves rather than on every sentence about it: a connect retried against a
station that is not there says `down` on the row each time and writes one
line. A restart carries `restart: true`, and is the only record of one — the
link did not go, so nothing says it on the row (ADR-0021 d.4).

**This app decides nothing about a line** (d.3). Whether a line is part of an
**incident**, and which kind, is the page's as it reads the file
([docs/ui/README.md](../ui/README.md)), so a rule
that changes is run over the whole journal again under itself. A `TRACK C
INVERT` is a reverser doing its job and is kept exactly as a cut that followed
one would be.

**The file is opened for appending, and this app keeps it to a size** (d.4
as amended). Each line is flushed as it is written, so a reader is never a
line behind the railroad. Above `TRIMMED_ABOVE` bytes (10 MB) the oldest lines
go, down to the newest `TRIMMED_TO` bytes (8 MB); the two are constants in
`src/dccex/journal.py`. The last `<p…>` about each district from the part
that went stays in front of what is kept, with its own `at`, so the file
still says each district's power. The trim is written beside the journal and
renamed over it, and the mirror's face opens the file by name on each read,
so it serves the old file or the new one whole. Nobody clears it.

## Standing the railroad down

`shutdown()` sends **zero to every locomotive this app has commanded**, in the
order they were commanded, and only then the track off. Whoever constructed
the app calls it before letting the loop go.

The process ending is not by itself an instruction to the railroad. The
station goes on running whatever it was last told, so a session that exits
over a rolling locomotive leaves it rolling, and that is not recoverable the
way switching the power back on is. The zeros come first because the station
keeps a speed per locomotive and resumes it, so cutting the supply over a held
speed only postpones the motion.

A link that was never open sends nothing at all. A railroad this app could not
reach is one it was not driving, and `_send` drops rather than queues.

## The command line

```
python -m dccex --broker <host:port> --store <url> --station <host:port>
                     [--id <name>] [--journal <path>]
```

The process a container runs, coming up alone against a broker
([ADR-0059](https://github.com/rails49/control/blob/main/docs/adr/0059-the-bus-is-a-broker-each-app-is-its-own-process-and-the-bridge-is-deleted.md),
decision 5) as `layout`, `scheduler`, `dispatcher`, `driver` and `simulator`
do, and as `dccex-usb` has all along.

**A store, and no railroad on the command line.** `--station` is where
`dccex-usb` serves the command station, `--store` where the store serves the
documents, `--id` the name the link row is keyed by, the package's where it is
given no other, and `--journal` the file the journal is appended to, on the
box `/var/lib/dccex/journal.jsonl` on the volume the mirror mounts beside this
app. There is no `--railroad`: the one document this app
reads is its railroad's script, and which railroad that is is the row's to
say (above). An address is the string the hardware answers to rather than
something looked up, so nothing else here is a railroad's. The id names the
broker's client too, `tc49-<id>`: this is the one app a railroad may run
twice, and two clients sharing a client id take turns disconnecting each
other.

The drain period, the poll, the reconnect backoff and how often the store is
asked are not flags. Nothing outside the process has an opinion about them,
and what the station is asked, how long it may go without answering before the
link falls, how often a lost link is retried and how often a script is asked
for are this app's own.

Coming up is the broker, then the railroad, then the script, then the desired
picture, then the link. The two rows the constructor states are publishes, and
a publish made to a broker that is not there is dropped rather than queued, so
the broker is waited for first. The **railroad** row is waited for by name,
because there is one of it and the script cannot be asked for without it, and
the script is asked for once on that thread — a store that has not answered is
a state this app comes up in and says on its row, not one it waits out. The
desired rows the broker has retained are waited for last and **before** the
link is opened, for a second: a value arriving over a link that is already up
is acted on as it arrives, so the whole picture has to be held before a
connection is handed it
([control#333](https://github.com/rails49/control/issues/333),
[ADR-0054](https://github.com/rails49/control/blob/main/docs/adr/0054-the-railroad-comes-up-at-rest-and-points-replay.md)).

The app is also constructed on the bus directly, with where the station is
served and the script's own text:

```python
app = DccEx(bus, "mirror", 2560, scripts=Scripts("http://store:8765"))
app.load(sample.TEXT)
```

Loading takes the **text**, which is what `--store` fetches and what the
tests hand over (ADR-0015 d.2). `asks()` is one ask of the store, made before
the link is opened; `following()` is the ones after it, and it comes back
where the text has changed and the process is to end. `control`'s bench no
longer builds this app: a live run against a station is `layout` and this app
as separate processes on the broker
([ADR-0014](../adr/0014-the-translator-is-on-the-bus-through-controls-package.md)
d.6).

`run()` is the connection: it connects, applies the retained desired state,
reads what the station says until the link goes, and reconnects with backoff.
Nothing else waits on it — a desired value arriving while the link is down is
remembered and applied on the next connect, the way the retained value is at
startup, and the power is the one that is not (ADR-0013 d.6).

**No dependency is added**: the whole of it is `asyncio` streams and
`urllib`, and the image builds with `uv sync --frozen`.

**asyncio owns this app's process.** `_send` writes to an `asyncio.StreamWriter`
from inside a bus subscriber, so whichever thread drains the bus is the thread
that writes to the station: with the loop owning the process every subscriber
already runs on the loop thread and that write is where it belongs. Under
`python -m dccex` the drain is a coroutine beside `run()`, and the MQTT client's
network thread only appends to the queue that drain empties. Putting this app on
a daemon thread under a synchronous owner would mean marshalling with
`call_soon_threadsafe` — a cross-thread write where none exists today.

A signal is what ends the process, and the railroad is stood down on the way
out: the same `shutdown()` whoever constructed the app calls, before the link
is let go.

## Checking it against a real station

Nothing in the test suite needs the hardware — the connection is injected and
the tests drive a socket pair — so the gate is green on a machine with nothing
plugged in. Verifying the actual link is runtime's job, and the row that
reports it is `device/link`.

With the railroad powered and a locomotive on address 3 standing on the main:

```
$ nc gleis49.org 2560
<s>
<iDCC-EX V-5.4.16 / ESP32 / EXCSB1_WITH_EX8874 G-devel-202504182148Z>
<p1 A>
<p1 B>
<p1>
<t 3 63 1>
<l 3 1 191 0>
```

The banner naming the firmware, the board and the motor shield is the station
answering through the mirror, which is what `device/link: up` is made of; the
`<p…>` lines are what `device/track` is folded from; and the `<l>` line is the
station saying what the locomotive is now doing, speed byte 191 being the
forward bit over step 63.

**Then wait, and watch the locomotive.** It should still be running ten seconds
later, and no further `<l 3 …>` should appear on the port. This is the step
that matters and the one the suite cannot take: every check above passes against
a station that is quietly stopping the train a second later, which is exactly
what a `<!Q>` in the poll did
([control#463](https://github.com/rails49/control/issues/463)). A speed byte of
129 — the direction bit over step 1 — is the emergency stop, and seeing one
arrive that nobody sent means something on this port is commanding the station
rather than asking it.

Send `<t 3 0 1>` to stop it again. `<!>` stops every locomotive at once and any
throttle may drive away from it afterwards; sending it is safe and leaves
nothing to clear.

**Reset the station** with the translator connected and watch the same port.
Within a second — one poll — the translator reads `<jM 32000 0>` and sends
`<JM 32000 1>`, then the script's `start` lines — the sample's four `<= …>`
and four `<JG …>` — and then the replay. `<=` with no arguments lists the
modes the station now has (ADR-0018, ADR-0021).

The version in the banner is worth reading. The difference between the
mapping here and whatever build the station runs is silent: an unknown command
draws no `<X>` and no reply at all, so a command a station does not have does
something else or does nothing, with nothing said either way.
