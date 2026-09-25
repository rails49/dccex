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
 * The work pane is the **tile**s, the **release**s under them and the
 * **monitor** under those: the station's particulars, what the station could be
 * written with, and its conversation as it arrives (#4, #6, #7, #8). What the
 * page around them proves is the installation the rest of the UI rests on: it
 * is built by node inside the image, served by nginx out of it, and draws in
 * the look rules (docs/ui/README.md, ADR-0008).
 *
 * **The counterparties are the page's, the flash included** (#9). Choosing a
 * release stops the locomotives, cuts track power and asks the **face** to
 * write, in that order and with the operator warned first (`flash.js`,
 * ADR-0006 d.2) — and what the row runs it with is handed down from here: the
 * same `#sends` the monitor is handed, so the stop and the cut go up the stream
 * as anything typed does and are marked as this page's in the monitor, and the
 * face's own `flash`, because a pane holding a counterparty of its own would be
 * a second answer to what the page talks to (the organisation's ADR-0002).
 *
 * **And the page is what polls** (ADR-0010 d.1). The station volunteers a
 * banner when it comes up and a `<p…>` when power changes, and an idle one on
 * a bench says nothing at all; on the box this UI exists for there is no
 * **translator** running to ask it anything. So this page asks, on its own
 * schedule, up its own stream, as a throttle would — and the **mirror** goes
 * on originating nothing, which is the whole of its correctness argument
 * (ADR-0010 d.2). The polls go up the way anything typed goes up, but they
 * are not written to the monitor, and the answers to them are shown only when
 * they changed (ADR-0010 d.1, amended). The first one waits for the stream to say it is
 * open rather than for the schedule to come round: a poll written at a socket
 * that is still connecting is refused and goes nowhere, and a page that asked
 * there spent its first five seconds reporting a station that was answering as
 * one that was not (#82).
 *
 * **The releases are asked for once and not on the poll** (#8). What the
 * station is doing changes under the eye, which is what the schedule above is
 * for; what the configured source carries changes when somebody publishes, and
 * a page that asked the release API through the face every five seconds would
 * spend somebody else's rate limit on an answer that is the same all evening.
 * What does change — which release is on the station — arrives on the banner
 * and is read off the **build** (ADR-0008 d.3).
 *
 * None of it changes the chrome: the band and the rail do not vary between
 * rails49 UIs, and the page is the same on a box with a command station and no
 * layout as on the layout box (ADR-0008 d.6).
 */

import { LitElement, html, type TemplateResult } from "lit";

import { flash, releases } from "../face.js";
import { type Said } from "../framing.js";
import { quieted } from "../monitor.js";
import {
  QUIET,
  asOf,
  heard,
  type Kept,
  type Readings,
} from "../readings.js";
import { type Carried } from "../releases.js";
import { Stream } from "../stream.js";
import { appStyles } from "./dccex-app.styles.js";
import { type Keyed } from "./dccex-monitor.js";
import "./dccex-band.js";
import "./dccex-monitor.js";
import "./dccex-rail.js";
import "./dccex-releases.js";
import "./dccex-tiles.js";

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
 * those are the band's second reading, each track's power and the **build**
 * (ADR-0008 d.2, d.3). `<JI>` asks for the current on every track and `<=>`
 * for what each track is set to. They go up as any typed message does,
 * through the one rule about what a whole message is (`message.js`), but they
 * are not written to the monitor: lines every five seconds that nobody typed
 * are noise there.
 */
const POLLS = ["<s>", "<JI>", "<=>"];

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
    carried: { state: true },
  };

  /** The conversation: what the station has said and what this page sent,
   *  oldest first, each line keyed by the number the page gave it when it kept
   *  it. */
  said: Keyed[] = [];

  /** What the band and the tiles are drawn from, as they stand. */
  readings: Readings = asOf(QUIET, 0);

  /** What the face said the configured source carries, or `null` where it has
   *  not answered — which is also where it has not been asked yet, and the
   *  list says the releases could not be read until it has. */
  carried: Carried[] | null = null;

  /** What the station and the face have said, which the readings are worked
   *  out of. It is not reactive: what a component draws is `readings`, and a
   *  second thing to draw would be a second answer to what the page knows. */
  #kept: Kept = QUIET;

  /** What each status line's subject last said, so the monitor shows one only
   *  when it changed (`quieted`, `monitor.js`). */
  #said: Record<string, string> = {};

  /** What the next line kept is keyed by.
   *
   * The monitor draws a row per key, so a key is assigned once, is never
   * reused and is never wound back: a key made of what a line says or of when
   * it arrived would draw two identical lines in one millisecond as one row,
   * and a page that renumbered what it holds on a trim would hand the monitor
   * the shift the keys are there to save it (#74).
   */
  #keys = 0;

  #polling: ReturnType<typeof setInterval> | null = null;
  #ticking: ReturnType<typeof setInterval> | null = null;

  /** The stream, and the two things it hands up: the lines that arrive, and
   *  the socket being open — which is when the page asks, because a poll sent
   *  at one that was still connecting was refused and went nowhere (#82). */
  readonly #stream = new Stream(
    (said: Said[]) => {
      this.#keep(said);
    },
    () => {
      this.#ask();
    },
  );

  override connectedCallback(): void {
    super.connectedCallback();
    this.#stream.open();
    void this.#list();
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
        <dccex-tiles .readings=${this.readings}></dccex-tiles>
        <dccex-releases
          .carried=${this.carried}
          .build=${this.readings.build}
          .sends=${this.#sends}
          .writes=${flash}
        ></dccex-releases>
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

  /** Ask the station how it is.
   *
   * Up the stream, because the page is one more client of the mirror's port
   * and that is what a client does (ADR-0007 d.2, ADR-0010 d.1).
   */
  #ask(): void {
    for (const poll of POLLS) {
      this.#stream.send(poll);
    }
  }

  /** The readings as they stand, on the page's own clock. */
  #now(): void {
    this.readings = asOf(this.#kept, Date.now());
  }

  /** Ask the face what the configured source carries, once.
   *
   * Once, because a release list is not a reading: what it carries changes
   * when somebody publishes, and the page is one browser asking somebody
   * else's service through this app. A face that could not be asked leaves the
   * list saying so rather than saying the source is empty (`face.ts`,
   * ADR-0009 d.2), and the way to ask again is to reload the page — which is
   * also what somebody does after publishing one.
   */
  async #list(): Promise<void> {
    this.carried = await releases();
  }

  /** Keep the lines, and read the station's own into the readings.
   *
   * **Only the station's.** A line this page sent is this page speaking, and
   * folding one in would be a page keeping its own link up by polling: the
   * band would then be saying that the page is running rather than that the
   * station is answering (ADR-0008, control ADR-0066).
   *
   * **A status line is kept only when it changed.** Every poll is answered
   * with the same banner and power lines, and a monitor full of them hides
   * what is new (`quieted`, `monitor.js`). The readings still hear every one.
   */
  #keep(said: Said[]): void {
    for (const line of said) {
      if (!line.sent) {
        this.#kept = heard(this.#kept, line.line, line.at.getTime());
      }
    }
    this.#now();
    const { shown, last } = quieted(this.#said, said);
    this.#said = last;
    const worth = said.filter((_line: Said, i: number) => shown[i]);
    const keyed = worth.map((line: Said) => ({ ...line, key: this.#keys++ }));
    const kept = [...this.said, ...keyed];
    this.said = kept.length > KEPT ? kept.slice(kept.length - KEPT) : kept;
  }
}

customElements.define("dccex-app", DccexApp);

declare global {
  interface HTMLElementTagNameMap {
    "dccex-app": DccexApp;
  }
}
