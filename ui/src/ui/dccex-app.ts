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
 * **And the page is what polls** (ADR-0010 d.1). The station volunteers a
 * banner when it comes up and a `<p…>` when power changes, and an idle one on
 * a bench says nothing at all; on the box this UI exists for there is no
 * **translator** running to ask it anything. So this page asks, on its own
 * schedule, up its own stream, as a throttle would — and the **mirror** goes
 * on originating nothing, which is the whole of its correctness argument
 * (ADR-0010 d.2). The polls go up the way anything typed goes up, so they are
 * marked as this page's in the monitor and an operator can tell their own
 * traffic from the railroad's.
 *
 * The releases go above the monitor under their own ticket, and that does not
 * change this: the band and the rail do not vary between rails49 UIs, and the
 * page is the same on a box with a command station and no layout as on the
 * layout box (ADR-0008 d.6).
 */

import { LitElement, html, type TemplateResult } from "lit";

import { clients } from "../face.js";
import {
  QUIET,
  asOf,
  counted,
  heard,
  type Kept,
  type Readings,
} from "../readings.js";
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

/** What the page asks the station with.
 *
 * The status request, which is what a throttle asks with and what an operator
 * types most: the station answers it with the power state and its banner, and
 * those are the band's second reading and the **build** (ADR-0008 d.2, d.3).
 * It goes up as any typed message does, through the one rule about what a
 * whole message is (`message.js`).
 */
const POLL = "<s>";

/** How often the page asks.
 *
 * Its own schedule and nobody else's, which is the property ADR-0010 d.1
 * bought: a page that wanted a reading every second and one that wanted none
 * are both clients doing what clients do, and the mirror cannot tell either
 * from DecoderPro. Two pages open means two pollers, as two throttles mean
 * two, and nothing deduplicates them.
 *
 * `SILENT_MS` is three of these, so one answer lost on a busy line is not an
 * outage on the chrome (`readings.js`).
 */
export const POLL_MS = 5000;

/** How often the readings are worked out again with nothing having arrived.
 *
 * The **link** going down is the absence of a line, so it is a thing that
 * happens on the clock rather than on the stream: a page that only recomputed
 * when the station spoke would say a station was answering for as long as it
 * stayed silent. It is also what moves the last-heard tile along a second at
 * a time.
 */
const TICK_MS = 1000;

export class DccexApp extends LitElement {
  static override readonly styles = appStyles;

  static override readonly properties = {
    said: { state: true },
    readings: { state: true },
  };

  /** The conversation: what the station has said and what this page sent,
   *  oldest first. */
  said: Said[] = [];

  /** What the band and the tiles are drawn from, as they stand. */
  readings: Readings = asOf(QUIET, 0);

  /** What the station and the face have said, which the readings are worked
   *  out of. It is not reactive: what a component draws is `readings`, and a
   *  second thing to draw would be a second answer to what the page knows. */
  #kept: Kept = QUIET;

  #polling: ReturnType<typeof setInterval> | null = null;
  #ticking: ReturnType<typeof setInterval> | null = null;

  readonly #stream = new Stream((said: Said[]) => {
    this.#keep(said);
  });

  override connectedCallback(): void {
    super.connectedCallback();
    this.#stream.open();
    this.#ask();
    this.#polling = setInterval(() => {
      this.#ask();
    }, POLL_MS);
    this.#ticking = setInterval(() => {
      this.#now();
    }, TICK_MS);
  }

  /** Let the stream go and stop asking.
   *
   * A page that is closed stops polling, which is the conversation being quiet
   * when nobody is watching — the correct conversation rather than one a
   * service manufactured to have something to show (ADR-0010 d.4).
   */
  override disconnectedCallback(): void {
    super.disconnectedCallback();
    this.#stream.close();
    if (this.#polling !== null) {
      clearInterval(this.#polling);
      this.#polling = null;
    }
    if (this.#ticking !== null) {
      clearInterval(this.#ticking);
      this.#ticking = null;
    }
  }

  override render(): TemplateResult {
    return html`
      <dccex-band .readings=${this.readings}></dccex-band>
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

  /** Ask the station how it is, and the face how many are on its port.
   *
   * Two counterparties and one schedule. The station is asked up the stream,
   * because the page is one more client of the mirror's port and that is what
   * a client does (ADR-0007 d.2, ADR-0010 d.1); the face is asked about
   * itself, because who is listening to a command station is not something a
   * command station knows (ADR-0008 d.4).
   */
  #ask(): void {
    this.#sends(POLL);
    void clients().then((count: number | null) => {
      this.#kept = counted(this.#kept, count);
      this.#now();
    });
  }

  /** The readings as they stand, on the page's own clock. */
  #now(): void {
    this.readings = asOf(this.#kept, Date.now());
  }

  /** Keep the lines, and read the station's own into the readings.
   *
   * **Only the station's.** A line this page sent is this page speaking, and
   * folding one in would be a page keeping its own link up by polling: the
   * band would then be saying that the page is running rather than that the
   * station is answering (ADR-0008, control ADR-0066).
   */
  #keep(said: Said[]): void {
    for (const line of said) {
      if (!line.sent) {
        this.#kept = heard(this.#kept, line.line, line.at.getTime());
      }
    }
    this.#now();
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
