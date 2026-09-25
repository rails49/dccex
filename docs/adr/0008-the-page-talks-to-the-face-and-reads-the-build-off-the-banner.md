# ADR-0008 — the page talks to the face and reads the build off the banner

- **Status:** accepted, 2026-09-23
- **Ticket:** rails49/dccex#1
- **Related:** [ADR-0001](0001-the-mirror-leaves-the-bus-for-a-face.md) (the
  mirror leaves the bus, and what reaches it instead),
  [ADR-0004](0004-the-face-reaches-a-browser-through-the-door-and-never-the-lan.md)
  (the page and the face on one origin),
  [ADR-0007](0007-the-monitors-stream-is-one-more-client-of-the-mirrors-port.md)
  (the stream the readings are made of),
  [org ADR-0001](https://github.com/rails49/.github/blob/main/docs/adr/0001-a-ui-of-its-own-is-about-something-other-than-the-loaded-railroad.md)
  (a UI of its own is about something other than the loaded railroad),
  [org ADR-0002](https://github.com/rails49/.github/blob/main/docs/adr/0002-a-ui-talks-to-the-bus-the-store-and-its-own-apps-face.md)
  (what a UI may talk to),
  [control ADR-0066](https://github.com/rails49/control/blob/main/docs/adr/0066-the-link-is-the-station-answering-not-the-socket-being-open.md)
  (the link is the station answering, not the socket being open)

## Context

The organisation's ADR-0002 lets a UI talk to three things: the bus, the store,
and its own app's **face**. It permits; it does not choose. This page has to
choose, and the choice decides what the page *is*.

Two of the three are on offer and both would work on the layout box. The bus
carries `device/link`, the track row and the current; the store holds what a
railroad is. Reading the band and the tiles off them is the short way, and it
is how a view inside `control` would have been written — which is the thing
org ADR-0001 refused, and this is where the refusal has to be paid for rather
than restated.

**The box this UI exists for has neither.** A command station on a cable,
plugged into a machine with no cameras, no railroad loaded, no broker to dial
and no `control` clone on it. Every reading taken off the bus is a reading that
is blank there, and a page whose readings are blank on the installation it was
written for is a page nobody can use to tell a dead station from a quiet one —
which is user story 1 and the reason any of this exists.

There is a third source, and it has been under the cable the whole time. The
station says all of it. Power and current come back on `<p…>` and `<c …>`; the
**link** is whether it is answering at all, which is what `control` ADR-0066
already says the link is; and the **build** is the `G-` field of the banner it
sends when it comes up. `control` publishes an optional `build` on
`device/link` today only because the translator had already read it off that
banner and had a bus to put it on — and org ADR-0002's deletions take that
field away, so the bus is about to stop being a source for it at all.

The remaining tile is the one the station cannot say: how many **clients** are
on the mirror's port. That is a fact about the mirror, which is what a face is
for.

So the choice is not between three counterparties. It is between a page about a
railroad that happens to show a command station, and a page about a command
station — and only the second one is the same page on both box shapes.

## Decision

**d.1** The page's only counterparty is the mirror's face. Not the bus, not the
store, not `control`, and not the release API: the app fetches releases and the
browser calls no third-party service (#12). Nothing on the page is conditional
on a railroad being loaded, because nothing on the page asks.

**d.2** Every reading about the station is made of what the station said, off
the **stream** (ADR-0007). The link, whether the rails are hot, the current on
the track, when the station last spoke, and the **build** — all of them are the
conversation, decoded on the page. There is no second channel and nothing is
inferred on one: the stream carries the bytes and no protocol of our own.

**d.3** The **build** is the `G-` field of the banner and nothing else. It is
what the hardware says it is running, so it is empty whenever the **link** is
down — during a flash, a pulled cable, a station switched off — and it fills
again by itself when the station comes back and says. A build held over from
before an outage would be this page reporting what it cannot see.

**d.4** The one reading that is not the station's is how many **clients** are
on the mirror's port, and it comes off the face, which is the app's own
business about itself.

**d.5** **Nothing on the page commands track power.** `control`'s band presses
ON, STOP and OFF because `layout` checks the railroad is drained before
anything reaches the wire; this page is on no bus, so a press here would go
down the cable with nothing behind it having checked. The band is two readings
and no controls. The one caller that cuts power is the flash sequence, which
cuts it as its own first step and confirms with the operator first (ADR-0006),
and the command box can still type `<0>` — which is what a raw monitor is, and
is the operator typing at the station rather than the chrome commanding a
railroad.

**d.6** One page, both box shapes, with no branch between them. A command
station on a cable with nothing else on the machine gets the whole page; the
layout box gets the same page with the same behaviour, beside `control`'s own
UI rather than inside it.

## Consequences

- The page serves and works with no broker, no store and no `control` clone
  present. That installation is the one this repository exists for, and it is
  not a reduced mode of anything.
- The page can say nothing about a railroad, and should not learn to. It has no
  turnout names, no locomotive roster and no run state, because none of those
  is a thing a command station says. Somebody wanting them wants `control`'s
  UI, which is next door on the layout box and is about that.
- Three tiles blank together when the link drops, and that is the correct
  reading rather than a gap: the build, the current and the last thing said are
  all the station talking, and the station is not talking.
- This UI draws no emergency stop. When LOOK.md widened red on the chrome to
  stop or a fault, the band's link took `--stop` while the station is not
  answering, since that is a fault (#138). Nothing else here is red.
- If `control` ever removes the optional `build` from `device/link` on a
  different schedule than expected, nothing here changes. This page never read
  it.
- A reading somebody wants that the station does not say and the mirror does
  not know has nowhere to come from, and the honest answer is that the page
  does not have it. That is the cost, and it is the same cost org ADR-0001
  accepted when it declined to make this a view of `control`.
