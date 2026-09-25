/**
 * The monitor: the station's conversation as it arrives, each line stamped
 * with the time it arrived, newest at the bottom.
 *
 * It is the page's and not the mirror's — the mirror carries the **stream** and
 * reads nothing on it (CONTEXT.md) — and what makes it a monitor rather than
 * another client of the port is that a person is reading it (ADR-0007).
 *
 * **A line the decoder knows carries its gloss** (#5): one plain sentence
 * beside the bytes, drawn quieter and smaller than them, and nothing at all
 * beside a line it does not know. The reading is the decoder's — a pure
 * function this component asks and holds no part of (ADR-0009 d.1) — and the
 * drawing is this component's.
 *
 * **And there is a box at the foot** (#6). What is typed in it goes up the
 * stream as one whole `<…>` message and is shown in the lines above, marked
 * differently from what the station said, so a reader can tell their own
 * traffic from the railroad's. Everything the station understands is typed
 * here, `<0>` included — that is what a raw monitor is, and none of it is a
 * named control on the page (ADR-0008 d.5). What is sent for what was typed is
 * `message.js`'s, writing it is the stream's, and holding the conversation is
 * the page's (`dccex-app.ts`); this component holds the box and draws lines.
 *
 * **The lines are handed to it and the sending is handed to it**, because what
 * is made of the conversation is the whole page and not this pane: the band
 * and the tiles read the same bytes (ADR-0008 d.2), and a monitor that owned
 * the stream would be the one pane of the page the rest had to ask.
 *
 * **Every row is keyed** (#74). The page keeps the last two thousand lines and
 * drops the oldest, so at capacity every arriving line shifts the whole
 * conversation up by one — and an unkeyed list, which Lit matches by position,
 * re-commits every binding on all two thousand rows for it. Keyed, the shift
 * moves the rows it already drew. The key is the page's to assign, because the
 * page is what keeps the conversation (`Keyed`, `dccex-app.ts`).
 *
 * **And it can be paused and cleared** (stories 12 and 13). The two controls
 * are drawn here and what they do is the page's, handed down the way the
 * sending is: **pause** holds the view, so that nothing on screen is trimmed
 * while a reader reads it — which is what scrolling up cannot do, since at
 * capacity the oldest lines go on being dropped — and what arrives behind it
 * is queued out of sight with a count on the monitor, the cap it is dropped
 * past said rather than hidden. **Clear** empties the conversation and any
 * queue and nothing else. Neither stops the stream, the polling or the tiles:
 * they are the view and not the conversation. The queue and the counting are
 * `monitor.js`'s, run rather than read; the drawing is this component's.
 *
 * **And a burst of arrivals is one drawing of it** (#74). Lit batches what
 * changes within a task, and the frames a busy line arrives in are each their
 * own task, so a station talking steadily is one update per frame it sends.
 * The monitor waits for the frame the browser is going to paint instead: what
 * arrived in between is drawn once, which is as often as anybody can read it.
 * A page nobody is looking at — another tab, a window behind one — is painting
 * nothing, so it draws nothing until it is looked at again, and what it draws
 * then is the conversation as it stands.
 *
 * **The view follows the newest line while the reader is at the bottom and
 * stays where it is once they have scrolled up**, so reading back does not
 * fight the stream. Where they were is measured before the lines change,
 * because afterwards every view is at the bottom of what it was.
 *
 * **And staying where they were survives a trim** (#75). At capacity the page
 * drops the oldest lines, so the pixels that go are the ones above the view: a
 * reader holding a scroll position is holding a distance from the top of a list
 * that just got shorter, and what they were reading comes up under them by the
 * height of whatever went. So the place held across an update is a row and
 * where in the view that row sat, and the view is put back to wherever that row
 * has got to. Browsers have scroll anchoring that may do this and may not — it
 * is best-effort and off in cases of its own — and the one thing the monitor
 * promises a reader who has scrolled up (#4) does not rest on it.
 *
 * **What it works out without drawing is run rather than read** (#78).
 * Whether the reader is at the bottom, the time a line arrived and what waits
 * behind a pause are `monitor.js`'s, which is JavaScript so that a bare node
 * can put the pairs that matter through them. What is left here needs a
 * browser — the rows, the box at the foot, the controls, the rectangles a held
 * row is measured with — and a gate with no browser in it can read that and
 * cannot scroll it.
 */

import { LitElement, html, nothing, type TemplateResult } from "lit";
import { repeat } from "lit/directives/repeat.js";

import { gloss } from "../decoder.js";
import { type Said } from "../framing.js";
import {
  EMPTIED,
  type Behind,
  atBottom,
  stamped,
  waiting,
} from "../monitor.js";
import { monitorStyles } from "./dccex-monitor.styles.js";

/** What marks a line this page sent, in the column the station's lines leave
 *  empty. A mark and a colour rather than a colour alone, because a reader who
 *  does not see the colour is still owed the distinction — and because the one
 *  thing this page must never be ambiguous about is which of these lines it
 *  put on the railroad. */
const SENT_MARK = "»";

/** What the box says before anything is typed into it. The shortest whole
 *  message there is, which is also the one an operator types most. */
const PLACEHOLDER = "<s>";

/** What the control that holds the view says, and what it says while it is
 *  holding. One control and not two, named for what pressing it will do, so a
 *  reader on a busy station is never working out which state they are in. */
const PAUSES = "pause";
const RESUMES = "resume";

/** What the control that empties the conversation says. It empties what is on
 *  screen and any queue behind it, and nothing else — the station is not
 *  spoken to and the readings are not touched. */
const EMPTIES = "clear";

/** A line as the page hands it down: what arrived, and the key the page gave
 *  it when it kept it.
 *
 *  The key is what the row is drawn under, so that a line falling off the
 *  front of the conversation moves the rows above it rather than re-committing
 *  every binding on all of them. Nothing the line carries would do: a line and
 *  the millisecond it arrived in are both ordinary to see twice on a serial
 *  port, and two rows keyed the same are one row.
 *
 *  It is the page's to assign, because the page is what keeps the conversation
 *  (`dccex-app.ts`). */
export interface Keyed extends Said {
  /** What this line is keyed by: assigned once when it was kept, never reused,
   *  and read for nothing else. */
  readonly key: number;
}

/** Where a reader who has scrolled up is, kept across an update: a row, and
 *  where in the view that row sat.
 *
 *  Not a number of pixels from the top of the conversation. The page drops the
 *  oldest lines at capacity (`KEPT`, `dccex-app.ts`), so what a trim takes is
 *  the top of that list, and a view left at the same `scrollTop` is looking at
 *  a different line afterwards. A row is not moved out from under a reader by
 *  that — it is carried up along with everything below what went — so putting
 *  the view back on the row puts the reader back on what they were reading,
 *  whether a thousand lines were dropped or none (#75).
 *
 *  The row is the newest one drawn. Lines arrive below it, so nothing arriving
 *  moves it, and it is the last row a trim could reach. */
interface Held {
  /** The row the place is measured against. */
  readonly row: Element;

  /** How far below the top of the view its top sat, in CSS pixels. Negative
   *  where the row begins above the view. */
  readonly below: number;
}

/** How far below the top of `scroller` the top of `row` sits.
 *
 *  Off the rectangles, which carry the fraction: `offsetTop` is rounded to
 *  whole pixels, and a fraction lost on every trim is a view that creeps away
 *  from the line the reader is on over an evening. */
function sits(scroller: Element, row: Element): number {
  return row.getBoundingClientRect().top - scroller.getBoundingClientRect().top;
}

/** Where the reader of `scroller` is, or `null` where there is no row to hold
 *  them by — a conversation nothing has been said in yet. */
function holding(scroller: Element): Held | null {
  const row = scroller.querySelector(".line:last-of-type");
  return row === null ? null : { row, below: sits(scroller, row) };
}

export class DccexMonitor extends LitElement {
  static override readonly styles = monitorStyles;

  static override readonly properties = {
    said: { attribute: false },
    sends: { attribute: false },
    paused: { attribute: false },
    behind: { attribute: false },
    pauses: { attribute: false },
    clears: { attribute: false },
  };

  /** The conversation to draw, oldest first, as the page hands it down. */
  said: Keyed[] = [];

  /** What sends a typed command, as the page hands it down: the message that
   *  went back, or `null` where nothing did.
   *
   *  A monitor nobody handed one to sends nothing, rather than reaching for a
   *  stream of its own. The box still takes typing — it is a raw monitor and
   *  the typing is not this component's to refuse — and nothing leaves the
   *  page, which is what a line drawn for it would have claimed. */
  sends: (typed: string) => string | null = () => null;

  /** Whether the view is held, as the page hands it down. */
  paused = false;

  /** What is waiting behind the pause, as the page hands it down: the count
   *  this draws is read off it and the lines in it are not this pane's to
   *  draw — they are out of sight until the reader resumes, which is what
   *  being paused means. */
  behind: Behind<Keyed> = EMPTIED;

  /** What holds the view and lets it go, as the page hands it down.
   *
   *  A monitor nobody handed one to holds nothing, for the reason `sends`
   *  gives: the conversation is the page's, and a pane that queued for itself
   *  would be keeping part of it where the band and the tiles cannot see
   *  it. */
  pauses: () => void = () => {};

  /** What empties the conversation and any queue, as the page hands it
   *  down. */
  clears: () => void = () => {};

  /** Whether the reader was at the bottom when the lines last changed. */
  #following = true;

  /** Where a reader who was not at the bottom was when the lines last changed.
   *  `null` where nobody has to be put back: a reader following the tail, or a
   *  conversation with no rows in it. */
  #held: Held | null = null;

  override render(): TemplateResult {
    const waits = waiting(this.behind);
    return html`
      <div class="controls">
        <button type="button" class="hold" @click=${this.pauses}>
          ${this.paused ? RESUMES : PAUSES}
        </button>
        <button type="button" class="empty" @click=${this.clears}>
          ${EMPTIES}
        </button>
        ${waits === null
          ? nothing
          : html`<span class="waiting">${waits}</span>`}
      </div>
      <div class="lines">
        ${this.said.length === 0
          ? html`<div class="quiet">nothing said yet</div>`
          : repeat(
              this.said,
              (said: Keyed) => said.key,
              (said: Keyed) => {
                const read = gloss(said.line);
                return html`
                  <div class=${said.sent ? "line sent" : "line"}>
                    <time datetime=${said.at.toISOString()}>${stamped(said.at)}</time>
                    <span class="mark">${said.sent ? SENT_MARK : nothing}</span>
                    <span class="said">${said.line}</span>
                    ${read === null
                      ? nothing
                      : html`<span class="gloss">${read}</span>`}
                  </div>
                `;
              },
            )}
      </div>
      <form class="box" @submit=${this.#send}>
        <input
          class="typed"
          type="text"
          placeholder=${PLACEHOLDER}
          aria-label="a command for the station"
          enterkeyhint="send"
          autocomplete="off"
          autocapitalize="off"
          autocorrect="off"
          spellcheck="false"
        />
        <button type="submit">send</button>
      </form>
    `;
  }

  /** Wait for the next animation frame, and draw once for everything that
   *  arrived before it.
   *
   * A line arrives in a frame of its own and Lit schedules an update per task,
   * so a busy station is a drawing per frame the station sent; a reader sees
   * the one the browser paints. Waiting for that paint coalesces the burst
   * into it, and every line that arrived in the meantime is in the one
   * drawing — none of them is dropped, because what is drawn is the
   * conversation the page holds and not the frame that woke it.
   *
   * Where the reader is is still measured before the lines change: the
   * measuring is `willUpdate`'s and the update is what this defers.
   */
  protected override async scheduleUpdate(): Promise<void> {
    await new Promise((painted) => requestAnimationFrame(painted));
    await super.scheduleUpdate();
  }

  /** Where the reader is, read before the lines change.
   *
   * Afterwards is too late: once a line has been appended, a reader who was at
   * the bottom and a reader who had scrolled up are the same distance from the
   * end of a longer page, and the scrolled-up one is who the rule is for.
   *
   * Two readings, because a reader is doing one of two things. One at the
   * bottom is following the tail and is put back on the tail. One who has
   * scrolled up is on a row, and it is the row that is remembered rather than
   * the position, because the position is what a trim takes away (`Held`).
   */
  override willUpdate(): void {
    const scroller = this.#scroller();
    this.#following = scroller === null || atBottom(scroller);
    this.#held =
      scroller === null || this.#following ? null : holding(scroller);
  }

  /** Put the view back where the reading was: on the newest line for a reader
   *  who was at the bottom, on their own row for one who had scrolled up.
   *
   * The view is set in one place, so there is one answer to where it goes.
   */
  override updated(): void {
    const scroller = this.#scroller();
    if (scroller === null) {
      return;
    }
    const where = this.#following
      ? scroller.scrollHeight
      : this.#back(scroller);
    if (where !== null) {
      scroller.scrollTop = where;
    }
  }

  /** Where the view has to be for the held row to be where the reader had it.
   *
   * The correction is what that row moved by, which is the height of whatever
   * the page trimmed off the front of the conversation — measured rather than
   * counted, so it is right for rows of any height and is exactly zero on an
   * update that only appended, where nothing above the view changed. It is
   * arithmetic on the scroll position as it stands, and the browser is told to
   * do none of its own (`overflow-anchor`, `dccex-monitor.styles.ts`): scroll
   * anchoring is best-effort and off in cases of its own, and the criterion
   * that the view does not move under a reader who has scrolled up cannot rest
   * on it (#75, #4).
   *
   * `null` where there is nobody to put back: no row was held, or the row that
   * was held is gone — one update that dropped the whole conversation, after
   * which there is nothing left of what they were looking at to hold them to.
   */
  #back(scroller: HTMLElement): number | null {
    const held = this.#held;
    if (held === null || !held.row.isConnected) {
      return null;
    }
    return scroller.scrollTop + sits(scroller, held.row) - held.below;
  }

  /** Send what is in the box, and clear it once something went.
   *
   * The box is emptied for what `sends` handed back, which is what left the
   * page: a command that was not sent — nothing typed, or no stream open to
   * send it on — leaves the typing where it is and draws no line, because a
   * line claiming the station was asked something it was never asked is the
   * observation nobody made (ADR-0009 d.2). The line for what did go is the
   * page's to keep, and it comes back down as one of `said`.
   */
  #send(sending: Event): void {
    sending.preventDefault();
    const box = this.#box();
    if (box === null) {
      return;
    }
    const sent = this.sends(box.value);
    if (sent === null) {
      return;
    }
    box.value = "";
  }

  #scroller(): HTMLElement | null {
    return this.renderRoot.querySelector<HTMLElement>(".lines");
  }

  /** The box at the foot. What is being typed lives in the element and not in
   *  a property of this component: a monitor that held every keystroke as
   *  state would redraw two thousand lines on each one, and nothing above the
   *  box is about what has not been sent yet. */
  #box(): HTMLInputElement | null {
    return this.renderRoot.querySelector<HTMLInputElement>(".typed");
  }
}

customElements.define("dccex-monitor", DccexMonitor);

declare global {
  interface HTMLElementTagNameMap {
    "dccex-monitor": DccexMonitor;
  }
}
