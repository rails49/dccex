/**
 * The monitor: the station's conversation as it arrives, each line stamped
 * with the time it arrived, newest at the bottom.
 *
 * It is the page's and not the mirror's — the mirror carries the **stream** and
 * reads nothing on it (CONTEXT.md) — and what makes it a monitor rather than
 * another client of the port is that a person is reading it (ADR-0007).
 *
 * **This is its downward half** (#4). Nothing is glossed: a line the decoder
 * knows carries one plain sentence beside it and that decoder is a pure
 * function landing under its own ticket (ADR-0009). Nothing is sent: the box at
 * the foot that types a whole `<…>` message, the pause, the clear and the
 * polling that keeps the readings live are all the page's under theirs
 * (ADR-0010 d.1). What is here is the reading.
 *
 * **The view follows the newest line while the reader is at the bottom and
 * stays where it is once they have scrolled up**, so reading back does not
 * fight the feed. Where they were is measured before the lines change, because
 * afterwards every view is at the bottom of what it was.
 */

import { LitElement, html, type TemplateResult } from "lit";

import { Stream, type Said } from "../stream.js";
import { monitorStyles } from "./dccex-monitor.styles.js";

/** How many lines the monitor keeps.
 *
 * A page left open on a busy railroad is handed every byte of an evening, and
 * a monitor is what the station is saying now: the oldest lines are dropped
 * rather than held until the browser cannot draw the page. Nothing was lost by
 * the mirror doing it — it keeps no history either (ADR-0010) — and this is the
 * page saying how much of the conversation it can show, which is its own
 * business.
 */
export const KEPT = 2000;

/** How close to the bottom still counts as being at it, in CSS pixels. A
 *  scroller that is one rounded sub-pixel from the end is a reader who has not
 *  scrolled up. */
const SLACK_PX = 4;

/** Whether the reader is at the bottom of `scroller`. */
export function atBottom(scroller: Element): boolean {
  return (
    scroller.scrollHeight - scroller.scrollTop - scroller.clientHeight <=
    SLACK_PX
  );
}

function padded(value: number, width = 2): string {
  return String(value).padStart(width, "0");
}

/** The time a line arrived, as the operator's own clock says it.
 *
 * Local time, because the person reading is at the layout correlating what
 * they saw with what the station said, and to the millisecond, because a burst
 * of `<…>` messages arrives inside one second. The instant itself rides on the
 * element's `datetime`, so nothing about when a line arrived is lost to the
 * formatting.
 */
export function stamped(at: Date): string {
  return (
    `${padded(at.getHours())}:${padded(at.getMinutes())}` +
    `:${padded(at.getSeconds())}.${padded(at.getMilliseconds(), 3)}`
  );
}

export class DccexMonitor extends LitElement {
  static override readonly styles = monitorStyles;

  static override readonly properties = {
    said: { state: true },
  };

  /** What the station has said, oldest first. */
  said: Said[] = [];

  readonly #stream = new Stream((said: Said[]) => {
    this.#arrived(said);
  });

  /** Whether the reader was at the bottom when the lines last changed. */
  #following = true;

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
      <div class="lines">
        ${this.said.length === 0
          ? html`<div class="quiet">nothing said yet</div>`
          : this.said.map(
              (said: Said) => html`
                <div class="line">
                  <time datetime=${said.at.toISOString()}>${stamped(said.at)}</time>
                  <span class="said">${said.line}</span>
                </div>
              `,
            )}
      </div>
    `;
  }

  /** Where the reader is, read before the lines change.
   *
   * Afterwards is too late: once a line has been appended, a reader who was at
   * the bottom and a reader who had scrolled up are the same distance from the
   * end of a longer page, and the scrolled-up one is who the rule is for.
   */
  override willUpdate(): void {
    const scroller = this.#scroller();
    this.#following = scroller === null || atBottom(scroller);
  }

  /** The newest line, if that is where they were. */
  override updated(): void {
    if (!this.#following) {
      return;
    }
    const scroller = this.#scroller();
    if (scroller !== null) {
      scroller.scrollTop = scroller.scrollHeight;
    }
  }

  #arrived(said: Said[]): void {
    const kept = [...this.said, ...said];
    this.said = kept.length > KEPT ? kept.slice(kept.length - KEPT) : kept;
  }

  #scroller(): HTMLElement | null {
    return this.renderRoot.querySelector<HTMLElement>(".lines");
  }
}

customElements.define("dccex-monitor", DccexMonitor);

declare global {
  interface HTMLElementTagNameMap {
    "dccex-monitor": DccexMonitor;
  }
}
