# Agent instructions

## Writing
Applies to code comments, commit messages, issues, PR descriptions, comments
and ADRs.

- Plain English. Short declarative sentences, ordinary words.
- Terse and technical. State the fact and the pointer, nothing else.
- No intensifiers or emphasis words (loudly, silently, really, exactly,
  crucially); no bold for emphasis.
- Don't justify a design inside a status line, issue or comment.
  Rationale goes in an ADR, once.
- Don't answer objections nobody raised.

## Agent skills

Matt Pocock's skills are copied into `.claude/skills/`, pinned to the commit in
`.claude/skills/MATTPOCOCK`. Update them with `scripts/vendor-skills.sh`, not by
hand.

### Issue tracker

GitHub Issues on rails49/dccex, via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

The five default labels, unchanged: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` and `docs/adr/` at the repo root. Where a skill names `GLOSSARY.md`, use `CONTEXT.md`. See `docs/agents/domain.md`.
