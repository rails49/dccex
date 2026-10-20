# ADR-0026 — the band's power control is `control`'s

- **Status:** accepted, 2026-10-20
- **Ticket:** #319
- **Supersedes:** [ADR-0017](0017-the-band-asks-layout-for-power.md) d.1, d.2
  and d.3; [ADR-0020](0020-the-band-has-a-stop-press.md) d.2 and d.3
- **Related:** [ADR-0023](0023-the-chrome-comes-from-look.md) (the chrome
  comes from look), `control` ADR-0078

## Context

`control` ADR-0078 makes `tc49/layout/power_wanted` and
`tc49/layout/state/power` carry `on`, `draining` or `off`. `layout` drops any
other ask. An emergency stop is `off`, applied at once in every state.
`stopped` leaves the contract.

This page's STOP asks for `stopped` (ADR-0020 d.2), so `layout` drops it.
The toggle asks for `off`, which is now the emergency stop.

`control`'s band uses the same `look-power` element. Its `asked()` and
`supply()` (`ui/src/model/commands.ts` at 109fc5d) map look's presses onto
ADR-0078 and decide when the element is dead.

## Decision

**d.1** The band's power control does what `control`'s does. A change there
is followed here.

**d.2** A press asks `layout` for:

| look's press | asked |
| --- | --- |
| toggle `off`, from `on` | `draining` |
| toggle `on`, from `off` or `draining` | `on` |
| stop sign `stopped` | `off` |

**d.3** `state/power` reads as `on` or `draining` where it says so, and as
`off` otherwise. look draws the state.

**d.4** Both presses are dead while the bus is unreachable or before
`layout` has reported `state/power`, with the one reason
`Waiting for the station`. Otherwise both are live.

ADR-0017 d.4 to d.6 and ADR-0020 d.4 stand.

## Consequences

- One press drains the railroad and one cuts it at once, as on `control`'s
  page.
- A silent station no longer disables the toggle. `layout` reports `off`
  then, and checks the `on` the toggle asks for.
- STOP is dead until `layout` has reported. ADR-0020's rule that `layout`
  holds a STOP sent before then goes with `stopped`.
- `control`'s rule that both presses are dead while an unsaved railroad is
  off (`control` ADR-0071) is about editing a railroad. This page edits none,
  and the rule does not apply.

## Considered

- **The toggle asks for `off`.** Two presses for the same immediate cut, and
  the same press means different things on the two pages.
- **A look release whose stop sign fires `off`.** Changes `control`'s page
  for no gain.
