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
# never moves (`compose.yaml`).
#
# The build context is the repository root, so this file can see `ui/` and
# `deploy/`. `.dockerignore` keeps `node_modules` and a previous `dist` out of
# it: a host's binaries are not this image's, and a build that copied them in
# would serve whatever was last built on somebody's laptop.

FROM node:22-alpine AS build

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
# drift is caught: the gate runs a node — to put the decoder's lines through
# the real function (`tests/ui/test_decoder.py`) — but it installs nothing.
RUN pnpm install --frozen-lockfile

COPY ui/ ./

# `tsc --noEmit && vite build`. The type check is part of the build on purpose:
# the box has no node, so this is the one place the page's TypeScript is
# compiled at all, and a type error has to stop the image rather than ship in
# it.
RUN pnpm run build

FROM nginx:alpine

# The page is served, not proxied. The face the page talks to is the mirror's
# and reaches it through the door under the `/dccex-usb` prefix, which the door
# strips (ADR-0004 d.2) — nothing here answers for it and nothing here knows it
# exists.
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=build /ui/dist /usr/share/nginx/html
