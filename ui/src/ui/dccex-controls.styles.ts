import { css } from "lit";

/**
 * The journal view's controls: one row of them above the table.
 *
 * They are the work pane's rather than the chrome's, so their colours are
 * Shoelace's theme tokens and they follow the system's light or dark setting
 * (`look.css`). The chrome's colours stay on the chrome.
 *
 * **They wrap rather than running off the side**, and each is sized for a
 * thumb: `--rail-button` is the look rules' minimum for one, which is what a
 * control pressed on a phone held at the layout asks for
 * (`dccex-monitor.styles.ts`).
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

  /* Which lines are read: the spans, the builds and the days in the file. */
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

  /* What is pressed: the reload. It keeps its size whatever the width,
     because that size is what a thumb has to hit. */
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
`;
