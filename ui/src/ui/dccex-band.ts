/**
 * The band: the UI's name on the left, and the readings on the right.
 *
 * There are no readings yet. The band carries two — whether the station is
 * answering, and whether the rails are hot — and both are made of what the
 * station said on the stream, which is not here yet either. **It presses
 * nothing**: `control`'s band commands track power because `layout` checks the
 * railroad is drained first, and this page is on no bus for anything to check
 * (ADR-0008 d.5).
 *
 * The right-hand spot is drawn as nothing rather than as an empty box, which
 * is what LOOK.md asks of a UI with no control that belongs there.
 */

import { LitElement, html, type TemplateResult } from "lit";

import { bandStyles } from "./dccex-band.styles.js";

export class DccexBand extends LitElement {
  static override readonly styles = bandStyles;

  override render(): TemplateResult {
    return html`<span class="name">dcc-ex</span>`;
  }
}

customElements.define("dccex-band", DccexBand);

declare global {
  interface HTMLElementTagNameMap {
    "dccex-band": DccexBand;
  }
}
