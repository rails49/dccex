# ADR-0021 — a restart is a stash the boot has cleared

- **Status:** accepted, 2026-10-09
- **Ticket:** #213
- **Supersedes:** [ADR-0018](0018-the-stations-setup-runs-at-start.md) d.2
- **Related:** ADR-0013 d.6 (a restart replays like a connect), ADR-0016 (the
  firmware's wording is part of the contract)

## Context

ADR-0018 d.2 reads a restart off the boot line `<@ 0 3 "Ready">`. That line is
the virtual LCD's, and its text, row and port are not part of any documented
interface. The first `<D RESET>` on the box printed a form d.2 did not name,
and nothing ran. A firmware update can do the same, and nothing is logged.

DCC-EX has no documented ready message, uptime or boot count. `<s>` answers the
same before and after a reset. Track modes do not tell a reset from a
deliberate change: `setTrackMode` broadcasts every change, and the boot sets A
and B through it (`TrackManager.cpp`). The sample's point 12 handler changes
D's mode in normal running.

A stash entry is held in RAM and is empty after every boot (`Stash.cpp`).
`<JM id loco>` sets one and `<JM id>` reads it as `<jM id loco>`, `0` when
unset. The parser takes `<JM>` in every build, EXRAIL or not
(`DCCEXParser.cpp`).

## Decision

**d.1** The translator owns stash `32000`.

**d.2** On a connect, and after a restart, the translator sends
`<JM 32000 1>` first, then runs `start` and the replay (ADR-0018 d.3).

**d.3** The poll sends `<JM 32000>` with `<s>`. Both only ask.

**d.4** `<jM 32000 0>` is a restart: `_forget`, then d.2.

**d.5** If no `<jM 32000 …>` arrives in the first ten polls of a link, the
translator logs a warning once.

**d.6** The boot line is no longer read.

## Consequences

- A restart is acted on within one poll, 1 s by default, instead of at once.
- A mode change from a throttle, JMRI or a handler does not touch the stash.
- An EXRAIL script that uses `STASH(32000)`, or a `<JM CLEAR ALL>` from any
  client, runs `start` and the replay again.
- A station whose firmware has no `<JM>` answers nothing. d.5 logs it, and no
  restart is seen.
- Every client of the mirror sees a `<jM 32000 1>` each poll.
- `replies.READY` and the README's bench step on `<@ 0 3 "Ready">` go.

## Considered

- **The boot line, with a warning after the licence line** (#213 as first
  filed). Keeps two undocumented lines in the contract.
- **Polling `<=>` against the modes `start` set.** A point handler or a
  throttle that changes a mode reads as a restart, and `start` undoes it.
- **A turnout or sensor defined in RAM as the marker.** JMRI and throttles
  list them.
- **The mirror telling its clients it reopened the port.** Misses
  `<D RESET>`, the reset button, a crash and a brownout.
