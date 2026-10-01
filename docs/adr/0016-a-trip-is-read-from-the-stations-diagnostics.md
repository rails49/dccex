# ADR-0016 — a trip is read from the station's diagnostics

- **Status:** accepted, 2026-09-30; d.5 amended 2026-10-01
- **Ticket:** #188, rails49/control#601
- **Amends:** ADR-0009 d.4 (the translator now reads one kind of diagnostic
  line)
- **Related:** ADR-0007 (the monitor's stream is one more client of the
  mirror's port), `control` ADR-0050 (no reason for a trip), `control`
  ADR-0062 (the gates read observed power)

## Context

A district the station cuts itself is published as `off` with no `reason`,
the same as a pressed OFF. The translator folds `device/track` to `on` only
where every district reads `1`, so one short stops every train on the
railroad. The `<s>` poll prints `0` for a tripped district, an off one, and a
powered one the station is watching for a rising current.

DCC-EX broadcasts nothing on a trip. It writes the trip to USB as a
diagnostic, `<* TRACK B POWER OVERLOAD 3120mA (max 3000mA) detected after 2ms.
Pause 40ms *>` (`MotorDriver.cpp:637`, fork tag `v5.6.4-rails49.1`), and
retries on its own with a wait that doubles from 40 ms to 10 s. The mirror
sends every USB byte to every client of its port, so the translator already
receives these lines.

## Decision

**d.1** A trip is what the station says. The translator does not infer one
from `wanted/track` against `device/track`: another throttle's OFF looks the
same.

**d.2** The translator reads `<* TRACK X … *>` lines from the mirror. It does
not poll `<JI>`.

**d.3** A district is tripped from `POWER OVERLOAD` or `FAULT PIN detected`
until `NORMAL` for that district. A commanded OFF and a link loss clear every
trip.

**d.4** A district in `ALERT`, with no trip since, counts as powered until
`NORMAL`. Otherwise its `<s>` digit decides. A `0` no line explains is off.

**d.5** `device/track` stays one word for the whole supply. `power` is `on`
when no district is off and at least one is not tripped, and `off`
otherwise. While a district is tripped, `reason` names it:
`"district B tripped"`, `"districts B, C tripped"`. A link reason takes
precedence.

> **Amended 2026-10-01:** `power` is `on` when at least one district is
> powered and not tripped, and `off` otherwise. A district that is off no
> longer turns the supply off: on the bench, C and D are unused and off, and
> the supply read `off` with A and B on. This is the wording `control` BUS.md
> took in rails49/control#601.

## Consequences

- A short in one district leaves trains and points elsewhere running. A train
  in the tripped district is sent moves and does not move.
- `control` BUS.md lets the supply's `reason` name tripped districts, with
  `on` or `off`. This revises `control` ADR-0050.
- The translator depends on the mirror for trips. Against the station's own
  TCP port it sees none, as before.
- The firmware's wording is part of the contract. The rails49 fork owns it.

## Considered

- **Polling `<JI>`.** It reads `-1` only between retries, so it misses a trip
  that restores within a poll.
- **A new `power` word, e.g. `tripped` or `partial`.** Every gate in `control`
  that checks for `on` would stop the railroad again.
- **One topic per district.** BUS.md keeps districts off the bus.
- **The current in the reason.** It changes on every retry and would
  republish `device/track` each time.
