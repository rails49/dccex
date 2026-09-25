/**
 * The tiles: the station's particulars, at the top of the work pane.
 *
 * A light for the **link**, the **build** the station says it is running, and
 * one per track in use, reading its current or `off` — which is what
 * `readings.js`'s `tiles()` returns (CONTEXT.md, **tile**). Every one of them
 * is the station talking, and the reading is the readings module's; this
 * component is handed them and draws them.
 *
 * **The build and the tracks blank together when the link goes down**, and
 * that is the correct reading rather than a gap: the station is not talking.
 * The build blanks hardest — a build held over from before a flash would be
 * the page reporting what it cannot see — and it fills again by itself when
 * the station comes back and says which one it is running, so nothing has to
 * be reloaded after a write (ADR-0008 d.3). The link's own light goes on
 * reading through it: whether the station is answering is the one thing it is
 * for, and it is the reading that says the rest are absent rather than zero.
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
        (shown: Shown) =>
          shown.lit === undefined
            ? html`
                <div class="tile">
                  <span class="of">${shown.of}</span>
                  <span class="reads">${shown.reads}</span>
                </div>
              `
            : html`
                <div class="tile light">
                  <span class="of">${shown.of}</span>
                  <span
                    class="dot ${shown.lit ? "on" : "off"}"
                    role="img"
                    aria-label=${shown.lit ? "answering" : "not answering"}
                  ></span>
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
