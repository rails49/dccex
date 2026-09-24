import { css } from "lit";

/**
 * The monitor: the station's conversation, newest at the bottom.
 *
 * It is the work pane's rather than the chrome's, so its colours are Shoelace's
 * theme tokens and it follows the system's light or dark setting (LOOK.md,
 * `theme.ts`). The chrome's four values are `look.css`'s and none of them
 * belongs on a pane.
 *
 * The lines are monospaced and the stamps are tabular, because a column of
 * times that jitters is a column nobody can read down. Nothing wraps off the
 * side: a `<…>` message is short, and a long one is wrapped rather than cut,
 * so what the station said is on the page whole.
 */
export const monitorStyles = css`
  :host {
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
    height: 100%;
    padding: 0.5rem;
  }

  /* The one thing that scrolls. It is given the height and the overflow so
     that following the newest line is a scroll position this component owns,
     rather than the work pane's or the window's. */
  .lines {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    box-sizing: border-box;
    padding: 0.25rem 0.5rem;
    border: 1px solid var(--sl-color-neutral-200);
    border-radius: var(--sl-border-radius-medium);
    background: var(--sl-color-neutral-50);
    font-family: var(--sl-font-mono);
    font-size: var(--sl-font-size-small);
    line-height: var(--sl-line-height-dense);
  }

  .line {
    display: flex;
    gap: 0.75rem;
  }

  time {
    flex: none;
    color: var(--sl-color-neutral-500);
    font-variant-numeric: tabular-nums;
  }

  /* The line as the station said it: its own spacing kept, and wrapped where
     it is too long for the width rather than run off the side. */
  .said {
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    color: var(--sl-color-neutral-900);
  }

  /* Before the station has said anything. It is not an error and not a
     reading — an idle station says nothing until something asks it, and
     nothing does yet (ADR-0010). */
  .quiet {
    color: var(--sl-color-neutral-500);
  }
`;
