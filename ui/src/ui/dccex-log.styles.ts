import { css } from "lit";

/**
 * The log: monospace, as the translator wrote it, scrolling inside its own
 * box. Long lines wrap, so a narrow pane beside the editor does not scroll
 * sideways. The face's sentence, where it will not serve the log, is quieter.
 */
export const logStyles = css`
  :host {
    display: flex;
    min-width: 0;
    min-height: 0;
  }

  :host([hidden]) {
    display: none;
  }

  .log {
    flex: 1 1 auto;
    box-sizing: border-box;
    min-width: 0;
    min-height: 6rem;
    margin: 0;
    padding: 0.25rem 0.5rem;
    border: 1px solid var(--sl-color-neutral-300);
    border-radius: var(--sl-border-radius-medium);
    background: var(--sl-color-neutral-0);
    color: var(--sl-color-neutral-900);
    font-family: var(--sl-font-mono);
    font-size: var(--sl-font-size-x-small);
    line-height: 1.4;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    overflow: auto;
  }

  .log.says {
    color: var(--sl-color-neutral-700);
    font-family: var(--sl-font-sans);
  }
`;
