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
 * **Holding the view still and emptying it are the page's**, because the
 * conversation is. **Paused**, what arrives is queued out of sight and
 * nothing on screen is trimmed — which is what scrolling up cannot do, since
 * at capacity the line a reader is reading goes off the front while they read
 * it (#75, #4). The stream, the polls and the readings are untouched: it is
 * the view and not the conversation, so the band and the tiles go on saying
 * what the station is doing. Resuming appends the queue in arrival order and
 * the usual trim applies from there. **Cleared**, the conversation and any
 * queue are empty and nothing else is: not the readings, not the schedule,
 * not what each subject last said.
 *
 * **What any of that does to the conversation is `monitor.js`'s.** The
 * lines on screen, the queue behind a pause, what it dropped and what each
 * subject last said are one value there, and a line arriving, a press of the
 * pause and a press of the clear are three pure functions of it — so the
 * rules are run rather than read (`tests/ui/test_monitor.py`). This page
 * holds the value, hands the readings every line it hears whether the view is
 * held or not, and calls them. The monitor draws the two controls and is
 * handed what they do the way it is handed its lines and its sending.
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
import {
  OPENED,
  type Conversation,
  arrived,
  cleared,
  held,
} from "../monitor.js";
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
import "./dccex-band.js";
import "./dccex-monitor.js";
import "./dccex-rail.js";
import "./dccex-releases.js";
import "./dccex-tiles.js";

/** What the page asks the station for every poll: the current on every track.
 *
 * One short line back (`<jI 4 8 0 0>`), so asking four times a second costs
 * every client on the port about sixty bytes a second. The station reports
 * one instantaneous ADC sample per track, which scatters widely around the
 * real current, so the page asks often and averages (`readings.js`). It is also what keeps the
 * **link** fresh, since any answer is the station speaking.
 */
const CURRENTS = "<JI>";

/** What the page asks the station for every `SLOW_EVERY` polls.
 *
 * The status request, which is what a throttle asks with and what an operator
 * types most: the station answers it with the power state and its banner, and
 * those are the band's second reading, each track's power and the **build**
 * (ADR-0008 d.2, d.3). `<=>` asks what each track is set to. The answer to
 * `<s>` is eight lines and every client on the port receives it, so it is not
 * asked every second.
 *
 * All of them go up as any typed message does, through the one rule about
 * what a whole message is (`message.js`), but they are not written to the
 * monitor: lines nobody typed, several a second, are noise there.
 */
const POLLS = ["<s>", "<=>"];

/** How many polls go by between one status request and the next. */
const SLOW_EVERY = 60;

/** How often the page asks.
 *
 * Its own schedule and nobody else's, which is the property ADR-0010 d.1
 * bought: a page that wanted a reading every second and one that wanted none
 * are both clients doing what clients do, and the mirror cannot tell either
 * from DecoderPro. Two pages open means two pollers, as two throttles mean
 * two, and nothing deduplicates them.
 *
 * `SILENT_MS` is twenty of these, so a few answers lost on a busy line are
 * not an outage on the chrome (`readings.js`).
 */
export const POLL_MS = 250;

/** How often the readings are worked out again with nothing having arrived.
 *
 * The **link** going down is the absence of a line, so it is a thing that
 * happens on the clock rather than on the stream: a page that only recomputed
 * when the station spoke would say a station was answering for as long as it
 * stayed silent.
 */
const TICK_MS = 1000;

export class DccexApp extends LitElement {
  static override readonly styles = appStyles;

  static override readonly properties = {
    conversation: { state: true },
    readings: { state: true },
    carried: { state: true },
  };

  /** The conversation: what the station has said and what this page sent,
   *  what waits behind a pause and what it dropped, whether the view is held,
   *  and what each subject last said.
   *
   *  One value, because the rules that change it are one module's and each of
   *  them answers with the whole of it (`monitor.js`). The page holds it and
   *  hands its parts down; nothing here works out what goes in it. */
  conversation: Conversation = OPENED;

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
      this.#polls = 0;
      this.#ask();
    },
  );

  /** How many times the page has asked since the stream last opened. A
   *  stream that has just opened is asked everything at once. */
  #polls = 0;

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
          .said=${this.conversation.said}
          .sends=${this.#sends}
          .paused=${this.conversation.paused}
          .behind=${this.conversation.behind}
          .pauses=${this.#pauses}
          .clears=${this.#clears}
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

  /** Hold the view, or let it go and append what waited.
   *
   * What that does to the conversation — the queue appended in arrival order,
   * through the one trim there is, with a note where the queue dropped lines
   * — is `held`'s (`monitor.js`).
   *
   * Nothing else is spoken to. The stream was never stopped, the polls were
   * never held and the readings were worked out all along, so there is
   * nothing to start again.
   */
  readonly #pauses = (): void => {
    this.conversation = held(this.conversation);
  };

  /** Empty the conversation, and any queue with it.
   *
   * And nothing else: the tiles, the polling and the stream are untouched,
   * because a clear is a reader emptying what is on screen rather than the
   * page forgetting what the station has told it. What it leaves standing —
   * what each subject last said, and the keys — is `cleared`'s
   * (`monitor.js`).
   */
  readonly #clears = (): void => {
    this.conversation = cleared(this.conversation);
  };

  /** Ask the station how it is.
   *
   * Up the stream, because the page is one more client of the mirror's port
   * and that is what a client does (ADR-0007 d.2, ADR-0010 d.1).
   */
  #ask(): void {
    this.#stream.send(CURRENTS);
    if (this.#polls++ % SLOW_EVERY === 0) {
      for (const poll of POLLS) {
        this.#stream.send(poll);
      }
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

  /** Hear the station's lines into the readings, and hand them all to the
   *  conversation.
   *
   * **Only the station's are heard.** A line this page sent is this page
   * speaking, and folding one in would be a page keeping its own link up by
   * polling: the band would then be saying that the page is running rather
   * than that the station is answering (ADR-0008, control ADR-0066).
   *
   * **Every line is heard, whether the view is held or not.** A pause is the
   * view and not the conversation, so the band and the tiles go on saying
   * what the station is doing while a reader holds the monitor still.
   *
   * What becomes of the lines from there — which repeats are worth showing,
   * what is appended and what is queued, what the queue drops and what it
   * forgets — is `arrived`'s (`monitor.js`).
   */
  #keep(said: Said[]): void {
    for (const line of said) {
      if (!line.sent) {
        this.#kept = heard(this.#kept, line.line, line.at.getTime());
      }
    }
    this.#now();
    this.conversation = arrived(this.conversation, said);
  }
}

customElements.define("dccex-app", DccexApp);

declare global {
  interface HTMLElementTagNameMap {
    "dccex-app": DccexApp;
  }
}
