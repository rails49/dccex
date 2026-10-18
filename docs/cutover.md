# The cutover: 2560 moves to this repository's stack

The command station's port was served on the layout box by `control`'s copy of
the mirror. This repository holds the mirror now, `control`'s copy is deleted
from its `main` (control#567), and the port changed hands at #16, closed on
2026-10-11. This page is the procedure that was followed and a record of what
happened.

**It was a cold changeover, and it stopped being a live one on 2026-09-24.**
The railroad was not in use while the work went on, so the box was brought
down, everything on it was brought up to date, and it was started again.
Nothing was timed, and 2560 was allowed to be dark for as long as the work
took. An earlier version of this page was written for a swap performed while
the railroad ran: it had a fifteen-minute abort deadline, an order that existed
to keep the port held for as short a time as possible, and a rollback pasted
from a container that was still running. None of that was needed, and what
replaced it is below.

The order was kept anyway — not because the port was precious, but because a
failure is only diagnosable if the changes go in one at a time.

## What hands over

| | before | after |
| --- | --- | --- |
| 2560 | `control`'s mirror container | this repository's, from `dccex:<commit>` |
| the translator | `control`'s, pointed at `control`'s mirror | pointed at this stack's, by control#567's repoint |
| the face | nowhere | the page's container came up with the stack, and #40 made it reachable ([ADR-0004](adr/0004-the-face-reaches-a-browser-through-the-door-and-never-the-lan.md)) |

The stack that runs it is this repository's own — `compose.yaml` with
`compose.box.yaml` over it, brought up by `scripts/deploy.sh` (#15) — the image
is named by the commit it was built from ([ADR-0005](adr/0005-the-image-is-named-by-the-commit-it-was-built-from.md)),
and what the mirror does once it is up is
[the mirror's page](dccex_usb/README.md).

## The day before

Everything here was additive and nothing in it was at risk. A step that
failed here failed with `control`'s mirror still serving 2560.

**Cold, none of this was a prerequisite.** It was, when the window was minutes
long and building the image inside it was the difference between a swap and an
outage. Cold, it was preparation that made the evening shorter.

1. `~/dccex` cloned on the box, and this stack's image built there — nothing
   started and nothing stopped, so the evening was a deploy and not the
   first time the image was built.
2. The delta between the box's `control` checkout and `control`'s `main`, read
   and reported on #16 — so that what went onto the box that evening was known
   before it went on, and so that a railroad which misbehaved afterwards had a
   list to read. It no longer had to be a delta of one change: that rule was
   the live swap's, and what it bought was a short list to bisect in a hurry.
   Cold, the list could be long, because [the order](#the-order) checked
   `control` on its own before the port moved.
3. **The blanks below, filled in from the box.** They were what the rollback
   needed, they were only on the box, and reading them after the swap would
   have been reading them from a machine whose port had just changed hands:

   ```
   docker ps --no-trunc --filter name=dccex
   docker inspect <the mirror container>
   ```

   Written down, into the block under [Going back](#going-back): the image's
   `RepoDigests` or `Image` digest, the container's `Cmd` and `Entrypoint`, its
   `Devices`, and what it published. `control` deploys by pulling `main` and
   rebuilding, so its image carries no name that means anything (ADR-0005's
   context) and the id was the only handle on that box's copy. It was a
   convenience and not the way back: the way back was a commit of `control`,
   which [Going back](#going-back) gives.
4. `scripts/deaf_client.py` on whatever laptop was in the room. It is in this
   repository and it is not in the gate.

The first two needed the box. The box was not reachable from where this page
was first written, and both went back to the person rather than being skipped
(#42).

**Where those four stand, 2026-09-24** (read over ssh, nothing started and
nothing stopped):

1. **Not done.** There was no `~/dccex` on the box and so no image built
   there. What it waited on had landed: the mirror's image, the compose overlay
   and the deploy are #15's. What was left was the clone, building the image on
   the box, and the deploy record's directory, which did not exist and needed
   somebody who can write `/var/lib` once:
   `sudo install -d -o ttmetro -g ttmetro /var/lib/rails49/deploys`.
2. **Done.** The box's `control` checkout is at `ba611d6` (#557) and
   `control`'s `main` is 31 commits ahead of it — the store moving to loopback,
   broker-first startup, the store image's uid and table ownership, the stock
   screen, control#567's six, and the repoint. Reported on #16 with the list.
   Under the live plan that was a reason to wait for an evening of `control`'s
   own; cold it was not, and the order below is what replaced it.
3. **Done.** The blanks under [Going back](#going-back) were filled, from the
   container that was serving 2560 at the time.
4. Left to the person, on the night.

## The order

**`control`'s deploy first**, and then this stack's. On a live swap the reason
was the port: `control`'s deploy is what removed the orphaned mirror container,
by the mechanism control#299 added for this collision, and what applied the
translator's repoint. Cold, the port was free either way. The reason to keep the
order was diagnosis: `control`'s delta and this repository's new stack are two
unrelated bodies of change, and a railroad that misbehaves after both went in
at once is a railroad with two suspects.

1. **Done on 2026-09-24, days before the evening** (reported on #16).
   `control`'s deploy, on the box, and **the railroad checked before the mirror
   moved**: the box came up on `control`'s `main` with `control`'s own mirror
   gone and this stack not yet there. 2560 was dark at this point and that was
   expected. What was checked was everything that is not 2560 — the store
   answers, the apps stand, the door serves `control`'s UI. That check is what
   made the next step's failures this repository's.
2. **Check the old mirror container is gone and not merely stopped**, below.
   Getting it wrong is invisible until a reboot. Checked on 2026-09-24:
   `tc49-dccex-usb-1` was *Removed*, and only the translator was left.
3. This stack's deploy: `scripts/deploy.sh`, which brings the project up from
   the clone against `/etc/rails49/box.env` (#15, ADR-0005 d.7). It takes 2560
   and brings the page's container up beside it, and it appends what it replaced to
   `/var/lib/rails49/deploys/dccex`. Run on 2026-09-25.
4. [The checks](#the-checks), in order, and then the physical acceptance,
   which was a person and a train and was #16's.

`control`'s delta was read before the evening and reported on #16 (#42). It did
not have to be a delta of one change any more — that rule was a live swap's, and
its point was that there is no time to bisect with the railroad down. What was
kept from it is step 1 above: deploy `control`, check `control`, and only then
move the port.

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

**Anyone in the room saying stop.** That was the whole signal, and it was to
be said out loud rather than inferred.

A failing check was not an abort signal. Cold, it was something to look at,
and looking at it cost a dark port that nothing was waiting on. Fix forward, or
[go back](#going-back) and come at it another evening — both were ordinary, and
neither was urgent.

What the signal was still for was the state of the layout when everyone left.
The one thing worth not leaving behind was a box that would surprise somebody:
half a stack up, a container that was stopped rather than removed, or a port
held by something nobody remembers starting. Going back was a state the
railroad had run in until that day.

## Going back

Going back was putting `control`'s mirror on 2560 again. It was **not**
ADR-0005's rollback. That one names a commit of this repository and is for a
later deploy of this stack going wrong (ADR-0005 d.7).

**The way back is a commit of `control`, and this page used to say it was not.**
It said `control`'s image "cannot be built again" because control#567 deleted
the source. That is true of `control`'s `main` and false of `control`'s
history: `ba611d6` — what the box was checked out at on 2026-09-24, and an
ancestor of `main` — carries `src/tc49/dccex_usb`, `deploy/app.Dockerfile` and
the `dccex-usb` service, all three. So the whole of the old world rebuilds from
a public repository:

```
cd ~/control
git checkout ba611d6            # or any commit before control#567
docker compose --profile hardware -f deploy/compose.yaml up -d --build
```

That was the rollback to reach for. It restored the mirror *and* the translator
pointing at it, from source, with no digest to transcribe and nothing that
depends on one box's unpushed image surviving a prune. It leaves `control`'s
checkout on a detached head, which the next deploy corrects by pulling.

The block below was the faster path: it needed no rebuild. It runs the image
that was serving 2560 on 2026-09-24, by the id it has on that box and nowhere
else:

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
previous deploy; nothing in this repository repoints it. Since #189 this stack
runs a translator too, so stop it first, as under
[The translator alone](#the-translator-alone).

**Nothing was pruned until the cutover was accepted.** No `docker image prune`,
no `docker system prune`, nothing removed by hand. Not because a prune would
destroy the way back — it would not, the checkout above rebuilds it — but for
two smaller reasons that both landed on the one evening it would matter. A prune
turns a five-second rollback into a ten-minute one. And **the rebuild is
equivalent rather than identical**: `control`'s image is
`FROM python:3.12-slim` with an unpinned `apt-get install`, so the base and the
Debian packages resolve at build time even though `uv sync --frozen` pins the
Python side. The image on the box was the one that had been serving the
railroad; a rebuild is an image that should. On an evening spent deciding
whether something is broken, that difference was worth keeping on disk. Since
the acceptance in #16 it is the box's to prune.
This repository's own images keep one step back by the deploy's rule rather
than by anybody remembering this line (ADR-0005 d.6).

### The translator alone

Since #189 the translator runs from this stack and `control` has none. To put
`control`'s translator back while this stack's mirror keeps 2560, stop this
stack's translator first, so that two translators are never on the bus:

```
cd ~/dccex
docker compose -f compose.yaml -f compose.box.yaml \
  --env-file /etc/rails49/box.env --env-file .env rm -sf translator
cd ~/control
git checkout 02839e0^           # the last commit with the translator
docker compose --profile hardware -f deploy/compose.yaml up -d --build
```

`control`'s translator asks for `host.docker.internal:2560`, which is this
stack's published mirror.

## The checks

Run in order. The first three are the port doing its job, and they were what
the acceptance was about.

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
5. **The face was not checked here.** The page's container came up with the
   stack, but nothing reached it until its `A` record and `BOX_UIS` entry
   existed, and those were #40's. The port is the railroad and the face is a page.
6. **A client that has stopped reading does not hold the app up.** After the
   swap, never before, because it stops and starts this stack's container. The
   container's log is opened first and left open beside the other two, because
   the mirror's own cut-off is read off it and nowhere else:

   ```
   docker logs -f <this stack's mirror container>            # from the box, left open
   python3 scripts/deaf_client.py --host <box> --port 2560   # says when it is full
   time docker stop <this stack's mirror container>          # from the box
   ```

   **The stop is timed, and five seconds is the bound.** `time` is on the
   `docker stop` because the clock is what this check reads. A healthy stop
   comes back in about a second — the app closes its face, aborts what its
   clients have not taken and lets the device go — and a `real` under five
   seconds is the pass, with the container's exit status `0` beside it, read
   where check 1 read `docker ps -a`.

   **The configured 330 seconds are a flash's, and are not this.**
   `compose.box.yaml` gives this container `stop_grace_period: 330s`, because
   `firmware.py` allows esptool 300 seconds to write the station and a
   container killed in the middle of a write leaves the station half written
   (#15). That is the room a flash is given, not what a shutdown is expected
   to take, and nothing is being written at this point in the evening: the two
   numbers measure different things, and this step is held to the five seconds
   above rather than to the grace. A stop still running at five has already
   failed it — the shutdown is waiting for the deaf client to take its
   megabyte, which is a wait that does not end. Left alone it comes back five
   and a half minutes later with the container dead of `137`, the same fault
   read off an exit status instead of off a clock, and there is no reason to
   stand there for it.

   Then bring it back up, and check 2 and 3 again.

   **There is time before the stop, and a limit on it.** The mirror cuts a
   client off itself once more than a megabyte is outstanding to it, which is
   about a minute and a half of the device talking flat out at 115200 8N1
   ([the mirror's page](dccex_usb/README.md#what-it-does-with-the-bytes)).
   That minute and a half is a floor: what fills the deaf client's buffer is
   the station's replies to its own `<s>`, which is a trickle beside flat out,
   so the window between starting the deaf client and the `docker stop` is far
   longer than it. Read the step through and then run it — it is not a race.

   **Stop only after the deaf client prints `full`.** Until then it may not
   be connected at all. On 2026-09-25 the Python `uv` manages was refused the
   LAN by macOS ("Network is unreachable", while `nc` reached 2560), the
   client never connected, and the first timed stop proved nothing.
   `/usr/bin/python3` reached it, and filled in 57 seconds.

   **If the cut-off comes first, the check proved nothing.** The mirror writes
   this line when it drops such a client, the pair in it being the laptop's
   address and the port it dialled from, as the mirror prints them:

   ```
   client disconnected ('192.168.1.47', 51274) too far behind
   ```

   After that line there is no deaf client left to hold the shutdown up, and a
   `docker stop` comes back inside the bound for a reason that has nothing to
   do with what this check is here to prove. Restart `scripts/deaf_client.py` and do the step
   again from the top.

The deaf client says nothing when the mirror goes, and that is expected: the
close is behind bytes it is not taking, so it never arrives. It says nothing
when it is cut off either, and for the same reason — which is why the cut-off
is read off the log above and not off the laptop. What is watched is the
container, on the box.

## The pointer in `control`

`control`'s box procedures were where somebody would look first on the
evening, and the mirror is not `control`'s any more. One line there pointing at
this page was all that was wanted; the procedure was not copied.

That edit was in another repository, so it was a ticket there, filed verbatim:

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

Filed as [control#578](https://github.com/rails49/control/issues/578), closed
on 2026-09-25.

## What happened, 2026-09-25

- `control`'s half went in on 2026-09-24, so the evening was this stack alone.
- `main` had moved past the clone the page was checked against: `86ea539`
  (#40) gave the face its door route. That is what was deployed. The face has
  no `A` record yet, so no browser reaches it by name.
- The deploy record's directory needed the one `sudo` above.
- Checks 1–4 and 6 passed. Check 6: full after 57 s, `docker stop` in 0.26 s,
  exit 0. The banner read `V-5.6.4 / ESP32 / EXCSB1_WITH_EX8874
  G-v5.6.4-rails49.1`.
- From the laptop the broker answered at `192.168.178.56` and not at
  `gleis49.org`, which gave "no route to host".
- A person connected on 2560 and drove a locomotive.

## What happened, 2026-10-01

- #189: `control` was deployed at its `main`, and `--remove-orphans` removed
  `tc49-dccex-1`. This stack was then deployed at `9b5947e`, and
  `dccex-translator-1` came up next to the mirror.
- The startup file on the box was kept as it was.
- `device/link/dccex` read up, connected to `mirror:2560`. A power ON from
  `control`'s UI reached the track in two seconds.
- `store:8765` resolves from this stack on the `rails49` network and answers.

## Not on this page

- The evening itself — the deploys above being run, the acceptance, and the
  decision to carry on or go back. That is #16, and this page is what it
  followed.
- The stack, the compose files and the deploy: built in #15 —
  `deploy/Dockerfile`, `compose.box.yaml` and `scripts/deploy.sh` — and this
  page names them rather than containing them.
- `control`'s side of it: the pointer from its box procedures is
  [a ticket there](#the-pointer-in-control) rather than an edit from here.
