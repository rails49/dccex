/**
 * The page: the band, the rail and the work pane between them.
 *
 * The work pane is the **monitor** — the station's conversation as it arrives
 * (#4). What the page around it proves is the installation the rest of the UI
 * rests on: it is built by node inside the image, served by nginx out of it,
 * and draws in the look rules (docs/ui/README.md, ADR-0008).
 *
 * The tiles and the releases go above the monitor under their own tickets, and
 * neither changes this: the band and the rail do not vary between rails49 UIs,
 * and the page is the same on a box with a command station and no layout as on
 * the layout box (ADR-0008 d.6).
 */

import { LitElement, html, type TemplateResult } from "lit";

import { appStyles } from "./dccex-app.styles.js";
import "./dccex-band.js";
import "./dccex-monitor.js";
import "./dccex-rail.js";

export class DccexApp extends LitElement {
  static override readonly styles = appStyles;

  override render(): TemplateResult {
    return html`
      <dccex-band></dccex-band>
      <dccex-rail></dccex-rail>
      <div class="work"><dccex-monitor></dccex-monitor></div>
    `;
  }
}

customElements.define("dccex-app", DccexApp);

declare global {
  interface HTMLElementTagNameMap {
    "dccex-app": DccexApp;
  }
}
