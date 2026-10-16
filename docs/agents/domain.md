# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase. This is a single-context repo.

## Before exploring, read these

- `CONTEXT.md` at the repo root: the glossary.
- `docs/adr/`: read ADRs that touch the area you're about to work in.

If either doesn't exist, proceed without comment. Don't flag the absence and don't suggest creating them upfront. The `/domain-modeling` skill creates them when terms or decisions get resolved.

## The glossary is `CONTEXT.md`

The skills call it `GLOSSARY.md`. Here it is `CONTEXT.md` and keeps that name. Where a skill says to read, write or create `GLOSSARY.md`, use `CONTEXT.md`. Don't create a `GLOSSARY.md`. Add entries in `CONTEXT.md`'s own shape (one `##` per word, refused words under **Not:**), not the skills' `GLOSSARY-FORMAT.md`.

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in `CONTEXT.md`. Don't drift to synonyms the glossary rejects.

If the concept you need isn't in the glossary yet, either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/domain-modeling`).

## Flag ADR conflicts

If your output contradicts an existing ADR, say so rather than overriding it:

> _Contradicts ADR-NNNN (<title>), but worth reopening because…_
