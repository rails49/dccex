# ADR-0028 — a railroad that is not built still runs its script

- **Status:** accepted, 2026-10-21
- **Ticket:** #329
- **Related:** [control ADR-0085](https://github.com/rails49/control/blob/main/docs/adr/0085-the-editor-saves-when-it-is-left-and-a-railroad-can-be-named-without-being-built.md)
  d.4 (a railroad can be named without being built),
  [ADR-0015](0015-the-script-is-a-railroads-document-in-the-store.md) (the
  script is a railroad's document in the store),
  [ADR-0026](0026-the-bands-power-control-is-controls.md) (the band's power
  control)

## Context

`tc49/layout/state/railroad` carries `built` (rails49/control#889):
`{"name": str, "at": stamp, "built": bool}`. An absent `built` reads as
`true`. Control ADR-0085 d.4 says `built: false` names a railroad whose
drawing is invalid, and that an app reading the row builds nothing and keeps
what it holds.

The translator reads nothing from the drawing. What it takes from the row is
which railroad's script to run, and the script is a document in the store
(ADR-0015), not derived from the drawing. The station is the same station
whichever railroad is named.

## Decision

**d.1** The translator runs the named railroad's script on `built: false` as
on `built: true`, at start and on a later row.

**d.2** The band shows the name followed by `not built` in a muted style on
`built: false`. `""` stays `no railroad loaded`, with no marker. An absent
`built`, or one that is not a boolean, reads as built.

**d.3** The band's ON and OFF presses stay available on `built: false`, on
the same rule as on a built railroad (ADR-0026 d.4). dccex does not refuse ON.
Whether `layout` accepts it is control's.

These depart from control ADR-0085 d.4, which says an app that reads the row
"builds nothing and keeps what it holds". dccex acts on the newly named
railroad instead: the translator runs its script, the band names it, and ON
stays available.

## Consequences

- A person can drive the station by hand to test while the drawing is being
  fixed, as far as `layout` allows.
- The script view opens the named railroad's script whether or not it is
  built.
