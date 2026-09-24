# The mirror's image: this repository's Python, run on a box that has Docker
# and nothing else.
#
# It is **the** image of this repository and not the mirror's alone — the
# translator runs from this one too when it lands, because the two share a
# lock file and the esptool pin `firmware.py` is written against, and a second
# image would be a second answer to what this repository was tested at
# (ADR-0005 d.2). The page is the exception and says why in
# `ui.Dockerfile`: node and nginx share neither.
#
# The name is the commit it was built from — `dccex:<commit>`, and the name
# never moves (ADR-0005 d.1). The commit is on the image as
# `org.opencontainers.image.revision` as well, so `docker inspect` still
# answers the question for one somebody renamed (d.4). **A tag is not what
# this is called**: a tag names a firmware release, which is the thing that
# gets written onto the command station (CONTEXT.md).
#
# Two stages, so that what ships is the interpreter and the packages and not
# the tool that resolved them. The build context is the repository root, as
# `ui.Dockerfile`'s is.

# uv, on the interpreter the runtime stage is. The lock file is what the
# packages come from, so the image is the versions this repository was checked
# at rather than whatever the index had this morning.
#
# The bases here are pinned by tag and not by digest, which the page's are no
# longer (`ui.Dockerfile`, #59). Resolving a digest needs a registry and this
# was written where there is none; inventing one would name an image nobody
# has seen. So this image still has what that ticket describes — a base that
# moves underneath a name ADR-0005 d.1 says never moves — and pinning these
# two is a ticket of its own, wanting a machine that can reach a registry to
# resolve them.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS build

# Copied rather than linked: the venv this stage produces is carried whole
# into the next one, and a hard link into uv's cache does not survive the copy.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# The dependencies in a layer of their own, ahead of the sources, for the
# reason `ui.Dockerfile` does it: the sources change on nearly every commit
# and the lock file seldom does.
#
# `--frozen`: the lock file is honoured rather than updated, so a lock that has
# drifted from `pyproject.toml` stops the build instead of being rewritten
# inside it where nobody would see it. `--no-dev`: pytest, ruff, black and
# pyright are the gate's and are not on a box.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src/ src/

# `--no-editable`: the package is built and installed, so the venv carries it
# and the sources do not have to be in the shipping stage for `python -m
# dccex_usb` to find them.
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.12-slim-bookworm

# What the deploy names the image after, recorded on the image itself
# (ADR-0005 d.4). `dev` is what a clone that has not been told a commit builds
# under, so `up --build` works with nothing set.
ARG DCCEX_COMMIT=dev
LABEL org.opencontainers.image.revision=$DCCEX_COMMIT
LABEL org.opencontainers.image.source=https://github.com/rails49/dccex

# The log is what a box has of this app — connects, disconnects, the device,
# and the line it says on its way up — and it is read with `docker logs`.
# Unbuffered, because a log that arrives when the buffer fills is a log that
# says nothing about a process that has just stopped talking.
ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

COPY --from=build /app/.venv /app/.venv

# Root, because the one thing this process does that no ordinary account can
# is open the command station's device: the node is the host's, its ownership
# is the host's, and a uid invented here would have to match a group on every
# box this ever runs on. What the container reaches is one character device
# and two ports; it dials nothing and it installs nothing.
#
# The flags are the command's, so `docker run dccex:<commit>` is the mirror on
# its own defaults and the stack passes the device and the port it means
# (`compose.box.yaml`). There is no bind address: both servers bind every
# interface and what limits their reach is the LAN (ADR-0042).
ENTRYPOINT ["python", "-m", "dccex_usb"]
CMD ["--device", "/dev/dccex", "--port", "2560"]
