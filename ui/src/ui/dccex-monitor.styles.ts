import { css } from "lit";

/**
 * The monitor: the station's conversation, newest at the bottom.
 *
 * It is the work pane's rather than the chrome's, so its colours are Shoelace's
 * theme tokens and it follows the system's light or dark setting (LOOK.md,
 * `theme.ts`). The chrome's six colours are `look.css`'s and none of them
 * belongs on a pane.
 *
 * A **gloss** is beside the line and never instead of it: the bytes stay
 * monospaced and dark and the sentence is smaller, quieter and in the page's
 * own face, so that what is being read is what the station said and the page's
 * reading of it is what is offered (ADR-0009).
 *
 * The lines are monospaced and the stamps are tabular, because a column of
 * times that jitters is a column nobody can read down. Nothing wraps off the
 * side: a `<…>` message is short, and a long one is wrapped rather than cut,
 * so what the station said is on the page whole.
 *
 * **What this page sent is marked and coloured**, in a column the station's
 * lines leave empty. Two channels rather than one, because which lines this
 * page put on the railroad is the thing it must never be ambiguous about, and
 * a colour alone is nothing to a reader who does not see it.
 *
 * **The controls sit above the conversation.** A pause and a clear are
 * gestures about the view, so they are outside the scroller and stay where
 * they are as the conversation moves under them, and they are drawn quieter
 * than the send at the foot: what is typed there is what goes on the
 * railroad, and holding a view still or emptying it never leaves the page.
 * Beside them is what the pause is holding back, as a count rather than as
 * lines.
 *
 * **The box at the foot is sized for a thumb.** `--rail-button` is the look
 * rules' minimum for one and it is a size rather than a colour — the chrome's
 * six colours stay on the chrome — so it is the value a box meant to be typed
 * at on a phone held at the layout asks for, and the value the controls above
 * are sized by too. The field takes what is left of the width and may shrink
 * to nothing, so a long command never pushes the send off the side.
 */
export const monitorStyles = css`
  :host {
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
    height: 100%;
    padding: 0.5rem;
  }

  /* The monitor's two controls and what the pause is holding back, above the
     conversation and outside the scroller so that they do not move with it.
     They are drawn quieter than the send at the foot: what is typed there
     goes on the railroad, and holding a view still or emptying it does not
     leave the page. */
  .controls {
    display: flex;
    flex: none;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
  }

  .controls button {
    background: var(--sl-color-neutral-100);
    color: var(--sl-color-neutral-700);
    border: 1px solid var(--sl-color-neutral-300);
    font-size: var(--sl-font-size-small);
  }

  /* How many lines are waiting behind the pause, and how many of those went
     when the queue filled. It is a count and not the lines: the lines are
     what the pause is keeping out of sight. Tabular, because it is a number
     that changes under the eye and a count that jitters is a count nobody can
     read. */
  .waiting {
    color: var(--sl-color-neutral-500);
    font-family: var(--sl-font-sans);
    font-size: var(--sl-font-size-x-small);
    font-variant-numeric: tabular-nums;
  }

  /* The one thing that scrolls. It is given the height and the overflow so
     that following the newest line is a scroll position this component owns,
     rather than the work pane's or the window's.

     Scroll anchoring is off on it (#75). The page drops the oldest lines at
     capacity and the component puts a reader who has scrolled up back on the
     row they were on itself (dccex-monitor.ts); a browser compensating for
     the same trim would be a second hand on the same scroll position — one
     that is best-effort, off in cases of its own and not the same in every
     browser. Off, where the view ends up is this component's arithmetic and
     nobody else's. */
  .lines {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    overflow-anchor: none;
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
    align-items: baseline;
    gap: 0.75rem;
  }

  time {
    flex: none;
    color: var(--sl-color-neutral-500);
    font-variant-numeric: tabular-nums;
  }

  /* Which end of the conversation a line is. It keeps its width whether there
     is a mark in it or not, so the lines stay in one column and what this page
     sent is something to see rather than to work out. */
  .mark {
    flex: none;
    width: 1ch;
    color: var(--sl-color-primary-700);
  }

  /* The line as the station said it: its own spacing kept, and wrapped where
     it is too long for the width rather than run off the side. */
  .said {
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    color: var(--sl-color-neutral-900);
  }

  /* The page's reading of the line, where it has one. It takes what is left
     of the width and wraps in it, so a sentence never pushes the bytes it is
     about off the side. */
  .gloss {
    flex: 1 1 auto;
    min-width: 0;
    color: var(--sl-color-neutral-500);
    font-family: var(--sl-font-sans);
    font-size: var(--sl-font-size-x-small);
  }

  /* The line as this page sent it. Drawn in the page's own accent beside the
     mark, so the two channels agree. */
  .sent .said {
    color: var(--sl-color-primary-700);
  }

  /* Before the station has said anything. It is not an error and not a
     reading — an idle station says nothing until something asks it, and
     nothing does yet (ADR-0010). */
  .quiet {
    color: var(--sl-color-neutral-500);
  }

  /* The box at the foot: the monitor's upward half. */
  .box {
    display: flex;
    flex: none;
    gap: 0.5rem;
    margin-top: 0.5rem;
  }

  /* What is typed. It takes what is left of the width and may shrink to
     nothing, which is what keeps the send button on the page at the width of
     a phone; the typing is monospaced because a message is. The size is the
     medium one rather than the lines' small, because a field below that is a
     field a phone zooms the page into. */
  .typed {
    flex: 1 1 auto;
    min-width: 0;
    box-sizing: border-box;
    min-height: var(--rail-button);
    padding: 0 0.5rem;
    border: 1px solid var(--sl-color-neutral-300);
    border-radius: var(--sl-border-radius-medium);
    background: var(--sl-color-neutral-0);
    color: var(--sl-color-neutral-900);
    font-family: var(--sl-font-mono);
    font-size: var(--sl-font-size-medium);
  }

  /* Sent. It keeps its size whatever the width, because it is the one thing
     on this pane a thumb has to hit. */
  button {
    flex: none;
    box-sizing: border-box;
    min-width: var(--rail-button);
    min-height: var(--rail-button);
    padding: 0 1rem;
    border: none;
    border-radius: var(--sl-border-radius-medium);
    background: var(--sl-color-primary-600);
    color: var(--sl-color-neutral-0);
    font-family: var(--sl-font-sans);
    font-size: var(--sl-font-size-medium);
    cursor: pointer;
  }
`;
