/**
 * What the page sends for what was typed: one whole `<…>` message, or nothing.
 *
 * A pure function of the text in the box and nothing else — no socket, no
 * state carried between calls, no clock and no DOM — so what leaves the page
 * for a given keystroke is the same for ever and is asserted as a pair of
 * strings on a machine with nothing plugged in (`tests/ui/test_message.py`).
 *
 * **The angle brackets are the station's and not the operator's.** Everything
 * the station understands is typed here, `<0>` included, because that is what
 * a raw monitor is; what a person types is `s` as readily as `<s>`, and both
 * are the same command. So the brackets are supplied where they are missing
 * and kept where they are there, and the two spellings come out as one
 * message.
 *
 * **Nothing is sent for nothing typed.** An empty box, a box of spaces and a
 * pair of brackets with nothing in them all come back as `null`: a `<>` on the
 * wire is a message the station would refuse, and a page that sent one would
 * be typing at the railroad on its own account.
 *
 * It reads no protocol beyond the delimiters. Which commands exist is the
 * station's, what a reply means is the **decoder**'s (`decoder.js`), and what
 * makes the bytes a whole message at the device is the mirror's framing, which
 * every client of the port reaches the same way (ADR-0007 d.2).
 *
 * It is JavaScript with its types in JSDoc, as the decoder is and for the same
 * reason: the gate is Python and cannot run a bundler, and a rule about what
 * goes down a cable asserted against the source that would produce it is not
 * asserted. What a bare node can run, the gate can put pairs through. `tsc`
 * checks this file as it checks the rest (`ui/tsconfig.json`).
 */

/** What the station wraps every message in. */
const OPEN = "<";
const CLOSE = ">";

/**
 * The one whole message the page sends for `typed`, or `null` where there is
 * nothing to send.
 *
 * @param {string} typed what is in the box at the foot of the monitor
 * @returns {string | null} one whole `<…>` message, or nothing
 */
export function message(typed) {
  const said = typed.trim();
  const opened = said.startsWith(OPEN) ? said.slice(OPEN.length) : said;
  const body = (
    opened.endsWith(CLOSE) ? opened.slice(0, -CLOSE.length) : opened
  ).trim();
  return body === "" ? null : `${OPEN}${body}${CLOSE}`;
}
