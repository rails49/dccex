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
 * The pause and the clear are the page's under their own tickets.
 *
 * **The view follows the newest line while the reader is at the bottom and
 * stays where it is once they have scrolled up**, so reading back does not
 * fight the feed. Where they were is measured before the lines change, because
 * afterwards every view is at the bottom of what it was.
 */

import { LitElement, html, nothing, type TemplateResult } from "lit";

import { gloss } from "../decoder.js";
import { type Said } from "../stream.js";
import { monitorStyles } from "./dccex-monitor.styles.js";

/** How close to the bottom still counts as being at it, in CSS pixels. A
 *  scroller that is one rounded sub-pixel from the end is a reader who has not
 *  scrolled up. */
const SLACK_PX = 4;

/** What marks a line this page sent, in the column the station's lines leave
 *  empty. A mark and a colour rather than a colour alone, because a reader who
 *  does not see the colour is still owed the distinction — and because the one
 *  thing this page must never be ambiguous about is which of these lines it
 *  put on the railroad. */
const SENT_MARK = "»";

/** What the box says before anything is typed into it. The shortest whole
 *  message there is, which is also the one an operator types most. */
const PLACEHOLDER = "<s>";

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
    said: { attribute: false },
    sends: { attribute: false },
  };

  /** The conversation to draw, oldest first, as the page hands it down. */
  said: Said[] = [];

  /** What sends a typed command, as the page hands it down: the message that
   *  went back, or `null` where nothing did.
   *
   *  A monitor nobody handed one to sends nothing, rather than reaching for a
   *  stream of its own. The box still takes typing — it is a raw monitor and
   *  the typing is not this component's to refuse — and nothing leaves the
   *  page, which is what a line drawn for it would have claimed. */
  sends: (typed: string) => string | null = () => null;

  /** Whether the reader was at the bottom when the lines last changed. */
  #following = true;

  override render(): TemplateResult {
    return html`
      <div class="lines">
        ${this.said.length === 0
          ? html`<div class="quiet">nothing said yet</div>`
          : this.said.map((said: Said) => {
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
            })}
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
