#!/usr/bin/env bash
#
# The gate: what CI runs on every pull request, and what you run here before
# you push. One command and one exit code, and every check runs even after one
# has gone red, so a single run names everything that is wrong rather than the
# first thing.
#
# Nothing here needs the command station. The mirror's tests open a pty and
# get a device they can open for real, and the flash injects what fetches a
# URL and what runs esptool, so the gate reaches no release API and writes no
# hardware. A test that does need the cable, a local service or a secret must
# skip itself when CI is set; that is the whole contract between this script
# and the workflow.
#
# Nothing here needs a Docker daemon either, and that is a rule with a
# mechanism rather than a habit: a test that needs one carries the `docker`
# marker and this script does not collect it (`-m "not docker"` below). The
# workflow runs those in a job of its own, required on the pull request, where
# a missing daemon is a failure and not a skip (#54, #56). Two reasons for the
# split. This gate is seconds and a daemonless machine — the agent sandbox is
# one — must still be able to run all of it. And a check that may skip itself
# is a check that can leave a required gate green while proving nothing, which
# is what `tests/ui/test_page_serves.py` did in every run recorded before this.
#
# A `node` marker is the same mechanism for the same reason, and this script
# does not collect it either (`-m "not docker and not node"`). Seven modules of
# the page are written as JavaScript so a bare node can run them, and what
# they assert is put through the real function rather than read off the source
# that would produce it — worth a node somewhere, and not worth a node on
# every machine this gate runs on (#101). The workflow runs those too, in a
# job of its own required on the pull request.
#
# **One thing it does fetch, once per environment.** `pyright` is distributed as
# a wrapper: the first time it runs in an environment it downloads a node and
# its own npm package into it, which is the `Install prebuilt node` line in the
# output. It is cached there, so a second run is silent and a machine with no
# network runs the whole gate as long as its environment already exists — but a
# cold `uv sync` and a cold gate do reach the network, and CI does it on every
# run because it builds the environment from scratch. The type checker stays in
# the gate regardless: a gate that dropped it to avoid a download would be
# green while proving less, which is the thing this script says twice above.

set -uo pipefail
cd "$(dirname "$0")/.."

if command -v uv >/dev/null 2>&1 && [ -f uv.lock ]; then
  PY=(uv run --frozen --quiet python)
  tool() { uv run --frozen --quiet "$@"; }
else
  # No uv: the package is where it lies and the tools are whatever is
  # installed. A tool that is not there is red rather than skipped — a gate
  # that passes by not running its type checker says nothing.
  export PYTHONPATH="src${PYTHONPATH:+:$PYTHONPATH}"
  PY=(python3)
  tool() { "$@"; }
fi

red=""

check() {
  local name=$1
  shift
  printf '== %s\n' "$name"
  if "$@"; then
    printf '== %s green\n\n' "$name"
  else
    red="$red $name"
    printf '== %s RED\n\n' "$name"
  fi
}

# The words the repository says it defines, still defined, and the decision
# still written down. Cheap, and it is the part of the vocabulary a machine
# can hold us to.
#
# All eighteen of them. The list held eight for as long as there were eight,
# and the ten that arrived with the page were never added, so deleting `##
# client` left the gate green while #7 leaned on the word (#91). It is written
# out rather than read off `CONTEXT.md`'s headings, because a check that took
# its list from the file it is checking would pass on whatever that file said —
# the same reason `ROUTE` is written out in `tests/ui/test_compose_serves.py`.
words() {
  local missing="" word
  local -a defined=(
    station mirror translator face build release tag client stream
    link monitor decoder gloss band rail tile image cutover
  )
  for word in "${defined[@]}"; do
    grep -q "^## ${word}\$" CONTEXT.md 2>/dev/null || missing="$missing $word"
  done
  compgen -G 'docs/adr/0001-*.md' >/dev/null || missing="$missing ADR-0001"
  if [ -n "$missing" ]; then
    echo "not defined, or not there:$missing"
    return 1
  fi
  local joined="${defined[*]}"
  echo "${joined// /, }; ADR-0001"
}

# The code still says where it was written. `control` deleted its side, so
# this is provenance and not a promise (ADR-0003) — but a commit nobody
# wrote down is a provenance nobody can check.
source_recorded() {
  local commit="deee7b6f54d0215f4e02c128e60f50322fd0978c"
  if ! grep -q "rails49/control" src/SOURCE.md 2>/dev/null; then
    echo "src/SOURCE.md does not name rails49/control"
    return 1
  fi
  if ! grep -q "$commit" src/SOURCE.md; then
    echo "src/SOURCE.md does not record the commit the copy was taken at"
    return 1
  fi
  echo "rails49/control at ${commit:0:7}"
}

# ruff, black and pyright are `control`'s, over the same `src` and `tests`
# and configured in `pyproject.toml` exactly as they are there. The code came
# across written for them, and `__main__.py` — the one file here that is not a
# copy — is the one nobody else has ever type-checked.
check syntax "${PY[@]}" -m compileall -q src tests
check words words
check source source_recorded
check ruff tool ruff check .
check black tool black --check .
check pyright tool pyright
check tests "${PY[@]}" -m pytest -q -m "not docker and not node"

if [ -n "$red" ]; then
  printf 'red:%s\n' "$red"
  exit 1
fi
echo "green"
