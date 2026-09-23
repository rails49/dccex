# ADR-0003 — the copy has no original left, and is fixed here

- **Status:** accepted, 2026-09-22
- **Ticket:** rails49/dccex#23, #24, #26
- **Supersedes:** [ADR-0002](0002-a-defect-in-copied-code-is-fixed-where-it-came-from.md)
  (a defect in copied code is fixed where it came from)
- **Related:** [ADR-0001](0001-the-mirror-leaves-the-bus-for-a-face.md) (d.6,
  the copy and what it promises), [SOURCE.md](../../src/SOURCE.md) (the commit
  it was taken at)

## Context

ADR-0002 routed a defect in a copied file to the repository it was copied
from: the fix lands in `control` first, comes back here as a re-copy at the
new commit, and `SOURCE.md` goes on telling the truth. That was right while
`control` had a copy to fix. The cost it accepted — a full round trip for
every defect — was paid to keep two live files in step.

rails49/control#567 merged on 2026-09-22 and deleted `src/tc49/dccex_usb` and
`tests/dccex_usb/`. There is no second copy. The defects ADR-0002 was written
for — #23, #24, #26 — are in this repository's file and nowhere else, and the
route it laid out has no destination: there is nothing upstream to fix, and a
re-copy would be a copy of what is already here.

## Decision

**d.1** A defect in `src/dccex_usb` is fixed here, with its test, like any
other code in this repository. There is no upstream step and no re-copy.

**d.2** `SOURCE.md` goes on naming `rails49/control` and `deee7b6`. That is
where the package came from, the commit is immutable, and the diff recipe
still runs. What it stops promising is that the two files stay the same: it
lists what has been changed here since, so a reader sorting a diff is told
which side of it is ours and why.

**d.3** ADR-0002 is superseded rather than quietly ignored, which is what its
own d.4 asked for. Its reasoning was never wrong; the repository it pointed at
stopped having the file.

**d.4** ADR-0001 d.6 stands, and so does ADR-0002 d.3's carve-out of it: the
behaviour and the numbers are not up for reconsideration here, a defect is not
a reconsideration, and a fix that changes what the mirror does amends d.6 at
the time. #23 is the first to do so.

## Consequences

- #23, #24 and #26 are one piece of work each rather than two, and an agent
  working only this repository can do them.
- #13 waits on #24 landing here, not on a round trip.
- The gate's `source` check is unaffected: `SOURCE.md` still names the
  repository and the commit, which is all it asks.
- A diff against `deee7b6` still shows the bus coming out, and now also the
  fixes `SOURCE.md` lists. Nobody has to guess which is which.
- If `dccex_usb` ever needs a change to travel the other way, there is no
  other way for it to travel. That is the point of the deletion, not a
  consequence this decision has to answer for.
