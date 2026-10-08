# ADR-0019 — the script is edited in CodeMirror

- **Status:** accepted, 2026-10-08
- **Related:** ADR-0015 (the script is a railroad's document in the store)

## Context

The script view edits a railroad's Python in a `<textarea>`. Tab inserts four
spaces and is the only help. It sets the textarea's value, which clears the
browser's undo history.

A compile error comes back from the face as `line N: message`. A textarea
cannot mark a line.

## Decision

**d.1** The **editor** is CodeMirror 6, built from its modules (view, state,
commands, language, lang-python), not `basicSetup`.

**d.2** It has Python highlighting, indenting on Enter, Tab and Shift-Tab on
a block, Backspace through one indent, Ctrl-/ for comments, line numbers and
bracket matching. It does not close brackets or quotes, and has no search.

**d.3** Highlight colours are Shoelace tokens and follow light and dark.

**d.4** A failed Apply marks the line it names. Any edit clears the mark.

**d.5** CodeMirror is in the main bundle.

## Consequences

- About 100 KB gzipped more on every load.
- The view tests read the editor's state, not a textarea's value. happy-dom
  does not lay CodeMirror out.
- `tabbed()` and `SPACES` in `ui/src/script.ts` go; the indent unit is
  CodeMirror's.

## Considered

- **Textarea with indent keys, no colour.** No dependency. The indenting is
  ours to write and to get right for Python.
- **A highlighted `<pre>` under a transparent textarea** (Prism, CodeJar,
  code-input, or a tokenizer of ours). The most code of ours: the two layers
  must agree on font, wrapping and scroll, and the indent keys are still ours.
- **Monaco.** Megabytes, web workers, and poor in a shadow root.
- **Loading CodeMirror only on the script view.** The view would need a
  loading state.
