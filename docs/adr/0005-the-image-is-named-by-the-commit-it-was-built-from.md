# ADR-0005 — the image is named by the commit it was built from

- **Status:** accepted, 2026-09-23
- **Ticket:** rails49/dccex#41, before #15
- **Related:** [ADR-0004](0004-the-face-reaches-a-browser-through-the-door-and-never-the-lan.md)
  (the door, and the box steps that are not code here),
  [ADR-0003](0003-the-copy-has-no-original-left-and-is-fixed-here.md) (the
  commit a copy came from, written down),
  [control ADR-0050](https://github.com/rails49/control/blob/main/docs/adr/0050-broken-hardware-is-reported-never-worked-around.md)
  (broken things are reported, never worked around)

## Context

`control` deploys by pulling `main` and rebuilding. Nothing is named after
what it was built from: the image that comes out is called the same thing the
one before it was called, so a box can say what is running only as a digest,
and the digest says nothing about which commit produced it. There is no
previous-version path written down anywhere, because there is nothing to
write one against.

#16's cutover can be rolled back at all only by an accident: the image it
replaces happens to still be on the box, unnamed, findable by digest if
nobody has pruned. That is why its procedure has to write out a `docker run`
by hand and carry a "do not prune" line. An incantation in one ticket's
procedure is not a way back; it is a way back for the person who wrote that
ticket, for as long as they remember it.

This repository's stack is #15's and is not written yet. Built in `control`'s
shape and no further, it inherits exactly the above. So the shape is settled
here, before #15 builds one, and before #16 cuts over on it — a versioning
scheme invented during a cutover gives the cutover a second failure mode, and
the first one is the cutover itself.

The words are already spoken for, which is most of what this decides.
[CONTEXT.md](../../CONTEXT.md) spends **tag** on a firmware release: the name
a caller picks a release by when it asks for one to be written onto the
command station. Docker calls the name after the colon a tag as well. Two
things called a tag in one sentence about a box is how somebody rolls a
railroad back to a firmware.

## Decision

**d.1** The image is named by the commit it was built from:
`dccex:<commit>`, the commit in full as `git rev-parse HEAD` gives it. One
commit, one image, one name, and the name never moves. Nothing on a box runs
`latest` and nothing runs `main`: a name that means something different next
week is a name nothing can be gone back to.

**d.2** It is one image for this repository, not one per app. The mirror runs
from it, and the translator will when it lands: they share a lockfile and they
share the esptool pin that `firmware.py` is written against, and a second
image would be a second answer to which esptool the repository was tested at.

**d.3** The word for the name is the **commit**. `tag` is a release's here and
stays a release's, whatever Docker calls the field — [CONTEXT.md](../../CONTEXT.md)
gains **image** and says both. A rollback names a commit; a flash names a tag;
neither sentence can be read as the other.

**d.4** The image carries the commit as `org.opencontainers.image.revision`
too, so a `docker inspect` on the box answers the question even for an image
somebody renamed, and the name is not the only copy of the fact. A deploy
builds from a clean checkout: a tree with uncommitted changes in it produces
an image whose name is a commit that is not what was built, so the deploy
refuses rather than lying in a name that outlives the person who typed it.

**d.5** A deploy appends what it did to a record on the box, at
`/var/lib/rails49/deploys/dccex`: one line per deploy, newest last, saying
when, the name that went and the name that came. Plain text, appended and
never rewritten, read with `tail` by a person who has just been handed the
box and has no tooling on it. The first line of a box's record says it
replaced nothing.

**d.6** A deploy keeps the image it replaced. That is one image of disk for
one step back, and it is the deploy's rule rather than a line in a cutover
procedure — #16's "do not prune" stops being something a person has to
remember. Anything older than one step back is the box's to prune, and what
pruning it costs is a second step back.

**d.7** Going back is one command naming the commit on the line before, read
off that record:

```
cd /etc/rails49/dccex && echo DCCEX_IMAGE=dccex:<commit> > .env && docker compose up -d
```

No digest recovered by hand, no `docker run` written out, and no rebuild: the
image is already on the box by d.6. The stack's `.env` holds that one line,
because the image's name is the one thing that differs between two deploys of
this repository, and writing it there is what makes the name survive a
restart — `restart: unless-stopped` brings back what was rolled back *to*.

**d.8** The happy path is unchanged. A deploy pulls, builds and brings up, as
`control`'s does; what is added is the name it builds under, the line it
appends and the image it does not delete. Rollback is not a deploy running
backwards — it skips the build, because the thing it wants was built already.

**d.9** None of this is code in this repository. The stack, its compose file
and the deploy are #15's, and they are built in this shape; what is here is
the decision and the mirror's page saying it (ADR-0004 d.6 is the same
division for the door's box steps). The gate is untouched by it: no box and
nothing to reach — one command and one exit status, as before.

*Amended for [#54](https://github.com/rails49/dccex/issues/54) and
[#56](https://github.com/rails49/dccex/issues/56), 2026-09-24:* "there is no
docker in the suite" stopped being true when #3 built the page inside the
image that serves it. The division stands by a different mechanism: a test
that needs a daemon carries the `docker` marker, the gate does not collect it,
and the workflow runs it in a job of its own that the pull request requires.
The gate is still one command, one exit status and no daemon; what the
amendment buys is that the check which proves an image serves cannot skip
itself out of a required gate, as it had in every recorded run.

## Consequences

- #15 has a shape to build rather than `control`'s to inherit, and #16 cuts
  over onto something that can be gone back on. The cutover stops carrying a
  rollback procedure of its own.
- A person on the box can answer "what is running, and what was running
  before it" from one `tail`, and "what commit is this" from the name. Neither
  answer needs this repository, a checkout, or the network.
- Rolling back needs nothing but the box. No registry, no credentials, no
  pull — which matters most in the case a rollback is for, where something
  that was just deployed is the thing that is broken.
- A rollback leaves `main` ahead of what runs, and nothing on the box makes
  that go away. The record is where it is visible; putting it right is a
  commit and the next deploy.
- The record lives on the box, so a box that is rebuilt from nothing starts a
  fresh one. Git still holds every commit; what is lost is which of them that
  box was running, which is why the record is not the only place the commit is
  written (d.4).
- Two steps back is not promised. A box that has pruned has one, and a deploy
  that has happened twice since a bad one is asking for a commit, which is
  d.7's command with an older name and a build first.
- `control`'s own stack is untouched. It has the same problem and this is not
  its fix; that is that repository's business.
