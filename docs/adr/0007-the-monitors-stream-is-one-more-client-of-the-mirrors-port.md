# ADR-0007 — the monitor's stream is one more client of the mirror's port

- **Status:** accepted, 2026-09-23
- **Ticket:** rails49/dccex#14, under #10
- **Related:** [ADR-0001](0001-the-mirror-leaves-the-bus-for-a-face.md) (the
  mirror leaves the bus for a face),
  [ADR-0004](0004-the-face-reaches-a-browser-through-the-door-and-never-the-lan.md)
  (the face reaches a browser through the door, and the stream rides the same
  router),
  [control ADR-0043](https://github.com/rails49/control/blob/main/docs/adr/0043-the-layout-interface-is-a-core-app-and-hardware-hangs-under-it-by-address.md)
  (the app that holds the device serves the port everything else is a client
  of),
  [control ADR-0066](https://github.com/rails49/control/blob/main/docs/adr/0066-the-link-is-the-station-answering-not-the-socket-being-open.md)
  (the link is the station answering, not the socket being open)

## Context

The UI shows the station's conversation and has a box to type into. That is
what 2560 has always served — every byte to every client, and a client's bytes
to the device as whole `<…>` messages — and the page cannot have it that way:
a browser cannot open a TCP socket, and a page served over `https` cannot open
a plain one even where it could. What a browser can open is a stream on the
origin it is already on, which is the face's (ADR-0004 d.3).

So the bytes have to reach the page through the face. **How** is the question,
and there were two shapes.

**A second fan-out.** The face is in the process that holds the device; it
could take the bytes from the mirror in memory and hand them to whatever
browsers are connected. Everything that makes 2560 safe would then exist
twice: the bound on how far behind a client may fall, the abort rather than the
polite close, the grace that disconnects everyone when the device is away, the
framing that keeps two clients from interleaving a command. Two copies of a
rule are two rules, and the day they disagree is the day a page holds a
megabyte the mirror thinks it let go of.

**A client of the port.** The face opens a connection to 2560 on the caller's
behalf and moves bytes between it and the browser. The rules stay where they
are and there is exactly one of each. What it costs is one hop on the loopback
interface inside the container, and a client the mirror cannot tell from JMRI
— which is not a cost, because the mirror has never told its clients apart
(CONTEXT.md, **client**).

## Decision

**d.1** A monitor's stream is one more client of the mirror's port. The face
joins 2560 on `127.0.0.1` when a page opens a stream, and what it does after
that is carry bytes: the station's out, and what the page types in.

**d.2** Every rule about a client is the mirror's and is not written again.
The fan-out, the megabyte a client may fall behind by, the cut-off, the grace
that disconnects everyone on an outage, the abort rather than the close, the
`<…>` framing and its size cap — all of them reach a page because a page is a
client of that port, and none of them has a second version for the stream.

**d.3** Nothing is buffered between the two ends. What the browser has not
taken is waited on before more is read off the mirror, so a monitor that has
stopped reading fills the mirror's socket and is cut off by **d.2**'s rule.
A buffer of the stream's own would hold what the mirror believes it has
handed over, and the mirror's bound would never be reached.

**d.4** The stream is served on the face's port, at `/stream` with the door's
prefix already off it, and is opened by upgrading and no other way. One port
carries it and the face's other requests, which is what makes it `wss://` on
the page's own origin with no second certificate (ADR-0004 d.3). A page from
another origin is refused before anything is joined: a browser asks nobody
before opening a stream, so the origin it names is the whole of what keeps a
page somewhere else off the command station (ADR-0004 d.4).

**d.5** The station's bytes ride as binary frames, unchanged. A text frame
must carry valid UTF-8 and a serial line promises none, and the mirror's
contract is that every byte reaches every client as it was sent. What a page
sends is read the other way round — text, binary or a continuation, all of it
payload — because what ends a message is `>` and the mirror is what reads for
it.

**d.6** The mirror is untouched. `station.py` has no knowledge of the face, no
knowledge of a stream, and nothing in it changed for this.

## Consequences

- 2560 behaves exactly as it did, with a page on the stream and without one.
  There is no code path through the mirror that exists only for the face.
- A page on the stream shows up in the mirror's log as a client connecting
  from loopback, and leaves by the same four paths every client leaves by. A
  person reading the log sees how many clients there are, which is what they
  saw before.
- The process holds one more socket pair per open monitor, which is what a
  page costs. There is no limit on how many beyond the OS's, as on 2560.
- A monitor cannot be told anything 2560 does not say. Whether the station is
  answering is read off the conversation, as the translator reads it
  (ADR-0066); there is no side channel on the stream and nothing is inferred
  on it.
- If the mirror's port is ever taken off the LAN, the stream keeps working:
  what it joins is `127.0.0.1` inside the container, which is the same place
  the port is bound either way.
- The gate proves this without a browser: the suite speaks the frames itself,
  drives the device with a pty, and holds the cut-off by timing out if the
  stream ever reads the mirror faster than the page is reading it.
