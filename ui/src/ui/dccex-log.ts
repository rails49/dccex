/**
 * The translator's **log**, beside the script view's editor (#365).
 *
 * While it is showing it asks for the log about once a second, from the byte
 * it has read up to, and adds what is new at the bottom. A file the translator
 * trimmed is read whole again (`log.ts`). It stops asking when it is not
 * showing: the script view is hidden, or the divider has hidden the log.
 *
 * Where the face will not serve the log, its sentence is what is shown, as it
 * came: a mirror started without `--log` says so.
 *
 * **It follows the bottom** unless the reader has scrolled up, and follows
 * again once they scroll back down to it.
 *
 * The asking is the page's, handed down, as the script's is
 * (`dccex-app.ts`). There is no heading over it.
 */

import { LitElement, html, type TemplateResult } from "lit";

import { type Logged, Tail } from "../log.js";
import { logStyles } from "./dccex-log.styles.js";

/** How long between asks, in milliseconds. */
export const EVERY = 1000;

/** How near the bottom, in pixels, still counts as at it. */
const SLACK = 8;

export class DccexLog extends LitElement {
  static override readonly styles = logStyles;

  static override readonly properties = {
    reads: { attribute: false },
    showing: { attribute: false },
  };

  /** What asks the face for the log from byte N, as the page hands it down.
   *  A pane handed none reads nothing. */
  reads: (from: number) => Promise<Logged> = () => Promise.resolve(null);

  /** Whether the log is in front of somebody. It asks only while it is. */
  showing = false;

  /** The log as far as it has been read. */
  readonly tail = new Tail();

  /** Which run of asks is current. Bumped to stop one. */
  #round = 0;

  #asking = false;

  #timer: ReturnType<typeof setTimeout> | undefined = undefined;

  #following = true;

  override disconnectedCallback(): void {
    super.disconnectedCallback();
    this.#stops();
  }

  override connectedCallback(): void {
    super.connectedCallback();
    if (this.showing) {
      this.#starts();
    }
  }

  override render(): TemplateResult {
    const { parts, says } = this.tail;
    const shown = says === "" ? parts : says;
    return html`<pre
      class=${says === "" ? "log" : "log says"}
      role="log"
      aria-label="log"
      tabindex="0"
      @scroll=${this.#scrolled}
    >${shown}</pre>`;
  }

  protected override updated(changed: Map<string, unknown>): void {
    if (changed.has("showing")) {
      if (this.showing && this.isConnected) {
        this.#starts();
      } else {
        this.#stops();
      }
    }
    if (this.#following) {
      const shown = this.#shown();
      shown.scrollTop = shown.scrollHeight;
    }
  }

  #shown(): HTMLElement {
    return this.renderRoot.querySelector(".log") as HTMLElement;
  }

  #starts(): void {
    if (this.#asking) {
      return;
    }
    this.#asking = true;
    void this.#asks(++this.#round);
  }

  #stops(): void {
    this.#asking = false;
    this.#round += 1;
    clearTimeout(this.#timer);
    this.#timer = undefined;
  }

  /** Ask, take the answer, wait, and ask again, until the round is over. One
   *  ask at a time, so answers land in the order they were asked. */
  async #asks(round: number): Promise<void> {
    while (round === this.#round) {
      const logged = await this.reads(this.tail.at);
      if (round !== this.#round) {
        return;
      }
      const again = this.tail.took(logged);
      this.requestUpdate();
      if (!again) {
        await new Promise((waited) => {
          this.#timer = setTimeout(waited, EVERY);
        });
      }
    }
  }

  /** Whether the reader is at the bottom, read each time they scroll. */
  readonly #scrolled = (): void => {
    const shown = this.#shown();
    this.#following =
      shown.scrollTop + shown.clientHeight >= shown.scrollHeight - SLACK;
  };
}

customElements.define("dccex-log", DccexLog);

declare global {
  interface HTMLElementTagNameMap {
    "dccex-log": DccexLog;
  }
}
