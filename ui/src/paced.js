/**
 * What the box at the foot sends, and when: a list of `<…>` messages, one
 * PROG reply at a time (#357).
 *
 * The station handles one PROG command at a time. While a `<W>`, `<V>`,
 * `<B>`, `<R>` or `<r>` waits for its ack it answers any other one of these
 * with `<X>` (`stashBusy`, `CommandStation-EX/DCCEXParser.cpp`). So the page
 * sends a list in order, and after one of these waits for the station's next
 * `<r…>`, `<v …>`, `<w …>` or `<X>` before it sends the next message. Any
 * other command is followed right away. Where no reply comes within
 * `REPLY_MS` the next message goes, and the page puts in a note.
 *
 * A list stops where a reply ends in `-1`, a reply is `<X>`, or the stream
 * closes. What was not sent is dropped, and the page puts in a note saying how
 * many and why.
 *
 * Everything typed at the box goes through here, so what is typed while a
 * list runs waits behind it. The state is one value and each function is a
 * value in and a value out. The clock, the timer and the socket are the
 * page's (`dccex-app.ts`); the cases are `tests/ui/test_paced.py`'s.
 */

import { message } from "./message.js";

/** How long the page waits for the reply to a PROG command, in ms. */
export const REPLY_MS = 10_000;

/** What the page says where a reply did not come. */
export const SILENT = "no reply within 10 s";

/** Why a list stopped, where the page says it. */
export const CLOSED = "the stream closed";

/** A list: `<`, then `>` and `<` with only spaces between, then `>`. */
const LIST = /^<.*>\s*<.*>$/s;

/** Where a list is cut. */
const BETWEEN = />\s*</;

/** A command the station answers with a PROG reply. */
const PROG = /^<[WVBRr][ >]/;

/** A PROG reply, or the station refusing. */
const REPLY = /^<(?:[rvw][ \d].*|X)>$/;

/** A reply that says the command failed. */
const FAILED = /^<X>$|[ ]-1>$/;

/**
 * What the page is sending: what waits to go, and whether the last message
 * sent waits for its reply.
 *
 * @typedef {{
 *   readonly queued: readonly string[],
 *   readonly awaiting: boolean,
 * }} Pacing
 */

/**
 * Nothing to send and nothing awaited.
 *
 * @type {Pacing}
 */
export const IDLE = { queued: [], awaiting: false };

/**
 * The messages the page sends for `typed`, in order.
 *
 * Text that opens with `<`, closes with `>` and has `>` then `<` inside is a
 * list, and an empty `<>` in it is dropped. Anything else is one message, or
 * none, as `message()` says.
 *
 * @param {string} typed what is in the box
 * @returns {string[]}
 */
export function listed(typed) {
  const said = typed.trim();
  const parts = LIST.test(said)
    ? said
        .slice(1, -1)
        .split(BETWEEN)
        .map((part) => `<${part}>`)
    : [said];
  return parts.flatMap((part) => message(part) ?? []);
}

/**
 * What ↑ brings back for `typed`: the one message, the whole typed text for a
 * list, or `null` where nothing is sent.
 *
 * @param {string} typed what is in the box
 * @returns {string | null}
 */
export function recalled(typed) {
  const said = listed(typed);
  if (said.length === 0) {
    return null;
  }
  return said.length === 1 ? said[0] ?? null : typed.trim();
}

/**
 * `pacing` with `said` waiting behind what it holds.
 *
 * @param {Pacing} pacing
 * @param {readonly string[]} said messages, in order
 * @returns {Pacing}
 */
export function added(pacing, said) {
  return { ...pacing, queued: [...pacing.queued, ...said] };
}

/**
 * The message to send now, or `null` where there is none or a reply is
 * awaited.
 *
 * @param {Pacing} pacing
 * @returns {{ pacing: Pacing, send: string | null }}
 */
export function next(pacing) {
  const [send, ...queued] = pacing.queued;
  if (pacing.awaiting || send === undefined) {
    return { pacing, send: null };
  }
  return { pacing: { queued, awaiting: PROG.test(send) }, send };
}

/**
 * `pacing` after the station said `line`.
 *
 * Only a reply heard while one is awaited counts. A failed one stops the
 * list.
 *
 * @param {Pacing} pacing
 * @param {string} line a whole `<…>` message from the station
 * @returns {{ pacing: Pacing, note: string | null }}
 */
export function answered(pacing, line) {
  if (!pacing.awaiting || !REPLY.test(line)) {
    return { pacing, note: null };
  }
  return FAILED.test(line)
    ? stopped(pacing, `the station answered ${line}`)
    : { pacing: { ...pacing, awaiting: false }, note: null };
}

/**
 * `pacing` once no reply came within `REPLY_MS`: the next message may go.
 *
 * @param {Pacing} pacing
 * @returns {{ pacing: Pacing, note: string }}
 */
export function waited(pacing) {
  return { pacing: { ...pacing, awaiting: false }, note: SILENT };
}

/**
 * Nothing more sent, and the note that says what was dropped and `why`, or
 * `null` where nothing was waiting.
 *
 * @param {Pacing} pacing
 * @param {string} why
 * @returns {{ pacing: Pacing, note: string | null }}
 */
export function stopped(pacing, why) {
  const left = pacing.queued.length;
  return {
    pacing: IDLE,
    note:
      left === 0
        ? null
        : `${left} command${left === 1 ? "" : "s"} not sent: ${why}`,
  };
}
