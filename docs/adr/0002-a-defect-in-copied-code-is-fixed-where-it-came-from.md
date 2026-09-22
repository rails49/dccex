# ADR-0002 — a defect in copied code is fixed where it came from

- **Status:** superseded by
  [ADR-0003](0003-the-copy-has-no-original-left-and-is-fixed-here.md),
  2026-09-22 — `control`'s copy was deleted, so there is no repository to fix
  a defect in but this one (accepted 2026-09-22)
- **Ticket:** rails49/dccex#23, #24, #26
- **Related:** [ADR-0001](0001-the-mirror-leaves-the-bus-for-a-face.md) (d.6,
  the copy and what it promises), [SOURCE.md](../../src/SOURCE.md) (the commit
  it was taken at)

## Context

Five modules arrived here as a copy of `rails49/control`'s `dccex_usb` at
`deee7b6`, and `station.py` and `framing.py` arrived byte-identical to it but
for the module paths. ADR-0001 d.6 says why: the next person can diff the two
and see only the bus coming out. `SOURCE.md` carries the recipe for that diff.

A review after the copy landed found four defects in `station.py`. None was
introduced here — all four came across in the copy and all four are in
`control` today. That is the case d.6 did not name. It says the way the mirror
behaves is not up for reconsideration *here*, which settles a rewrite; it does
not say where a bug goes.

Fixing one here is the obvious move and the wrong one. The first substantive
change to a copied file is the moment the diff recipe stops being worth
running: from then on the two files differ in ways a reader has to sort into
"the bus coming out" and "something else", and nothing tells them which is
which. `control` also keeps the defect, so the railroad's own mirror stays
broken while this one is fixed — and the fix, if it came back at all, would
come back as a merge nobody planned.

## Decision

**d.1** A defect in a file this repository copied is fixed in the repository it
was copied from. The fix lands there first, on its own terms, with its own
test.

**d.2** It comes back here as a re-copy at the new commit, not as a patch. The
file is taken whole, the module paths are rewritten as they were the first
time, and `SOURCE.md` is updated to name the new commit. A re-copy is
mechanical and can be delegated; the fix upstream is not and cannot.

**d.3** ADR-0001 d.6 stands, with this carve-out named: the behaviour and the
numbers are not up for reconsideration here, and a defect is not a
reconsideration. When a fix changes what the mirror does, d.6 is amended to say
so at the time, rather than left to read as though nothing moved.

**d.4** This holds while `SOURCE.md` claims the files are diffable. If that
claim is ever withdrawn — if this package forks from `control` on purpose —
this ADR is superseded rather than quietly ignored.

## Consequences

- A `station.py` defect found here is two pieces of work: one in `control`, one
  here. On this tracker the second is a re-copy ticket blocked by the first.
- A defect cannot be fixed here by an agent working only this repository, which
  is why #23, #24 and #26 are `ready-for-human` rather than `ready-for-agent`
  despite being fully specified.
- #13 waits on #24 landing in `control` and coming back, not on a local patch.
- Someone has to be able to land changes in `control`. If that stops being
  true, this decision has to be revisited, and d.4 is how.
- The three defects are real and are not fixed by writing this down. They are
  #23, #24 and #26.
