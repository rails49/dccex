# ADR-0010 — the page polls, and the mirror originates nothing

- **Status:** accepted, 2026-09-23
- **Ticket:** rails49/dccex#1
- **Related:** [ADR-0007](0007-the-monitors-stream-is-one-more-client-of-the-mirrors-port.md)
  (the stream is one more client of the mirror's port),
  [ADR-0008](0008-the-page-talks-to-the-face-and-reads-the-build-off-the-banner.md)
  (every reading on the page is made of the conversation),
  [control ADR-0043](https://github.com/rails49/control/blob/main/docs/adr/0043-the-layout-interface-is-a-core-app-and-hardware-hangs-under-it-by-address.md)
  (the app that holds the device serves the port everything else is a client
  of),
  [control ADR-0066](https://github.com/rails49/control/blob/main/docs/adr/0066-the-link-is-the-station-answering-not-the-socket-being-open.md)
  (the link is the station answering)

## Context

The **band**'s two readings and three of the four **tile**s are made of what
the station said (ADR-0008 d.2). The station volunteers some of it — it sends a
banner when it comes up, and `<p…>` when power changes — but an idle station
sitting on a bench says nothing at all, and a page whose readings are made of
silence has no readings.

On the layout box something already asks. The **translator** polls `<s>`, as it
always has, and the answers fan out to every **client** on 2560 including a
page. **On the box this UI exists for, nothing does.** A command station on a
cable with no railroad loaded has no translator running beside it, and that is
the installation user story 29 is about: the whole page has to work there or
the installation is a fiction.

So somebody has to ask. Three could.

**The mirror could.** It holds the device and a timer is four lines. What it
costs is the only sentence that makes this app trustworthy: every byte on 2560
came from the station, and every byte the device was sent came from a client.
A mirror with a timer has an opinion about what `<s>` is and about when the
railroad wants to be asked — it is reading payload to decide what to write —
and a person watching the conversation on a monitor can no longer tell the
app's own traffic from a throttle's, because for the first time there is some.
The mirror gained a **face** in #12–#14 and kept that sentence intact; spending
it on a timer would be spending it for convenience.

**The face could, on a page's behalf.** The bytes would even enter by the
client path, since a **stream** is one more client of the port (ADR-0007). But
the schedule would be the app's rather than the page's: a page that wanted a
reading every ten seconds and one that wanted it every second would get
whatever the app chose, a page that wanted none would get one anyway, and the
app would still have to know what `<s>` means to send it. It is the mirror's
objection with a longer path to it.

**The page could.** It is a client of the port already, by the stream and under
every rule the port has (ADR-0007 d.2). Throttles poll. JMRI polls. A page
polling is a client doing what clients do, on a schedule belonging to whoever
is looking at it, and the mirror cannot tell it from DecoderPro — which is the
property ADR-0007 bought and this is what it is for.

## Decision

**d.1** The page polls. It asks the station for what its readings need, on its
own schedule, by sending whole `<…>` messages up its stream exactly as any
client sends them — and it marks the lines it sent, so an operator can tell
their own traffic from the railroad's.

**d.2** **The mirror originates nothing.** Every byte written to the device
came from a client and arrived as a whole `<…>` message. Not on opening the
device, not on reopening it after an outage, not on shutdown, not on a timer,
and not when a page connects. There is no probe, no keep-alive, no handshake
and no hello.

**d.3** It reads no payload in either direction. Outbound it is unframed
bytes to every client unchanged; inbound it reads `<` and `>` to know where a
message ends and no further. Nothing in it knows what any message means, and
the flash is the one thing it does that is not mirroring — which is why the
flash is the device being handed over rather than a message being sent.

**d.4** A conversation that is quiet when nobody is watching is the correct
conversation. With no page open and no translator on the box the station says
nothing, because nothing asked it anything, and the log of the railroad is what
was said rather than what a service manufactured to have something to show.
Nothing about a flash needs polling either: the station's banner arrives on its
own when it comes back up, which is how the **build** returns (ADR-0008 d.3).

**d.5** The gate holds **d.2**. A test runs the app's whole life against a
device that never goes away — the open, a client arriving, the station talking
and being fanned out, a client typing, clients leaving, and the shutdown — and
asserts that the only bytes that ever reached the device are the one message a
client sent.

## Consequences

- Two pages open means two pollers, as two throttles mean two. Nothing
  deduplicates them and nothing should: the answers fan out to everyone anyway,
  so a second poller costs one more `<s>` on a line that carries the whole
  conversation.
- On the layout box the translator's polls and a page's polls are both on the
  wire, and neither knows about the other. That was already true of a throttle.
- The mirror's correctness argument stays one sentence long, which is what lets
  it be checked: what the device sent reached every client, and what reached
  the device came from one.
- A page that is closed stops polling, so readings on a page opened later start
  from the first answer rather than from a history nothing kept. There is no
  history to keep — the mirror has no state of its own, and gaining a poller
  would have been the first of it.
- If a reading is ever wanted while nobody is watching, the thing to write is a
  client of the port that wants it. That is what the translator is, and it is
  next door.
