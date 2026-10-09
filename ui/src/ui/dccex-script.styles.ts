import { css } from "lit";

/**
 * The **script** view: the railroads down the top, the editor under them, and
 * the controls at the foot.
 *
 * It is the work pane's rather than the chrome's, so its colours are Shoelace's
 * theme tokens and it follows the system's light or dark setting (LOOK.md,
 * `theme.ts`). The chrome's six colours stay on the chrome.
 *
 * **The editor is monospace and it takes the height it is given.** A script is
 * Python, where the indentation is the structure: a proportional font hides
 * which lines line up, and an editor that grew with its text would push the
 * controls off a phone. So the editor scrolls and the pane does not.
 *
 * **The editor's own colours are here** and not in the module that builds it:
 * every highlighting tag is given a class and the classes are coloured below,
 * so the view's colours are in one sheet and the sheet is what a check reads
 * (ADR-0019 d.3, `editor.ts`, `tests/ui/test_script.py`). CodeMirror mounts
 * its base rules in this shadow root ahead of these, so a rule here of the
 * same weight wins — which is what the `.cm-` selectors are written to.
 *
 * **The dangerous press is drawn as one**, and the warning above it in the
 * theme's warning ink — the same pair the flash is drawn with, because this is
 * the other gesture on this page that stops a railroad (ADR-0006,
 * `dccex-releases.styles.ts`). The look rules' `--stop` is the chrome's and
 * means a fault or a stop there.
 *
 * **The controls are sized for a thumb.** `--rail-button` is the look rules'
 * minimum for one and it is a size rather than a colour, so it is what a
 * control meant to be pressed on a phone held at the layout asks for.
 */
export const scriptStyles = css`
  /* A column, and the editor in it takes what is left. A flex column rather
     than a grid of named rows because what is drawn varies — the sentence above
     the editor is there for a railroad with no script and not otherwise, and so
     are the warnings — and a row list would give the spare height to whichever
     child happened to land on it. */
  :host {
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
    gap: 0.5rem;
    padding: 0.5rem;
    min-height: 0;
  }

  /* The other view is showing. Written out because the rule above it beats
     the hidden attribute on its own: a host with a display of its own is
     drawn whatever that attribute says. The page hides this pane rather than
     taking it away, so that unapplied edits are still here to come back to
     (dccex-app.ts). */
  :host([hidden]) {
    display: none;
  }

  /* What the view is called. The word is the glossary's. */
  h2 {
    margin: 0;
    color: var(--sl-color-neutral-700);
    font-family: var(--sl-font-sans);
    font-size: var(--sl-font-size-small);
    font-weight: var(--sl-font-weight-semibold);
  }

  /* The railroads the store holds, one to a control. They wrap: a store with
     a dozen railroads is a row that would otherwise run off a phone. */
  .railroads {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem;
    margin: 0;
    padding: 0;
    list-style: none;
  }

  /* What stands in for the list where there is none — a face that could not be
     asked, or a store with no railroads in it — and what is said about the
     script in the editor. Quiet, because it is the page saying what it knows
     rather than a reading. */
  .unlisted,
  .says {
    margin: 0;
    color: var(--sl-color-neutral-500);
    font-family: var(--sl-font-sans);
    font-size: var(--sl-font-size-small);
  }

  /* Where the editor is put. The pane draws this and puts a CodeMirror in it
     (dccex-script.ts), so the rule is about the room it gets and not about
     what is in it. */
  .editing {
    display: flex;
    flex: 1 1 auto;
    min-height: 12rem;
    min-width: 0;
  }

  /* The editor. It scrolls its own text: the pane is the height of the window
     and the controls under it are what a person has to reach. */
  .script.cm-editor {
    flex: 1 1 auto;
    box-sizing: border-box;
    min-width: 0;
    border: 1px solid var(--sl-color-neutral-300);
    border-radius: var(--sl-border-radius-medium);
    background: var(--sl-color-neutral-0);
    color: var(--sl-color-neutral-900);
    overflow: hidden;
  }

  /* Which one has the keyboard, in the theme's own ink rather than the dotted
     outline CodeMirror falls back to. */
  .script.cm-editor.cm-focused {
    outline: 1px solid var(--sl-color-primary-600);
  }

  /* The text, monospace, and it is what scrolls — a long line goes sideways
     inside the editor rather than widening the pane. */
  .script .cm-scroller {
    font-family: var(--sl-font-mono);
    font-size: var(--sl-font-size-small);
    line-height: 1.4;
    overflow: auto;
  }

  /* The caret follows the theme. CodeMirror's base rules set it from a light
     or a dark flag of their own, and this page has neither: the Shoelace
     tokens are what follow the system here (theme.ts). */
  .script.cm-editor .cm-content {
    caret-color: var(--sl-color-neutral-900);
  }

  /* The line numbers, quieter than the text and with a rule between. A
     compile error names a line, so the numbers are what a reader matches it
     against (ADR-0019). The ink is the -700 step, as the token colours below
     are (issue 218). */
  .script.cm-editor .cm-gutters {
    border-right: 1px solid var(--sl-color-neutral-200);
    background: var(--sl-color-neutral-50);
    color: var(--sl-color-neutral-700);
  }

  /* The bracket under the caret and the one that closes it. */
  .script.cm-editor.cm-focused .cm-matchingBracket {
    background: var(--sl-color-primary-200);
  }

  /* The bracket under the caret with no pair, which is every bracket while a
     line is being typed. A neutral wash and not the danger ink: danger in this
     sheet is a line the face refused. @codemirror/language washes it in one
     colour for both themes, which is what this rule replaces (issue 219). */
  .script.cm-editor.cm-focused .cm-nonmatchingBracket {
    background: var(--sl-color-neutral-200);
  }

  /* The line a failed Apply named: the text under a rule carrying the face's
     message, and that line's number told apart in the gutter (ADR-0019 d.4,
     editor.ts). The ink is the one the refusal itself is drawn in at the foot
     of this sheet, and the number is marked by a weight as well as a colour,
     for the reason the picked railroad is. */
  .script.cm-editor .refused {
    text-decoration: underline wavy var(--sl-color-danger-600);
    text-underline-offset: 0.2em;
  }

  .script.cm-editor .refused-line {
    color: var(--sl-color-danger-700);
    font-weight: var(--sl-font-weight-semibold);
  }

  /* What a reader of Python needs told apart (ADR-0019 d.3). The classes are
     the editor's and the colours are the theme's, so both halves follow the
     system's light or dark setting. A tag with no rule here is drawn as the
     text around it.

     Each is the -700 step. Shoelace inverts the scale for the dark theme, so
     a step is read on the editor's background twice, and -700 is the one that
     clears 4.5:1 in both: -600 was 3.2:1 for a decorator in light and 3.9:1
     for a keyword in dark (issue 218, ui/test/editor.test.ts). */
  .tok-keyword {
    color: var(--sl-color-violet-700);
  }

  .tok-string {
    color: var(--sl-color-green-700);
  }

  .tok-comment {
    color: var(--sl-color-neutral-700);
  }

  .tok-number {
    color: var(--sl-color-cyan-700);
  }

  .tok-decorator {
    color: var(--sl-color-amber-700);
  }

  .tok-function {
    color: var(--sl-color-blue-700);
  }

  /* Apply, and the note beside it where the editor is not what was applied. */
  .controls,
  .warning,
  .leaving {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem;
  }

  button {
    flex: none;
    box-sizing: border-box;
    min-height: var(--rail-button);
    padding: 0 0.75rem;
    border: none;
    border-radius: var(--sl-border-radius-medium);
    background: var(--sl-color-primary-600);
    color: var(--sl-color-neutral-0);
    font-family: var(--sl-font-sans);
    font-size: var(--sl-font-size-small);
    cursor: pointer;
  }

  /* One Apply at a time, and nothing to press while the warning it opened is
     open: a control that looked pressable would be a second text stored for
     one press. */
  button[disabled] {
    background: var(--sl-color-neutral-300);
    color: var(--sl-color-neutral-600);
    cursor: default;
  }

  /* The railroad this editor is showing. Marked by a swap and a weight rather
     than by a colour alone, which is the rule the rail and the release list are
     marked by: a reader who does not see the colour is owed the answer too. */
  .railroad {
    background: var(--sl-color-neutral-100);
    color: var(--sl-color-neutral-900);
  }

  .railroad[aria-current] {
    background: var(--sl-color-primary-600);
    color: var(--sl-color-neutral-0);
    font-weight: var(--sl-font-weight-semibold);
  }

  /* That the editor holds edits nothing else is holding a copy of. It is a
     state of the page and not a fault, so it is drawn as the warning ink rather
     than as a stop. */
  .unapplied {
    color: var(--sl-color-warning-700);
    font-family: var(--sl-font-sans);
    font-size: var(--sl-font-size-x-small);
  }

  /* The two warnings: what applying does, and what leaving a railroad with
     unapplied edits does. Each takes its own line above its presses — a
     sentence beside a button is a sentence read after it. */
  .warns {
    flex: 1 0 100%;
    margin: 0;
    color: var(--sl-color-warning-700);
    font-family: var(--sl-font-sans);
    font-size: var(--sl-font-size-small);
  }

  /* The yes to the warning about stopping the railroad, drawn as the dangerous
     press it is, and the yes that discards edits with it. */
  .confirms,
  .discards {
    background: var(--sl-color-danger-600);
  }

  /* And the two ordinary ways out. */
  .cancels,
  .keeps {
    background: var(--sl-color-neutral-100);
    color: var(--sl-color-neutral-900);
  }

  /* What became of the last Apply: the face's sentence, or this page's where
     there was no answer to read. */
  .became {
    margin: 0;
    font-family: var(--sl-font-sans);
    font-size: var(--sl-font-size-small);
  }

  .became.applied {
    color: var(--sl-color-success-700);
  }

  .became.failed {
    color: var(--sl-color-danger-700);
  }
`;
