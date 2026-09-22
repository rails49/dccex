# ADR-0003 — the copy has no source, and station.py is ours

- **Status:** accepted, 2026-09-22
- **Ticket:** rails49/dccex#23, #24, #26
- **Supersedes:** [ADR-0002](0002-a-defect-in-copied-code-is-fixed-where-it-came-from.md)
- **Related:** [ADR-0001](0001-the-mirror-leaves-the-bus-for-a-face.md) (d.6,
  the copy and what it promised), [SOURCE.md](../../src/SOURCE.md) (where the
  code was written),
  [control#567](https://github.com/rails49/control/issues/567) (the deletion)

## Context

ADR-0002 decided that a defect in a file this repository copied is fixed in the
repository it was copied from, and comes back here as a re-copy. It was
committed on 2026-09-22 at 21:17. rails49/control#567 merged a minute later and
deleted `src/tc49/dccex_usb` and `tests/dccex_usb/`. There is no longer a
repository to send a fix to.

This is not a reversal. ADR-0002 named the end of the route in its own
consequences — #567 was already written — and d.4 said what happens when the
copy has nothing left to be a copy of. What it got wrong was the order. It
expected the deletion to wait until the box ran the mirror from here (#16), and
the deletion went first, so the three defects it routed upstream never took
that route at all.

Nothing is chosen here. The source was deleted and this is what follows. It is
written down because four documents now say things that are not true, and
because a reader who finds ADR-0002 first should not conclude that #24 is
waiting on a pull request somewhere else.

## Decision

**d.1** The copy is over. `src/dccex_usb` is this repository's own code. There
is no upstream, no re-copy, and no commit to stay diffable against.

**d.2** A defect in it is fixed here, on its own terms, with its own test.
ADR-0002 d.1 and d.2 retire with the repository they named.

**d.3** The numbers ADR-0001 d.6 pinned — the backoff, the grace, the
outstanding-bytes cut-off and the handover — are ordinary code now. The pin was
bought with diffability, and diffability is what stopped being purchasable.
This reopens nothing today: changing one of them still needs a case, and it is
an ordinary case now rather than an amendment to an ADR.

**d.4** [SOURCE.md](../../src/SOURCE.md) stays, as provenance and not as a
constraint. It says where the code was written and what the copy changed,
because `station.py` holds the class the mirror is and a reader wants to know
why it is named after a package that no longer exists. It promises nothing
about staying diffable.

## Consequences

- #23, #24 and #26 are fixed here. #24 goes first: it is the severe one, it is
  reproduced, and #13 waits on it.
- #13 waits on #24 landing here, not on a re-copy.
- The container serving 2560 on the box was built from source that no longer
  exists. It runs, #24's deadlock runs in it, and it cannot be rebuilt. If that
  image is pruned or its tag moves, the railroad has no mirror until #15
  publishes one. That is what makes #15 urgent in a way its own ticket does not
  say.
- The diff recipe in `SOURCE.md` still runs. `deee7b6` is a commit, and
  deleting a file on `main` does not take it out of history. What it shows is
  the bus coming out, which is what it always showed. What has gone is any
  reason to run it before changing this file.
- A defect found in `src/dccex_usb` from here on is one piece of work, not two.
