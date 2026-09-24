/**
 * The page: the band, the rail and the work pane between them.
 *
 * **The conversation is held here.** The page opens the **stream**, keeps the
 * lines that arrive on it and the lines it sent, and hands them down — because
 * what is made of that conversation is the whole page and not one pane of it:
 * the band's two readings and the tiles' particulars are the same bytes the
 * monitor is drawing (ADR-0008 d.2), and a second stream for them would be a
 * second client of the mirror's port for one page.
 *
 * The work pane is the **monitor** — the station's conversation as it arrives
 * (#4, #6). What the page around it proves is the installation the rest of the
 * UI rests on: it is built by node inside the image, served by nginx out of it,
 * and draws in the look rules (docs/ui/README.md, ADR-0008).
 *
 * The releases go above the monitor under their own ticket, and that does not
 * change this: the band and the rail do not vary between rails49 UIs, and the
 * page is the same on a box with a command station and no layout as on the
 * layout box (ADR-0008 d.6).
 */

import { LitElement, html, type TemplateResult } from "lit";

import { Stream, type Said } from "../stream.js";
import { appStyles } from "./dccex-app.styles.js";
import "./dccex-band.js";
import "./dccex-monitor.js";
import "./dccex-rail.js";

/** How many lines the page keeps.
 *
 * A page left open on a busy railroad is handed every byte of an evening, and
 * a monitor is what the station is saying now: the oldest lines are dropped
 * rather than held until the browser cannot draw the page. Nothing was lost by
 * the mirror doing it — it keeps no history either (ADR-0010) — and this is the
 * page saying how much of the conversation it can show, which is its own
 * business.
 */
export const KEPT = 2000;

export class DccexApp extends LitElement {
  static override readonly styles = appStyles;

  static override readonly properties = {
    said: { state: true },
  };

  /** The conversation: what the station has said and what this page sent,
   *  oldest first. */
  said: Said[] = [];

  readonly #stream = new Stream((said: Said[]) => {
    this.#keep(said);
  });

  override connectedCallback(): void {
    super.connectedCallback();
    this.#stream.open();
  }

  override disconnectedCallback(): void {
    super.disconnectedCallback();
    this.#stream.close();
  }

  override render(): TemplateResult {
    return html`
      <dccex-band></dccex-band>
      <dccex-rail></dccex-rail>
      <div class="work">
        <dccex-monitor
          .said=${this.said}
          .sends=${this.#sends}
        ></dccex-monitor>
      </div>
    `;
  }

  /** Send what somebody typed, and keep the line that went.
   *
   * What comes back is what left the page, or `null` where nothing did — there
   * was nothing to send, or there is no stream open to send it on. A line is
   * kept only for what actually went: a line claiming the station was asked
   * something it was never asked is the observation nobody made (ADR-0009
   * d.2).
   */
  readonly #sends = (typed: string): string | null => {
    const sent = this.#stream.send(typed);
    if (sent !== null) {
      this.#keep([{ at: new Date(), line: sent, sent: true }]);
    }
    return sent;
  };

  #keep(said: Said[]): void {
    const kept = [...this.said, ...said];
    this.said = kept.length > KEPT ? kept.slice(kept.length - KEPT) : kept;
  }
}

customElements.define("dccex-app", DccexApp);

declare global {
  interface HTMLElementTagNameMap {
    "dccex-app": DccexApp;
  }
}
