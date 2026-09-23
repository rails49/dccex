/**
 * The page: the band, the rail and the work pane between them.
 *
 * Nothing is in the work pane. What this proves is the installation the rest
 * of the UI rests on — the page is built by node inside the image, served by
 * nginx out of it, and draws in the look rules from its first commit
 * (docs/ui/README.md, ADR-0008).
 *
 * The tiles, the releases and the monitor land in the work pane under their
 * own tickets. None of them changes this: the band and the rail do not vary
 * between rails49 UIs, and the page is the same on a box with a command
 * station and no layout as on the layout box (ADR-0008 d.6).
 */

import { LitElement, html, type TemplateResult } from "lit";

import { appStyles } from "./dccex-app.styles.js";
import "./dccex-band.js";
import "./dccex-rail.js";

export class DccexApp extends LitElement {
  static override readonly styles = appStyles;

  override render(): TemplateResult {
    return html`
      <dccex-band></dccex-band>
      <dccex-rail></dccex-rail>
      <div class="work"></div>
    `;
  }
}

customElements.define("dccex-app", DccexApp);

declare global {
  interface HTMLElementTagNameMap {
    "dccex-app": DccexApp;
  }
}
