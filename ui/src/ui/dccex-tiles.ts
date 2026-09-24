/**
 * The tiles: the station's particulars, at the top of the work pane.
 *
 * Four readings — the **build** the station says it is running, the current on
 * the track, how many **client**s are on the mirror's port, and how long ago
 * the station last said anything (CONTEXT.md, **tile**). Three of them are the
 * station talking and the fourth is the **mirror** answering about itself, and
 * the reading is the readings module's; this component is handed them and
 * draws them.
 *
 * **Three of them blank together when the link goes down**, and that is the
 * correct reading rather than a gap: the station is not talking. The build
 * blanks hardest — a build held over from before a flash would be the page
 * reporting what it cannot see — and it fills again by itself when the station
 * comes back and says which one it is running, so nothing has to be reloaded
 * after a write (ADR-0008 d.3). The clients tile goes on reading through it,
 * because a station that has stopped talking says nothing about who is
 * listening.
 *
 * **The build is here rather than on the band.** It is long, and it belongs
 * beside the releases it gets compared against, which land above the monitor
 * under their own ticket.
 */

import { LitElement, html, type TemplateResult } from "lit";

import { QUIET, asOf, tiles, type Readings, type Shown } from "../readings.js";
import { tilesStyles } from "./dccex-tiles.styles.js";

export class DccexTiles extends LitElement {
  static override readonly styles = tilesStyles;

  static override readonly properties = {
    readings: { attribute: false },
  };

  /** What the page has read off the station. Tiles nobody has handed readings
   *  to are blank, which is what a page that has heard nothing has to show. */
  readings: Readings = asOf(QUIET, 0);

  override render(): TemplateResult {
    return html`
      ${tiles(this.readings).map(
        (shown: Shown) => html`
          <div class="tile">
            <span class="of">${shown.of}</span>
            <span class="reads">${shown.reads}</span>
          </div>
        `,
      )}
    `;
  }
}

customElements.define("dccex-tiles", DccexTiles);

declare global {
  interface HTMLElementTagNameMap {
    "dccex-tiles": DccexTiles;
  }
}
