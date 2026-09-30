#!/usr/bin/env bash
#
# The deploy: this repository's stack, brought up on the box against the box's
# own declaration.
#
#   ./scripts/deploy.sh
#
# One ssh, one heredoc, one login shell on the other end. It pulls, refuses a
# tree that is not clean, builds the image under the commit it built from,
# brings the project up and appends what it did to the box's record
# (ADR-0005). Nothing here is run on this machine but `ssh`.
#
# **It is not the cutover.** The first time 2560 changes hands on the layout
# box is #16 and is followed from `docs/cutover.md`: `control`'s deploy goes
# first, because that is what removes the orphaned container and repoints the
# translator, and this runs after it. Every time after that is this script and
# nobody watching a train.
#
# **Going back is not this script run backwards** (ADR-0005 d.8). The image it
# replaced is still on the box, so a rollback names the commit on the line
# before and skips the build:
#
#   ssh ttmetro@gleis49.org
#   cd ~/dccex
#   tail -2 /var/lib/rails49/deploys/dccex
#   echo DCCEX_COMMIT=<commit> > .env
#   docker compose -f compose.yaml -f compose.box.yaml \
#     --env-file /etc/rails49/box.env --env-file .env up -d --no-build

set -euo pipefail

# The box, the clone on it and the branch it is brought to. Every one of them
# is overridable, and every one of them has the answer for the box this
# repository is deployed to: a different box or a different branch is an
# ordinary thing to want, and neither of them decides whose code runs.
BOX=${DCCEX_BOX:-ttmetro@gleis49.org}
STACK=${DCCEX_STACK:-dccex}
BRANCH=${DCCEX_BRANCH:-main}

# Where the clone came from, and the one value here the environment has no say
# in (#102). The line below sets the origin rather than believing it, because a
# box whose remote somebody had repointed stopped a deploy dead (control#541) —
# and a variable would hand the shell this was run from exactly the say that
# was taken off the box. So it comes out of the checkout, which is what the
# comment down there claims and what a reader who trusts it can rely on. A
# fork's origin, if it is ever genuinely wanted, is an argument to this script
# rather than something the surrounding environment sets behind it.
ORIGIN=https://github.com/rails49/dccex.git

# The box's declaration of itself: root-owned, edited by hand, and the one
# file every stack on this box is started against. It is not in this
# repository and it is not this script's to write.
BOX_ENV=/etc/rails49/box.env

# What this box has run, one line per deploy, newest last (ADR-0005 d.5).
RECORD=/var/lib/rails49/deploys/dccex

echo "+ ssh $BOX"

# Unquoted, so the names set above are substituted into the script that goes
# over the wire; everything the far end evaluates is written `\$`.
ssh "$BOX" bash -l <<REMOTE
set -euo pipefail

box_env=$BOX_ENV
record=$RECORD
stack=\$HOME/$STACK

# The box guard, before anything is pulled or built. A box that has not been
# declared is not a box this stack knows how to come up on, and coming up on
# the defaults a clean clone uses would serve the page at a host nothing
# resolves and tell the door a domain that is not the box's.
if [ ! -r "\$box_env" ]; then
  echo "no box declaration at \$box_env, or it is not readable." >&2
  echo "This stack is started against that file: it is root-owned, edited by" >&2
  echo "hand, and carries BOX_DOMAIN, BOX_UIS and BOX_ACME_PROVIDER. A box" >&2
  echo "without one is a box the installation has not been run on." >&2
  exit 1
fi

if [ ! -d "\$stack/.git" ]; then
  echo "no clone at \$stack." >&2
  echo "Cloning this repository onto the box is a person's one-time step" >&2
  echo "(rails49/dccex#42), not a deploy's: git clone $ORIGIN \$stack" >&2
  exit 1
fi

cd "\$stack"

# Set rather than trusted, and set to the constant above. A clone somebody
# repointed by hand is a clone that deploys somebody else's commits, and the
# origin is not a thing this script reads off the box — or off the shell it
# was run from — and believes.
#
# A clone with no remote named origin is given one instead of stopping the
# deploy: \`set-url\` fails on such a clone and \`set -e\` aborted here on
# git's terse message rather than on one of this script's own sentences, which
# every other guard gives (#119). The state both lines reach is the one state
# this cares about — the origin is the constant above — and \`set-url\`'s
# complaint is dropped because a clone that has no origin yet is not a thing
# gone wrong.
git remote set-url origin "$ORIGIN" 2>/dev/null ||
  git remote add origin "$ORIGIN"

# No prompt, ever. A deploy that stops on a credential prompt stops holding
# the terminal open with no terminal on the other end of it.
export GIT_TERMINAL_PROMPT=0
git fetch --prune origin
git checkout "$BRANCH"
git merge --ff-only "origin/$BRANCH"

# ADR-0005 d.4: a tree with uncommitted changes in it produces an image whose
# name is a commit that is not what was built. The name would outlive whoever
# typed it, so this refuses rather than lying in one.
dirty=\$(git status --porcelain)
if [ -n "\$dirty" ]; then
  echo "the clone at \$stack is not clean, and the image would be named after" >&2
  echo "a commit that is not what was built (ADR-0005 d.4):" >&2
  echo "\$dirty" >&2
  exit 1
fi

commit=\$(git rev-parse HEAD)

# The record's directory, made before compose is run and as this account, so
# that nothing here arrives later as a root-owned directory the daemon made
# for a bind source that was not there. It is under /var/lib, so the first
# deploy onto a fresh box needs one command from somebody who can write
# there; this says which.
if [ ! -d "\$(dirname "\$record")" ]; then
  if ! mkdir -p "\$(dirname "\$record")" 2>/dev/null; then
    echo "cannot make \$(dirname "\$record") as \$(id -un)." >&2
    echo "Once, as somebody who can write /var/lib:" >&2
    echo "  sudo install -d -o \$(id -un) -g \$(id -gn) \$(dirname "\$record")" >&2
    exit 1
  fi
fi
touch "\$record"

# What the project's own .env says, and whether there is one at all. It is read
# once and kept, because both things this deploy wants of it come out of the one
# text: what is running, and what to put back if the \`up\` fails (#83).
# \`--env-file .env\` is how compose is told which commit, so the new one is
# written before the \`up\` and cannot be written after it — and an \`up\` that
# failed would otherwise leave the file naming a commit that was never brought
# up. A box being deployed onto for the first time has no file, which is the
# line of the record that replaced nothing, and a failed \`up\` must leave it
# with none.
if [ -e .env ]; then had=yes; kept=\$(cat .env); else had=no; kept=; fi

# What is running now, out of that text — the one line that differs between two
# deploys of this repository (ADR-0005 d.7). It names the mirror's image and the
# page's both, because the two are two images of one commit.
was=\$(printf '%s\n' "\$kept" | sed -n 's/^DCCEX_COMMIT=//p' | tail -1)
if [ -n "\$was" ]; then went=dccex:\$was; else went=none; fi

printf 'DCCEX_COMMIT=%s\n' "\$commit" > .env

# --build, because the box builds its own images and pulls none; --remove-orphans,
# because a service that left this project must leave the box with it — which
# is what takes \`control\`'s mirror off 2560 if it is ever brought up by this
# project's name. Nothing is pruned: the image this replaces stays, and it is
# the one step back ADR-0005 d.6 keeps.
#
# A failure here is a deploy that did not happen rather than one that half did:
# .env goes back to what it said, nothing is appended to the record — nothing
# was replaced — and the box is left on the commit it was already running. The
# containers are not rolled back, which is ADR-0005 d.7 and a person's command.
if ! docker compose -f compose.yaml -f compose.box.yaml \
  --env-file "\$box_env" --env-file .env \
  up -d --build --remove-orphans
then
  if [ "\$had" = yes ]; then printf '%s\n' "\$kept" > .env; else rm -f .env; fi
  echo >&2
  echo "docker compose up failed, and dccex:\$commit is not running." >&2
  if [ "\$had" = yes ]; then
    echo "Put .env back to \$went, which is what this box is on." >&2
  else
    echo "Removed .env again: there was none before this run." >&2
  fi
  echo "Nothing was appended to \$record, because nothing was replaced." >&2
  exit 1
fi

# Appended and never rewritten, newest last, plain text for somebody who has
# just been handed the box and has nothing else on it (ADR-0005 d.5).
printf '%s  %-46s  ->  %s\n' \
  "\$(date -u +%Y-%m-%dT%H:%M:%SZ)" "\$went" "dccex:\$commit" >> "\$record"

echo
echo "deployed dccex:\$commit"
tail -2 "\$record"
REMOTE
