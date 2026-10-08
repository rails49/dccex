# ADR-0018 — the station's setup runs at `start`

- **Status:** accepted, 2026-10-08; d.2, d.3 and d.6 amended 2026-10-08 (#207); d.2 amended again 2026-10-08
- **Ticket:** #207
- **Amends:** [ADR-0013](0013-a-railroads-own-station-commands-are-a-script-in-the-translator.md)
  d.6 (a station restart replays like a connect) and d.9 (the setup is a
  `start` handler, not a power handler)
- **Related:** ADR-0016 (the firmware's wording is part of the contract),
  ADR-0017 (the band asks `layout` for power)

## Context

The sample's power handler sets each district's mode and `<JG>` limit, then
sends `<1>`. A `<1>` from JMRI, a throttle or the monitor's command box skips
it, and the station powers its districts as they are. After a restart that is
the firmware's defaults.

Modes and limits outlast a power OFF and are lost on a restart. The translator
lowers the link after ten missed polls, which a reset can be shorter than.

These commands are this repository's. `control` sees only the bus, and works
with a JMRI translator as well.

## Decision

**d.1** A script event `start`. The translator runs its handler when it
connects to the station and when the station restarts.

**d.2** A restart is the station's boot line `<@ 0 3 "Ready">`, the last
line `setup()` prints (`CommandStation-EX.ino`, `LCD(3, F("Ready"))`). The
virtual LCD starts out on the USB port, so this is its form at boot.

> **Amended 2026-10-08:** d.2 named the licence line, the first line of
> `setup()`. It comes before `TrackManager::Setup` sets the firmware's modes and
> before the station reads its port.
>
> **Amended again 2026-10-08:** d.2 then named `<* LCD3:Ready *>`. The station
> on the box printed `<@ 0 3 "Ready">` after `<D RESET>`, and nothing ran.

**d.3** On a restart the translator does what it does on a connect: `start`
first, then the retained desired state, power excepted (ADR-0013 d.6). A point
handler may set a district's mode, so it runs after `start`.

> **Amended 2026-10-08:** a restart first forgets what the station reported
> before it. A handler the replay runs reads no report from before the
> restart.

**d.4** `start` has no default. `t.default()` in its handler sends nothing.

**d.5** Nothing about `start` reaches the bus.

**d.6** The sample sets modes and limits at `start`. It has no power
handler.

> **Amended 2026-10-08:** d.6 kept a power handler that only called
> `t.default()`. With no handler the translator sends the same command.

## Consequences

- While the translator runs, a `<1>` from any client powers districts the
  script has set.
- A restart while the translator is down leaves the firmware's defaults until
  it comes back.
- The boot line is part of the contract, as the trip lines are (ADR-0016).
- A railroad's script in the store moves its setup to `start` by hand.
- CONTEXT.md's **event** entry has a third kind.

## Considered

- **The setup in the power handler**, as before. Only a power-on through the
  bus gets it.
- **EXRAIL at the station's boot.** It is compiled into the firmware, so a
  release would carry one railroad's settings.
- **A restart read from the link going down.** Ten seconds of silence; a reset
  can be shorter.
- **`reported_start`.** A connect is not something the station reports.
