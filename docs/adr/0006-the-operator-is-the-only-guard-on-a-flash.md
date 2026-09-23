# ADR-0006 — the operator is the only guard on a flash

- **Status:** accepted, 2026-09-23
- **Ticket:** rails49/dccex#13, under #10
- **Related:** [ADR-0001](0001-the-mirror-leaves-the-bus-for-a-face.md) (the
  mirror leaves the bus, and what reaches the flash instead),
  [ADR-0004](0004-the-face-reaches-a-browser-through-the-door-and-never-the-lan.md)
  (the page and the face on one origin),
  [control ADR-0065](https://github.com/rails49/control/blob/main/docs/adr/0065-the-app-that-owns-the-device-flashes-it.md)
  (the app that owns the device flashes it),
  [control ADR-0051](https://github.com/rails49/control/blob/main/docs/adr/0051-track-power-is-cut-by-the-client-that-was-written-to-cut-it.md)
  and
  [control ADR-0062](https://github.com/rails49/control/blob/main/docs/adr/0062-a-guarantee-about-a-railroad-lives-in-the-client-that-makes-it.md)
  (a guarantee about a railroad lives in the client written to honour it)

## Context

Writing the firmware drops the rails and resets the board. Every throttle
loses the station, the translator loses the link, and anything moving keeps
moving until friction stops it. It takes a minute or two. Doing it while a
train is running is the one way this app can hurt a railroad, and #13 is the
ticket that makes it possible to ask for from a page.

**Nothing in this repository can tell whether a train is running.** The mirror
holds a cable and repeats it; it is not on the bus, it has no store, and a
command station is not a fact about a railroad (ADR-0001). The face is private
to this app and is not somewhere else to get at the layout
([CONTEXT.md](../../CONTEXT.md), **face**). The run state and the track row
exist, in `control`, and there is no path from here to either that ADR-0001 did
not deliberately cut.

Two ways to get one back were available, and both are worse than the problem:

- **Put the mirror back on the bus** to read the run state before it writes.
  That is the coupling ADR-0001 removed, and its cost is a cable that cannot
  be mirrored on a box with no broker — which is most boxes, most of the time,
  including the one somebody is debugging a station on.
- **Have the page ask `control` and refuse.** The page can do that and should
  (d.2), but a check in a client is advice: the station is written by whatever
  reaches the face, and the next thing to reach it will be `curl` on the box.
  A guard that the thing being guarded can walk around is a guard nobody can
  rely on, and one people will rely on anyway.

`control` settled the same question for cutting track power and settled it the
same way: the guarantee lives in the client that was written to make it
(ADR-0051, ADR-0062). This is that rule, applied to the one other thing that
stops a railroad, and written down here because #13 is where a person first
gets a button for it.

## Decision

**d.1** The mirror checks nothing about the railroad before it writes. It does
not read a run state, a track row, a throttle, or anything else that is a fact
about a layout — and no later version of it does, because acquiring the ability
is what ADR-0001 says this app is not for. What it does check is its own
business: the tag, the release, the digest, the device, and whether it is
already writing (#13).

**d.2** The guard is the operator, and the page is what helps them be one. It
sequences what it can — it is a UI on the same origin as the rest of them, it
can stop what it can stop and say what is about to happen — and it confirms
before it asks. What it cannot do is prevent, and it does not pretend to: a
sequence the operator declines is a flash that is not asked for, not a flash
that is refused.

**d.3** What this app owes instead is the truth, before and after. Every
refusal is a status and a reason to whoever asked rather than a line in a log
addressed to nobody (#13); the outage is visible to every client on 2560 for
as long as it writes, which is the same outage a pulled cable gives them; and
what is running afterwards is read off the station itself, as the **build** in
the banner it sends when it comes back. Nobody has to be told what was written
— they can ask the hardware.

**d.4** This decision is recorded in this repository and amends nothing in
another. #13 asked for it on ADR-0002, and neither ADR-0002 is available to
carry it: the one here is about where a defect in copied code is fixed and is
superseded ([ADR-0003](0003-the-copy-has-no-original-left-and-is-fixed-here.md)),
and the one the face is built on is the organisation's, in `rails49/.github`,
which is another repository — which is the thing the same criterion says not
to touch. So it is written here, where the code it governs is, and #13's other
half of that criterion is met exactly.

## Consequences

- A flash under a moving train is possible, and stays possible. That is the
  point of writing it down: the face's refusals are about tags, sources,
  digests and devices, and nobody should read them as a safety mechanism.
- The page's sequence is where the care goes, and it is the UI's work rather
  than this repository's. A page that skips it is a page that is wrong, and
  nothing here can tell.
- A person with `curl` on the box can write the station at any moment. That is
  true of every app behind the door on a LAN that carries no authentication
  (control ADR-0042) and is not made worse by the face.
- If the UI one day reads the run state, d.1 does not change: what changes is
  how good the page's sequence can be. The app stays the thing that knows
  about a cable and nothing about a railroad.
- `control` is untouched. Its mirror, its ADRs and its bus are its own; this
  says what the app in this repository does.
