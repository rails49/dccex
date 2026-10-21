import { css } from "lit";

/**
 * The work pane, inside look's shell: the band, the rail and the strip they
 * turn into on a short window are look's (ADR-0023).
 */
export const appStyles = css`
  :host {
    display: block;
  }

  /* "not built" after the railroad's name on the band (ADR-0028 d.2). */
  .unbuilt {
    color: var(--sl-color-neutral-500);
  }

  /* Where everything the page is about goes: one view, which the rail picks
     (issue 169). The rows are the monitor view's, which is the one with two
     things in it — the tiles across the top, and the monitor under them
     taking the rest of it and scrolling its own lines. The tiles take what
     they need and the pane scrolls once there is more in it than fits.

     The monitor's row is minmax(12rem, 1fr) rather than 1fr. A bare 1fr
     grows to fit what is in it, so a long conversation made the pane scroll
     instead of the lines. The floor keeps a few lines in view on a short
     screen, where the pane scrolls to reach it. */
  .work {
    display: grid;
    height: 100%;
    box-sizing: border-box;
    grid-template-rows: auto minmax(12rem, 1fr);
    min-height: 0;
    overflow: auto;
    background: var(--sl-color-neutral-0);
  }

  /* The releases view is one thing and takes what it needs: a list given the
     height of the pane would put its last row at the foot of the window. */
  .work.releases {
    grid-template-rows: auto;
    align-content: start;
  }

  /* The script view is one thing and takes the whole of the pane: the editor
     in it scrolls its own text, so the pane must not scroll instead of it — a
     page of Python under a window that scrolls puts the Apply control below
     the fold. minmax(0, 1fr) rather than 1fr, because a 1fr track grows to fit
     what is in it: a long script is the row, and its longest line the column. */
  .work.script {
    grid-template-columns: minmax(0, 1fr);
    grid-template-rows: minmax(0, 1fr);
    overflow: hidden;
  }

  /* The journal view is one thing and takes the whole of the pane, as the
     script does: the list in it scrolls its own rows, so the pane must not
     scroll instead of it — an evening's incidents under a window that scrolled
     would put the period and the reload above the fold. */
  .work.journal {
    grid-template-columns: minmax(0, 1fr);
    grid-template-rows: minmax(0, 1fr);
    overflow: hidden;
  }
`;
