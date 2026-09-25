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

*Amended for [#15](https://github.com/rails49/dccex/issues/15), 2026-09-24,
where the stack was built:*

**d.7's one line is `DCCEX_COMMIT=<commit>`**, not `DCCEX_IMAGE=dccex:<commit>`,
and the directory it is written in is the clone on the box rather than
`/etc/rails49/dccex`. Both for the same reason: the page landed between this
decision and the stack that carries it, and it is a second image of the same
commit under the same naming rule (`compose.yaml`, `deploy/ui.Dockerfile`). A
rollback naming one image would take the mirror back and leave the page where
it was — two lines, where this decision asked for one — and the commit names
both, `dccex:<commit>` and `dccex-ui:<commit>`. Nothing else of d.7 moves: one
line, in the project's own `.env`, no rebuild, and `restart: unless-stopped`
bringing back what was rolled back *to*.

**d.9 has run its course.** The stack is code in this repository now —
`deploy/Dockerfile`, `compose.box.yaml` beside `compose.yaml`, and
`scripts/deploy.sh` — and it is built in this shape. The box's half is an
overlay because `compose.yaml` has one promise of its own to keep, which is to
come up from a clean clone. The gate is untouched, as d.9 said it would be:
the check that starts the built image and dials 2560 against it carries the
`docker` marker of the amendment above, so the gate is still one command and
one exit status on a machine with no daemon.

*Amended for [#55](https://github.com/rails49/dccex/issues/55), 2026-09-24:*

**d.2's count is two, and the second is the page's.** What it decided about
the Python apps stands as written: the mirror and the translator share a lock
file and they share the esptool pin, they are one image and not one each, and
a second image of them would be a second answer to which esptool this
repository was tested at. #3 built a page, and a page built by node and served
by nginx shares neither the lock file nor the pin. The single stage that would
have kept it in the one image is a stage carrying both toolchains — which is
the second answer this decision exists to prevent, arriving as a stage instead
of as an image, rather than a way around it. So the page is
`dccex-ui:<commit>`, built by `deploy/ui.Dockerfile` and named by d.1's rule
like everything else here (`compose.yaml`). What d.2 divides on is a
toolchain and not an app: an app that shares the lock file shares the image,
which is every app this repository has. Nothing else of d.2 moves, and nothing
of d.1 does — the commit names both images, which is what lets the amendment
above keep d.7's rollback at one line.

*Amended for [#57](https://github.com/rails49/dccex/issues/57), 2026-09-24:*

**d.4 is both images', and an image nobody named a commit for carries an empty
revision.** d.4 was written when there was one image and says "the image"; the
page's, added by #3 and counted by the amendment above, carried no label at all
until #57 — its name was the only copy of the commit, which is the thing d.4
exists to prevent, and it falls back to `dev`. It carries one now, from a build
argument `compose.yaml` passes the same variable the name is built from, so the
two cannot name different commits.

What d.4 did not say is what the label says when no commit is supplied, which
is what `docker compose up --build` on a clean clone is. It says nothing: the
argument defaults to empty, and no `dev`, `unknown` or `local` goes in it.
`dev` is what such a build is *named*, and a name is where it belongs; a
revision that reads like a commit reference and is none would send somebody
looking for a checkout that never existed, where an empty one can only be read
as nobody having named one. Nothing else of d.4 moves — the label is always
set, and it is still the copy that survives a rename.

The mirror's image defaults that argument to `dev` (`deploy/Dockerfile`, #15),
which this leaves standing. The two images disagree about what an unnamed build
claims to have been built from, and settling that is a ticket of its own.

*Amended for [#97](https://github.com/rails49/dccex/issues/97), 2026-09-24:*

**The ticket of its own above is settled, and the empty revision is both
images'.** The mirror's image defaults the argument to nothing too
(`deploy/Dockerfile`), and `compose.box.yaml`, which is where its build is
declared, passes it `${DCCEX_COMMIT:-}` — the same variable the name is built
from, as `compose.yaml` does for the page. The reasoning is the amendment
above's and is not a second decision: `dev` in a field that means the commit
this was built from is a commit reference that is none, whichever image
carries it, and the two images could not go on answering a `docker inspect`
differently about the same clean clone. Nothing of the names moves — both are
still `dev` where nobody named a commit, which is where `dev` is true — and
what a built image carries is now run rather than read for both of them
(`tests/deploy/test_mirror_serves.py`, `tests/ui/test_page_serves.py`).

*Amended for [#41](https://github.com/rails49/dccex/issues/41), 2026-09-25:*

**d.7's `up -d` is `up -d --no-build`.** Both services have a `build:`, so
compose builds an image it cannot find rather than failing. If the image named
on the line before has been pruned, a plain `up -d` builds whatever the clone
has checked out and names it after the older commit, which is the lie d.4
refuses. With `--no-build` it fails instead. The normal way back is still a
revert and the next deploy; this command is for when that is not at hand.

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
