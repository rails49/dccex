import { css } from "lit";

/**
 * The **script** view: the railroads down the top, the box under them, and the
 * controls at the foot.
 *
 * It is the work pane's rather than the chrome's, so its colours are
 * Shoelace's theme tokens and it follows the system's light or dark setting
 * (LOOK.md, `theme.ts`). The chrome's six colours stay on the chrome.
 *
 * **The box is monospace and it takes the height it is given.** A script is
 * Python, where the indentation is the structure: a proportional font hides
 * which lines line up, and a box that grew with its text would push the
 * controls off a phone. So the box scrolls and the pane does not.
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
  /* A column, and the box in it takes what is left. A flex column rather than
     a grid of named rows because what is drawn varies — the sentence above the
     box is there for a railroad with no script and not otherwise, and so are
     the warnings — and a row list would give the spare height to whichever
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
     script in the box. Quiet, because it is the page saying what it knows
     rather than a reading. */
  .unlisted,
  .says {
    margin: 0;
    color: var(--sl-color-neutral-500);
    font-family: var(--sl-font-sans);
    font-size: var(--sl-font-size-small);
  }

  /* The box. Monospace, and it scrolls its own text: the pane is the height of
     the window and the controls under it are what a person has to reach. */
  .script {
    flex: 1 1 auto;
    box-sizing: border-box;
    width: 100%;
    min-height: 12rem;
    padding: 0.5rem;
    border: 1px solid var(--sl-color-neutral-300);
    border-radius: var(--sl-border-radius-medium);
    background: var(--sl-color-neutral-0);
    color: var(--sl-color-neutral-900);
    font-family: var(--sl-font-mono);
    font-size: var(--sl-font-size-small);
    line-height: 1.4;
    resize: vertical;
    white-space: pre;
    overflow: auto;
    tab-size: 4;
  }

  /* Apply, and the note beside it where the box is not what was applied. */
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

  /* The railroad this box is showing. Marked by a swap and a weight rather
     than by a colour alone, which is the rule the rail and the release list
     are marked by: a reader who does not see the colour is owed the answer
     too. */
  .railroad {
    background: var(--sl-color-neutral-100);
    color: var(--sl-color-neutral-900);
  }

  .railroad[aria-current] {
    background: var(--sl-color-primary-600);
    color: var(--sl-color-neutral-0);
    font-weight: var(--sl-font-weight-semibold);
  }

  /* That the box holds edits nothing else is holding a copy of. It is a state
     of the page and not a fault, so it is drawn as the warning ink rather than
     as a stop. */
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
