#!/usr/bin/env bash
#
# Copies Matt Pocock's skills (https://github.com/mattpocock/skills) into
# .claude/skills/, pinned to one commit. The same copy serves a session on
# your machine and a cloud session: a cloud session does not install the
# plugins a repository's settings turn on, but it does load what the clone
# carries under .claude/skills/. So the plugin is not installed here, and this
# script is how the copy is updated.
#
#   scripts/vendor-skills.sh           # the tip of main
#   scripts/vendor-skills.sh <ref>     # a branch, tag or commit
#
# The skills taken are the ones the plugin lists in its plugin.json. The ones
# a previous run copied are listed in .claude/skills/MATTPOCOCK, and are
# removed first, so a skill dropped upstream is dropped here too and a skill
# of this repository's own is never touched. Review the diff, then commit it.
# The skills are left as they are upstream: what this repository does
# differently (its glossary is CONTEXT.md) is said in CLAUDE.md and
# docs/agents/, not patched into the copy, so the next run does not undo it.

set -euo pipefail

ref="${1:-main}"
repo="https://github.com/mattpocock/skills"
root="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
dest="$root/.claude/skills"
stamp="$dest/MATTPOCOCK"
license="$dest/MATTPOCOCK.LICENSE"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

git clone -q "$repo" "$tmp/src"
git -C "$tmp/src" checkout -q "$ref"
commit="$(git -C "$tmp/src" rev-parse HEAD)"

mkdir -p "$dest"
if [[ -f "$stamp" ]]; then
	sed -n 's/^skill: //p' "$stamp" | while read -r name; do
		rm -rf "${dest:?}/$name"
	done
fi

mapfile -t paths < <(python3 -I -c '
import json, sys
for p in json.load(open(sys.argv[1]))["skills"]:
    print(p)
' "$tmp/src/.claude-plugin/plugin.json")

{
	echo "Copied by scripts/vendor-skills.sh; do not edit by hand."
	echo "source: $repo"
	echo "commit: $commit"
	echo "license: MIT, in MATTPOCOCK.LICENSE"
	for p in "${paths[@]}"; do
		name="$(basename "$p")"
		if [[ -e "$dest/$name" ]]; then
			echo "vendor-skills: $name is already in .claude/skills and is not ours to replace" >&2
			exit 1
		fi
		cp -R "$tmp/src/$p" "$dest/$name"
		echo "skill: $name"
	done
} >"$stamp.new"
mv "$stamp.new" "$stamp"
cp "$tmp/src/LICENSE" "$license"

echo "vendored ${#paths[@]} skills from $repo at $commit"
