/**
 * Where the stream is, and where a line ends: the two rules of the **stream**
 * that are not the socket.
 *
 * The socket is `stream.ts`'s. It holds one, opens another when the one it has
 * goes, and writes a whole message up it. What is here is what that module
 * works out without touching anything — the address to open, off the page's
 * own address, and the whole lines that have arrived, off the bytes that
 * have — so neither of these reaches a browser, a clock or a network and both
 * are run with the pairs that matter on a machine with nothing plugged in
 * (`tests/ui/test_stream.py`).
 *
 * The name is the mirror's. `framing.py` cuts the same conversation into whole
 * `<…>` messages at the other end of this stream, to the same shape and for
 * the same reason: bytes arrive in whatever chunks the network hands over, and
 * a rule that needed a line whole would be a rule about the network.
 *
 * **Nothing here reads a line.** What one means is the decoder's, which is a
 * pure function of a line (ADR-0009), and what is sent for what was typed is
 * `message.js`'s, which is another.
 *
 * It is JavaScript with its types in JSDoc, as `decoder.js`, `message.js`,
 * `readings.js`, `releases.js`, `flash.js` and `monitor.js` are: the seven the
 * gate runs rather than reads. These two were read for as long as there was no
 * node to run them with, and a framing that kept its delimiter or a scheme
 * picked the wrong way round leaves a source saying every right word (#78,
 * #101). `tsc` checks this file as strictly as it checks the rest
 * (`ui/tsconfig.json`).
 */

const HTTPS = "https:";
const WSS = "wss:";
const WS = "ws:";

const NEWLINE = "\n";
const RETURN = /\r+$/;

/**
 * As much of a page's address as the stream's is built from: what the page was
 * served over, and the address itself.
 *
 * A `Location` is one, and so is a plain object with the two fields — which is
 * what lets the rule below be run under a bare node. Nothing here touches a
 * browser value; it reads two strings off one.
 *
 * @typedef {{
 *   readonly href: string,
 *   readonly protocol: string,
 * }} Where
 */

/**
 * One line of the conversation, and the moment it was on the page's clock.
 *
 * `at` is when it arrived: the page's clock at the read that carried it, or at
 * the write that sent it. Two lines in one read carry the same stamp, which is
 * what happened. `line` is the line as the station said it, with the newline it
 * ended off — or the whole message this page sent, as it went. `sent` is which
 * end of the conversation it is: `true` where this page sent it, `false` where
 * the station said it, and the monitor draws the two differently so a reader
 * can tell their own traffic from the railroad's.
 *
 * Every field is read-only. A line is what arrived, and nothing downstream of
 * the framing edits the conversation it is showing.
 *
 * @typedef {{
 *   readonly at: Date,
 *   readonly line: string,
 *   readonly sent: boolean,
 * }} Said
 */

/**
 * Where the stream is for the page `where` was read off, under `path`.
 *
 * The page's own address with the scheme swapped and nothing else touched, so
 * a browser opens `wss://` from a page served over `https` and `ws://` from
 * one served over plain HTTP, on whatever host and port the page itself came
 * from. Nothing about the stream is a name or a port of its own (ADR-0004
 * d.3), and nothing in this page names a host: a page that did would work on
 * the machine it was written on and nowhere else.
 *
 * The path is handed in rather than read here. The door's prefix is spelled
 * once, in the module that says where the face is (`face.ts`), and that module
 * is TypeScript — which a bare node cannot import, and this rule is one a bare
 * node runs. So the one spelling stays where it is and the caller passes what
 * it built from it (`STREAM_PATH`, `stream.ts`).
 *
 * @param {Where} where the page's own address
 * @param {string} path where the face answers the stream, on that origin
 * @returns {string}
 */
export function streamAt(where, path) {
  const at = new URL(path, where.href);
  at.protocol = where.protocol === HTTPS ? WSS : WS;
  return at.href;
}

/**
 * Fold `arrived` into `buffered` and take off every whole line, stamped `at`.
 *
 * Returns what is still a partial line, to be passed back as `buffered` next
 * time, and the lines that completed, in the order they did — the shape the
 * mirror's own readers have (`stream.py`, `framing.py`), and for the same
 * reason: bytes arrive in whatever chunks the network hands over, and a rule
 * that needed a line whole would be a rule about the network.
 *
 * A line that is empty once its newline is off is dropped. It is the `\r` of a
 * `\r\n` pair and a blank line the station wrote, and neither is something it
 * said.
 *
 * @param {string} buffered what was left over last time
 * @param {string} arrived the bytes that have just come, one byte one
 *   character (`stream.ts`)
 * @param {Date} at the page's clock at the read that carried them
 * @returns {[string, Said[]]} what is still partial, and the lines that
 *   completed
 */
export function lines(buffered, arrived, at) {
  const whole = buffered + arrived;
  const parts = whole.split(NEWLINE);
  const rest = parts.pop() ?? "";
  /** @type {Said[]} */
  const said = [];
  for (const part of parts) {
    const line = part.replace(RETURN, "");
    if (line) {
      said.push({ at, line, sent: false });
    }
  }
  return [rest, said];
}
