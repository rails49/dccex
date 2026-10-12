import { css } from "lit";

/**
 * The journal view's controls: one row of them above the table.
 *
 * They are the work pane's rather than the chrome's, so their colours are
 * Shoelace's theme tokens and they follow the system's light or dark setting
 * (LOOK.md, `theme.ts`). The chrome's six colours stay on the chrome.
 *
 * **They wrap rather than running off the side**, and each is sized for a
 * thumb: `--rail-button` is the look rules' minimum for one, which is what a
 * control pressed on a phone held at the layout asks for
 * (`dccex-monitor.styles.ts`, `ui/look/README.md`).
 *
 * **The yes is drawn as the dangerous press it is**, and the warning above it
 * in the theme's own warning ink — the way a flash's is
 * (`dccex-releases.styles.ts`). Clearing the journal is the one gesture on
 * this view that throws something away, and nothing behind the page guards it
 * (ADR-0006).
 */
export const controlsStyles = css`
  :host {
    display: block;
    box-sizing: border-box;
    padding: 0.5rem;
    border-bottom: 1px solid var(--sl-color-neutral-200);
  }

  .controls {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem;
    font-family: var(--sl-font-sans);
    font-size: var(--sl-font-size-small);
  }

  /* The chooser and the toggle, each with its word beside it: a control whose
     word is only a tooltip is a control a reader has to press to understand. */
  label {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    box-sizing: border-box;
    min-height: var(--rail-button);
    color: var(--sl-color-neutral-700);
  }

  /* Which lines are read: the three spans and the builds in the file. */
  .choices {
    box-sizing: border-box;
    min-height: var(--rail-button);
    max-width: 14rem;
    padding: 0 0.5rem;
    border: 1px solid var(--sl-color-neutral-300);
    border-radius: var(--sl-border-radius-medium);
    background: var(--sl-color-neutral-0);
    color: var(--sl-color-neutral-900);
    font-family: var(--sl-font-sans);
    font-size: var(--sl-font-size-small);
  }

  /* The toggle itself, at the size a thumb can hit. */
  .toggle {
    width: 1.25rem;
    height: 1.25rem;
    margin: 0;
  }

  /* How big the file is, and the link that keeps a copy of it. Both are
     quieter than the presses: they say what is there rather than doing
     something to it. */
  .size {
    color: var(--sl-color-neutral-500);
    font-size: var(--sl-font-size-x-small);
    font-variant-numeric: tabular-nums;
  }

  .downloads {
    display: flex;
    align-items: center;
    box-sizing: border-box;
    min-height: var(--rail-button);
    color: var(--sl-color-primary-700);
  }

  /* What is pressed: the reload, the clear, and the two the warning asks
     with. They keep their size whatever the width, because that size is what a
     thumb has to hit. */
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

  /* Nothing to press while the warning the press opened is open. */
  button[disabled] {
    background: var(--sl-color-neutral-300);
    color: var(--sl-color-neutral-600);
    cursor: default;
  }

  /* The warning, and the two presses that answer it. It takes the whole width
     under the controls, so what is being thrown away is never off the side of
     the sentence about throwing it away. */
  .warning {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0 0.25rem;
  }

  /* What clearing does. It takes its own line above the presses: a sentence
     beside a button is a sentence read after it. */
  .warns {
    flex: 1 0 100%;
    margin: 0;
    color: var(--sl-color-warning-700);
    font-family: var(--sl-font-sans);
    font-size: var(--sl-font-size-small);
  }

  /* The yes, drawn as the dangerous press it is, and never the quieter of the
     two. */
  .confirms {
    background: var(--sl-color-danger-600);
  }

  /* And the no, which is the ordinary way out of a warning. */
  .cancels {
    background: var(--sl-color-neutral-100);
    color: var(--sl-color-neutral-900);
  }

  /* What became of the last clear, in the face's own words. */
  .says {
    margin: 0.5rem 0 0;
    color: var(--sl-color-neutral-700);
    font-family: var(--sl-font-sans);
    font-size: var(--sl-font-size-small);
  }
`;
