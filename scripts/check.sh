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

set -uo pipefail
cd "$(dirname "$0")/.."

if command -v uv >/dev/null 2>&1 && [ -f uv.lock ]; then
  PY=(uv run --frozen --quiet python)
else
  # No uv: the package is where it lies and pytest is whatever is installed.
  export PYTHONPATH="src${PYTHONPATH:+:$PYTHONPATH}"
  PY=(python3)
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
words() {
  local missing="" word
  for word in station mirror translator face build release tag; do
    grep -q "^## ${word}\$" CONTEXT.md 2>/dev/null || missing="$missing $word"
  done
  compgen -G 'docs/adr/0001-*.md' >/dev/null || missing="$missing ADR-0001"
  if [ -n "$missing" ]; then
    echo "not defined, or not there:$missing"
    return 1
  fi
  echo "station, mirror, translator, face, build, release, tag; ADR-0001"
}

# The copy still says what it is a copy of. A package moved out of another
# repository is only diffable against it while the commit is written down.
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

check syntax "${PY[@]}" -m compileall -q src tests
check words words
check source source_recorded
check tests "${PY[@]}" -m pytest -q

if [ -n "$red" ]; then
  printf 'red:%s\n' "$red"
  exit 1
fi
echo "green"
