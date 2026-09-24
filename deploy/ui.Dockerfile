# The UI's image: node builds the page, nginx serves what came out.
#
# Two stages, because the box's job is a command station. It has Docker and
# nothing else on it — no node, no pnpm, no toolchain to keep in step with this
# repository — and the machine that builds the page is a container that exists
# for the length of the build (ADR-0005, docs/ui/README.md). What ships is the
# second stage: a static server and the files `vite` wrote.
#
# It is not the mirror's image. ADR-0005 keeps one image for this repository
# because the Python apps share a lock file and an esptool pin; a page built by
# node and served by nginx shares neither, and a stage that carried both
# toolchains would be a second answer to what this repository was tested at.
# The naming rule is the same one — the commit it was built from, and the name
# never moves (`compose.yaml`) — and so is the rule under it: the commit is on
# the image as well as in the name, so the name is not the only copy of it
# (ADR-0005 d.4, and `deploy/Dockerfile` does the same).
#
# The build context is the repository root, so this file can see `ui/` and
# `deploy/`. `.dockerignore` keeps `node_modules` and a previous `dist` out of
# it: a host's binaries are not this image's, and a build that copied them in
# would serve whatever was last built on somebody's laptop.
#
# **Both bases are pinned by digest, with the tag kept in front of it.** A tag
# is republished: `node:22-alpine` is whatever was pushed under that name this
# morning, so two builds of this commit a month apart are two different images
# and ADR-0005 d.1 — one commit, one image, one name — holds for the name and
# not for what is under it. A digest names one build of one base and cannot be
# moved, so d.7's path for rebuilding an older commit resolves the bases that
# commit was written against rather than today's. The tag stays because a
# digest says nothing to a reader about what the image is (#59).
#
# What a pin costs is the other half of that, and it is why the digests are
# written down here rather than resolved when the image is built: **a pinned
# base does not pick up its own security updates.** It picks them up when
# somebody moves the pin, and moving it is a commit of this repository like
# any other change to what the image is — reviewed, named by the commit it
# ships under, and gone back on by d.7 like anything else.
#
# To move one, on a machine that can reach a registry:
#
#     docker buildx imagetools inspect node:22-alpine
#
# and the `Digest:` it prints replaces the one below, the tag left as it is.
# The two here are what those tags pointed at on 2026-09-24. Nothing resolves
# them from inside the gate: that needs a registry, and a digest that cannot
# be checked from where it is written is a digest nobody has seen. What the
# gate holds is the shape — `tests/deploy/test_stack.py` reads both lines back
# and asks that neither names something that can move.

FROM node:22-alpine@sha256:0a7108bf6c7bf5de370ffb1a3ed6be93d405b43ff159f681a8d18c0e2bc2e402 AS build

WORKDIR /ui

# pnpm, which is what the project builds pages with (#1, #58), at the version
# `package.json` names. `corepack` reads that field, so the pnpm that installs
# here is the pnpm the lock file was written by rather than whatever the base
# image happens to ship.
RUN corepack enable

# The dependencies in a layer of their own, ahead of the sources. The sources
# change on nearly every commit and the lock file seldom does; a single copy
# would put them in one layer and reinstall packages that did not move.
COPY ui/package.json ui/pnpm-lock.yaml ui/pnpm-workspace.yaml ./

# `--frozen-lockfile`: the lock file is honoured rather than updated, so the
# image is the versions this repository was checked at, and a lock file that
# has drifted from `package.json` stops the build instead of being rewritten
# inside it where nobody would see it. This is also the only place that
# drift is caught: a node runs the page's own functions elsewhere in this
# repository — the decoder's lines put through the real one
# (`tests/ui/test_decoder.py`) — but those checks carry the `node` marker, the
# gate does not collect them (`scripts/check.sh`), and none of them installs
# anything.
RUN pnpm install --frozen-lockfile

COPY ui/ ./

# `tsc --noEmit && vite build`. The type check is part of the build on purpose:
# the box has no node, so this is the one place the page's TypeScript is
# compiled at all, and a type error has to stop the image rather than ship in
# it.
RUN pnpm run build

FROM nginx:alpine@sha256:1ed1b0e1d7652937d6cbdaf4018c7b6fc009a7dd6c3047351e2eddda745de43f

# What the compose project names the image after, on the image itself
# (ADR-0005 d.4). A `docker inspect` on the box then answers what a container
# was built from even for an image somebody renamed, and the name — which is
# the only place this was written before #57 — stops being the only copy of
# the fact.
#
# **The default is empty, and not `dev`.** `dev` is what a clone that has not
# been told a commit builds *under*, and it is a true thing to call a name. In
# a field that means the commit this was built from it would be a commit
# reference that is not one, which is worse than nothing: `docker inspect`
# showing an empty revision is an image nobody named a commit for, and there
# is no reading of it under which some `dev` was checked out. `compose.yaml`
# passes `${DCCEX_COMMIT:-}` — the same variable the name is built from, so
# the name and the label cannot disagree.
ARG DCCEX_COMMIT=
LABEL org.opencontainers.image.revision=$DCCEX_COMMIT

# The page is served, not proxied. The face the page talks to is the mirror's
# and reaches it through the door under the `/dccex-usb` prefix, which the door
# strips (ADR-0004 d.2) — nothing here answers for it and nothing here knows it
# exists.
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=build /ui/dist /usr/share/nginx/html
