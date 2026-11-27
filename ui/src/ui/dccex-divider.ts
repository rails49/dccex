/**
 * The divider between the script view's editor and its **log** (#365, #416).
 *
 * What it holds is the log's share of the room the two are in. What is drawn
 * and dragged is look's `look-gap` (rails49/look#62). Each `look-gap-move`
 * is a new share, which the divider says in a `divided` event, and the view
 * lays the two out by it. It says the share it opens with as well, when it is
 * put in the page.
 *
 * Wider than `ACROSS` the log is to the right of the editor and the gap's
 * `axis` is `x`; narrower, the log is below and the `axis` is `y`. The view's
 * sheet lays the two out on the same query.
 *
 * Dragged to the log's edge the share is `0`, which hides the log, and the
 * divider stays at the edge to be dragged back. The browser remembers the
 * share in `localStorage`. A store that refuses is a share that is not
 * remembered, and the divider opens on `SHARE`.
 */

import "@rails49/look";
import { keepDivider, keptDivider } from "@rails49/look";
import type { LookGapMoveDetail } from "@rails49/look";
import { LitElement, html, type TemplateResult } from "lit";

import { ACROSS, dividerStyles } from "./dccex-divider.styles.js";

export { ACROSS };

/** The log's share where none is remembered. */
export const SHARE = 0.4;

/** Where the share is remembered. */
export const REMEMBERED = "dccex.log.share";

/** A share under this is the log dragged to its edge, and hidden. */
const EDGE = 0.05;

/** The most of the room the log takes. The editor keeps the rest. */
const MOST = 0.9;

/** `share` as the divider takes it: `0` near the edge, no more than `MOST`,
 *  and `SHARE` for anything that is not a number. */
export function held(share: number): number {
  if (!Number.isFinite(share)) {
    return SHARE;
  }
  if (share < EDGE) {
    return 0;
  }
  return Math.min(share, MOST);
}

/** The share the browser remembers, or `SHARE`. */
export function remembered(): number {
  const kept = keptDivider(REMEMBERED);
  return kept === null ? SHARE : held(kept);
}

/** Remember `share`, where the browser lets the page. */
function remember(share: number): void {
  keepDivider(REMEMBERED, share);
}

export class DccexDivider extends LitElement {
  static override readonly styles = dividerStyles;

  static override readonly properties = {
    across: { state: true },
  };

  /** The log's share of the room, `0` where it is hidden. */
  share = remembered();

  /** Whether the log is beside the editor rather than below it. */
  across = false;

  #media: MediaQueryList | null = null;

  override connectedCallback(): void {
    super.connectedCallback();
    this.#media = matchMedia(ACROSS);
    this.across = this.#media.matches;
    this.#media.addEventListener("change", this.#turned);
    this.#says();
  }

  override disconnectedCallback(): void {
    super.disconnectedCallback();
    this.#media?.removeEventListener("change", this.#turned);
    this.#media = null;
  }

  override render(): TemplateResult {
    return html`<look-gap
      axis=${this.across ? "x" : "y"}
      @look-gap-move=${this.#dragged}
    ></look-gap>`;
  }

  /** Move the divider to `share`, and say so. */
  moves(share: number): void {
    this.share = held(share);
    this.#says();
  }

  #says(): void {
    this.dispatchEvent(new CustomEvent("divided", { detail: this.share }));
  }

  readonly #turned = (): void => {
    this.across = this.#media?.matches ?? false;
  };

  /** The share is what lies between the pointer and the log's edge of the
   *  room the divider is in. Each move is remembered. */
  readonly #dragged = (event: CustomEvent<LookGapMoveDetail>): void => {
    const room = this.parentElement?.getBoundingClientRect();
    if (room === undefined) {
      return;
    }
    const share = this.across
      ? (room.right - event.detail.x) / room.width
      : (room.bottom - event.detail.y) / room.height;
    this.moves(share);
    remember(this.share);
  };
}

customElements.define("dccex-divider", DccexDivider);

declare global {
  interface HTMLElementTagNameMap {
    "dccex-divider": DccexDivider;
  }
}
