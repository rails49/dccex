/**
 * The tiles: one per track in use, in a row at the top of the monitor view.
 *
 * A tile is one track and four readings of it — whether it has power, what it
 * is set to, the current it draws and the most it may draw — which is what
 * `readings.js`'s `tiles()` answers (CONTEXT.md **tile**, issue 170). Every one
 * of them is the station talking, and the reading is the readings module's;
 * this component is handed them and draws them.
 *
 * **The power is a symbol and the rest are words.** Green where the track has
 * power and red where it has not, grey where the station has said nothing about
 * it — a colour nobody confirmed would be a reading nobody took (ADR-0009 d.2).
 * The same reading is the symbol's label in every state, so a reader who cannot
 * see the colour is given it too, which is how the **link** is drawn on the
 * band (issue 168).
 *
 * **The whole row goes when the link goes down**, and that is the correct
 * reading rather than a gap: a tile is one track, and a station that is not
 * talking is not saying it has any (ADR-0008 d.3). The row keeps its height
 * while it is empty, so the monitor does not move under the reader's thumb at
 * the moment the station goes away. The **link** and the **build** are the
 * **band**'s and are not tiles.
 *
 * **They press nothing** (ADR-0011 d.3). The band's power button is the only
 * control on the page that commands track power outside the flash sequence's
 * own step, and a tile beside it that could be pressed would be a second one.
 */

import { mdiPower } from "@mdi/js";
import { LitElement, html, type TemplateResult } from "lit";

import { QUIET, asOf, tiles, type Readings, type Tile } from "../readings.js";
import "./dccex-icon.js";
import { tilesStyles } from "./dccex-tiles.styles.js";

export class DccexTiles extends LitElement {
  static override readonly styles = tilesStyles;

  static override readonly properties = {
    readings: { attribute: false },
  };

  /** What the page has read off the station. Tiles nobody has handed readings
   *  to are no tiles at all, which is what a page that has heard nothing has
   *  to show. */
  readings: Readings = asOf(QUIET, 0);

  override render(): TemplateResult {
    return html`
      ${tiles(this.readings).map(
        (tile: Tile) => html`
          <div class="tile">
            <span
              class="power ${tile.hot === null ? "" : tile.hot ? "on" : "off"}"
              role="img"
              aria-label=${tile.says}
            >
              <dccex-icon .path=${mdiPower}></dccex-icon>
            </span>
            <span class="mode">${tile.mode}</span>
            <span class="draws">${tile.draws}</span>
            <span class="most">${tile.most}</span>
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
