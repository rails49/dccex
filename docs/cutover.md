# The cutover: 2560 moves to this repository's stack

The command station's port is served on the layout box by `control`'s copy of
the mirror. This repository holds the mirror now, `control`'s copy is deleted
from its `main` (control#567), and one evening the port changes hands. That
evening is #16. This page is what is followed that evening, and it is written
before it so that nobody composes it with the railroad down.

Read it through first. It is short on purpose, it has blanks that are filled
in the day before, and the order in it is the whole of its value.

**Nothing on this page is done in advance.** What is prepared in advance is
[the day before](#the-day-before), and none of that stops a container, frees a
port or interrupts 2560.

## What hands over

| | before | after |
| --- | --- | --- |
| 2560 | `control`'s mirror container | this repository's, from `dccex:<commit>` |
| the translator | `control`'s, pointed at `control`'s mirror | pointed at this stack's, by control#567's repoint |
| the face | nowhere | `https://dccex.$BOX_DOMAIN/dccex-usb/` ([ADR-0004](adr/0004-the-face-reaches-a-browser-through-the-door-and-never-the-lan.md)) |

The stack that runs it is #15's, the image is named by the commit it was built
from ([ADR-0005](adr/0005-the-image-is-named-by-the-commit-it-was-built-from.md)),
and what the mirror does once it is up is
[the mirror's page](dccex_usb/README.md).

## The day before

Everything here is additive and nothing in it is at risk. A step that fails
here fails with `control`'s mirror still serving 2560, and the answer is
"tomorrow then".

1. `~/dccex` cloned on the box, and this stack's image built there — build
   only, nothing started and nothing stopped, so the window is a swap and not
   a first build.
2. The delta between the box's `control` checkout and `control`'s `main`, read
   and reported on #16. If it carries anything beyond control#567 and the
   translator's repoint, `control` gets an evening of its own first, so that
   the cutover night's deploy is a delta of one known change.
3. **The blanks below, filled in from the box.** They are what the rollback
   needs, they are only on the box, and reading them at midnight is reading
   them from a machine whose port has just changed hands:

   ```
   docker ps --no-trunc --filter name=dccex
   docker inspect <the mirror container>
   ```

   Write down, into the block under [Going back](#going-back): the image's
   `RepoDigests` or `Image` digest, the container's `Cmd` and `Entrypoint`, its
   `Devices`, and what it publishes. `control` deploys by pulling `main` and
   rebuilding, so its image carries no name that means anything (ADR-0005's
   context) — the digest is the only handle on it, and control#567 deleted the
   source, so it cannot be built again.
4. `scripts/deaf_client.py` on whatever laptop is in the room. It is in this
   repository and it is not in the gate.

The first two need the box. When this page was written they had not been done:
the box was not reachable from where it was written, and both went back to the
person rather than being skipped (#42).

**Where those four stand, 2026-09-24** (read over ssh, nothing started and
nothing stopped):

1. **Not done, and not doable yet.** There is no `~/dccex` on the box and no
   image to build there: the stack, the mirror's image and the deploy are
   #15's and #15 is not built. This step waits on it.
2. **Done, and it says wait.** The box's `control` checkout is at `ba611d6`
   (#557) and `control`'s `main` is 31 commits ahead of it. That is far more
   than control#567 and the repoint, so by this page's own rule the cutover
   night's deploy would not be a delta of one known change. Reported on #16,
   where the split point is named.
3. **Done.** The blanks under [Going back](#going-back) are filled, from the
   container that was serving 2560 at the time.
4. Still the person's, on the night. `scripts/deaf_client.py` is in this
   repository.

## The order

**`control`'s deploy first.** Not because it is polite but because it is the
step that frees the port: it removes the orphaned mirror container by the
mechanism control#299 added for exactly this collision, and it applies the
translator's repoint in the same step. A deploy of this stack before it meets
a port that is still held.

1. `control`'s deploy, on the box. When it returns, the mirror container is
   gone and the translator is pointed at `dccex-usb:2560` as this stack will
   serve it.
2. **Check that it is gone and not merely stopped**, below. This is its own
   step because getting it wrong is invisible until a reboot.
3. This stack's deploy: the image built the day before, brought up from
   `/etc/rails49/dccex` (#15, ADR-0005 d.7). It takes 2560 and its face's
   port, and it appends what it replaced to
   `/var/lib/rails49/deploys/dccex`.
4. [The checks](#the-checks), in order, and then the physical acceptance,
   which is a person and a train and is #16's.

### Stopped is not removed

```
docker ps -a --filter name=dccex
```

Nothing stopped may be left behind. Every service on that box is
`restart: unless-stopped` and none of them has a systemd unit, so a container
that was stopped rather than removed comes back at the next reboot and takes
2560 — weeks later, with nobody in the room, and with this stack's mirror
exiting because its port is busy (the mirror's page: a mirror that cannot
serve its port exits). A stopped container is not a cutover that half worked;
it is a cutover that works until the power goes out.

## The abort signal

**Any check below that does not pass, or anyone in the room saying stop.**
That is the whole signal, and it is said out loud rather than inferred: the
person who asked for the window is the one who decides the railroad is in a
state they will leave it in overnight.

On the signal, [go back](#going-back). Not forward, not half: 2560 carries
`control`'s mirror or it carries this stack's, and the state where it carries
neither is the one the layout cannot be left in.

There is no deadline in this page and no step that has to be finished tonight.
Going back is a state the railroad runs in — it ran in it this morning.

## Going back

Going back is putting `control`'s mirror on 2560 again, and it is **not**
ADR-0005's rollback. That one names a commit of this repository and is for a
later deploy of this stack going wrong (ADR-0005 d.7). This one names a digest,
because `control`'s image has no name that says what it is and its source is
deleted from `control`'s `main`:

```
docker rm -f <this stack's mirror container>          # 2560 goes quiet here

docker run -d --name tc49-dccex-usb-1 \
  --restart unless-stopped \
  --network tc49_default \
  --device /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0:/dev/dccex \
  -p 2560:2560 \
  sha256:c41622ef3d4fa1bd6027f945958262fedece9b2ddafc4c38a9b2014371d69af4 \
  python -m tc49.dccex_usb --broker broker:1883 --device /dev/dccex --port 2560
```

Filled in from step 3 of [the day before](#the-day-before) — the digest, the
name, the device and the command the container was running, read off the box
while it was still running them. Read on 2026-09-24 from `tc49-dccex-usb-1`,
up at the time and serving 2560, and the image is the one that container was
created from. The image has never been pushed anywhere, so `RepoDigests`
carries the same `sha256:` its `Id` does; it is a handle on that box's copy
and on no other.

**`--network tc49_default` is not in the skeleton this replaced, and it is not
optional.** `control`'s mirror is a client of the bus and dials the broker by
the name `broker`, which resolves on that network and nowhere else. A rollback
that started it without the network would take 2560 back and publish nothing,
which is the state `control`'s dispatcher reads as the mirror being gone. This
repository's mirror needs no such flag: it has no broker, which is what
ADR-0001 is about. The translator goes back with `control`'s
previous deploy; nothing in this repository repoints it.

**Nothing is pruned until the cutover is accepted.** No `docker image prune`,
no `docker system prune`, nothing removed by hand: the image above is the only
copy of `control`'s mirror that exists anywhere, and a pruned box is a box with
nothing to go back to. After the acceptance in #16 it is the box's to prune.
This repository's own images keep one step back by the deploy's rule rather
than by anybody remembering this line (ADR-0005 d.6).

## The checks

In order. The first three are the port doing its job, and they are what the
acceptance is about.

1. **The orphan is gone**, `docker ps -a` as above, and the deploy record says
   what happened: `tail -2 /var/lib/rails49/deploys/dccex`.
2. **The station answers through the port.** `<s>` asks it what it is; the
   banner coming back names the firmware, the board and the **build**:

   ```
   $ nc <box> 2560
   <s>
   <iDCC-EX V-5.4.16 / ESP32 / EXCSB1_WITH_EX8874 G-9db8d0e>
   ```

3. **Two clients see one conversation.** A second `nc` alongside the first,
   `<s>` sent from one: both see the reply. That is the fan-out, and it is the
   reason the app exists.
4. **DecoderPro reconnects**, as a third client, and the translator reports the
   link up — which is the repoint having landed, not something this stack can
   report on its own behalf.
5. **The face answers through the door**, from a browser on the page's origin:

   ```
   https://dccex.$BOX_DOMAIN/dccex-usb/releases   →   {"tags": [...]}
   ```

   The label, its `A` record and `BOX_UIS` are box steps and a person's
   (ADR-0004 d.6). A face that does not answer is not a reason to go back on
   2560: the port is the railroad and the face is a page.
6. **A client that has stopped reading does not hold the app up.** After the
   swap, never before, because it stops and starts this stack's container. The
   container's log is opened first and left open beside the other two, because
   the mirror's own cut-off is read off it and nowhere else:

   ```
   docker logs -f <this stack's mirror container>            # from the box, left open
   python3 scripts/deaf_client.py --host <box> --port 2560   # says when it is full
   docker stop <this stack's mirror container>               # from the box
   ```

   The container exits well inside Docker's ten-second grace and exits `0`,
   not `137`. A shutdown that waits for that client to take its megabyte waits
   forever; `137` is that wait being killed. Then bring it back up, and
   check 2 and 3 again.

   **There is time, and there is a bound.** The mirror cuts a client off
   itself once more than a megabyte is outstanding to it, which is about a
   minute and a half of the device talking flat out at 115200 8N1
   ([the mirror's page](dccex_usb/README.md#what-it-does-with-the-bytes)).
   That minute and a half is a floor: what fills the deaf client's buffer is
   the station's replies to its own `<s>`, which is a trickle beside flat out,
   so the window between starting the deaf client and the `docker stop` is far
   longer than it. Read the step through and then run it — it is not a race.

   **If the cut-off comes first, the check proved nothing.** The mirror writes
   this line when it drops such a client, the pair in it being the laptop's
   address and the port it dialled from, as the mirror prints them:

   ```
   client disconnected ('192.168.1.47', 51274) too far behind
   ```

   After that line there is no deaf client left to hold the shutdown up, and a
   `docker stop` exits `0` for a reason that has nothing to do with what this
   check is here to prove. Restart `scripts/deaf_client.py` and do the step
   again from the top.

The deaf client says nothing when the mirror goes, and that is expected: the
close is behind bytes it is not taking, so it never arrives. It says nothing
when it is cut off either, and for the same reason — which is why the cut-off
is read off the log above and not off the laptop. What is watched is the
container, on the box.

## The pointer in `control`

`control`'s box procedures are where somebody looks first on the evening of the
window, and the mirror is not `control`'s any more. One line there pointing at
this page is all that is wanted — the procedure is not copied, because a
procedure that exists twice is a procedure with a stale half.

That edit is in another repository. It is a ticket there and **this repository
does not wait on it**: a pointer that has not landed costs a person one search,
and nothing on this page depends on it. To file, verbatim:

```
title: the box procedures point at dccex's cutover page for 2560

The mirror that serves the command station on 2560 moved to rails49/dccex and
this repository's copy is deleted (control#567). On the evening of
rails49/dccex#16 the port changes hands: `control`'s deploy goes first, because
it is what removes the orphaned mirror container (control#299) and applies the
translator's repoint, and the stack that takes the port is rails49/dccex's.

The procedure for that evening — the order, the abort signal, going back, and
the checks — is rails49/dccex `docs/cutover.md`. What is missing is a line in
this repository's box procedures saying so, for the person who opens them that
evening and finds nothing about a port that is no longer served from here.

Acceptance:

- [ ] The box procedures carry a line pointing at rails49/dccex
      `docs/cutover.md` for the cutover of 2560, and at that repository for the
      mirror generally.
- [ ] Nothing of the mirror's own operation is copied into it. A link, not a
      duplicate.
```

Filed as [control#578](https://github.com/rails49/control/issues/578).

## Not on this page

- The window itself — the deploys above being run, the acceptance, and the
  decision to carry on or go back. That is #16, and this page is what it
  follows.
- The stack, the compose file and the deploy: #15's, and this page names them
  rather than containing them.
- `control`'s side of it: the pointer from its box procedures is
  [a ticket there](#the-pointer-in-control) rather than an edit from here.
