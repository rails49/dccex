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

### Issue tracker

GitHub Issues on rails49/dccex, via the `gh` CLI. See
`docs/agents/issue-tracker.md`.

### Triage labels

The five default labels, unchanged: `needs-triage`, `needs-info`,
`ready-for-agent`, `ready-for-human`, `wontfix`. See
`docs/agents/triage-labels.md`.

### Domain docs

Single-context: `GLOSSARY.md` and `docs/adr/` at the repo root. See
`docs/agents/domain.md`.

What each kind of doc holds: org
[ADR-0021](https://github.com/rails49/.github/blob/main/docs/adr/0021-each-fact-has-one-owner-and-the-glossary-is-glossary-md.md).
