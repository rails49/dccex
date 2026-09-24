/**
 * The decoder: one line of the station's conversation in, one **gloss** out or
 * nothing.
 *
 * A pure function of the line and nothing else (ADR-0009 d.1) — no socket, no
 * state carried between calls, no clock and no DOM — so what it makes of a
 * line is the same for ever and is asserted as a pair of strings on a machine
 * with nothing plugged in (`tests/ui/test_decoder.py`).
 *
 * **Silence rather than a guess.** A line this does not recognise whole gets
 * nothing back and the monitor shows it raw. There is no partial gloss and no
 * category read off a first character: a sentence about a railroad that
 * nothing observed is the worked-around observation ADR-0009 d.2 refuses, in
 * the one place an operator is most likely to trust it.
 *
 * It is the page's own, and it runs the opposite way from the **translator**
 * next door, which turns desired values into these messages (CONTEXT.md).
 *
 * It is JavaScript with its types in JSDoc, as `message.js` is: the two the
 * gate runs rather than reads, being what decides what a person reads and what
 * reaches the station. The gate is Python and cannot run a bundler, and a
 * gloss asserted against the source that would produce it is not asserted;
 * what a bare node can run, the gate can put pairs through
 * (`tests/ui/test_decoder.py`). `tsc` checks this file as it checks the rest
 * (`ui/tsconfig.json`).
 */

/** What the station wraps every message in. */
const OPEN = "<";
const CLOSE = ">";

/**
 * Track power, on or off: `<p0>`, `<p1>`, and either with the track it is
 * about — `<p1 MAIN>`.
 *
 * @param {string} rest what follows the `p`
 * @returns {string | null}
 */
function power(rest) {
  const said = /^([01])(?: ([A-Z]+))?$/.exec(rest);
  if (said === null) {
    return null;
  }
  const state = said[1] === "1" ? "on" : "off";
  return said[2] === undefined
    ? `track power is ${state}`
    : `${said[2]} track power is ${state}`;
}

/**
 * A turnout the station has thrown or closed: `<H 12 1>`, `<H 12 0>`.
 *
 * The id is the station's own number for it and not a name. A command station
 * holds no names — the page is about the station and about nothing on a
 * railroad (docs/ui/README.md) — so the number is what there is to say.
 *
 * @param {string} rest what follows the `H`
 * @returns {string | null}
 */
function turnout(rest) {
  const said = /^(\d+) ([01])$/.exec(rest);
  if (said === null) {
    return null;
  }
  return `turnout ${said[1]} is ${said[2] === "1" ? "thrown" : "closed"}`;
}

/**
 * The banner the station sends when it comes up:
 * `<iDCC-EX V-5.0.7 / MEGA / STANDARD_MOTOR G-9db6d10>`.
 *
 * The `G-` field is the **build** — what the station says it is running, and
 * the fact a **release** is compared against (CONTEXT.md, ADR-0008 d.3). A
 * banner without one is not glossed: the page would be saying a station came
 * up without saying as what, and the build is the half of this line that is
 * worth a sentence.
 *
 * @param {string} rest what follows the `i`
 * @returns {string | null}
 */
function banner(rest) {
  const said = /^DCC-EX V-(\S+) \/ (\S+) \/ \S+ G-(\S+)$/.exec(rest);
  if (said === null) {
    return null;
  }
  return (
    `the station came up running DCC-EX ${said[1]} on ${said[2]}, ` +
    `build ${said[3]}`
  );
}

/**
 * The current on a track: `<c CurrentMAIN 123 C Milli 0 0 4000 1000>`.
 *
 * Milliamps or nothing. The unit is on the line because the station may send
 * another, and a number read as milliamps because it was assumed to be is a
 * reading nobody took.
 *
 * @param {string} rest what follows the `c`
 * @returns {string | null}
 */
function current(rest) {
  const said = /^Current(\S+) (-?\d+) C Milli(?: -?\d+)+$/.exec(rest);
  if (said === null) {
    return null;
  }
  return `the ${said[1]} track is drawing ${said[2]} milliamps`;
}

/**
 * What the station says to a message it would not take: `<X>`.
 *
 * Which message is not on the line — the station does not say — so the
 * sentence does not either.
 *
 * @param {string} rest what follows the `X`
 * @returns {string | null}
 */
function rejected(rest) {
  return rest === "" ? "the station rejected that command" : null;
}

/** What the decoder knows, by the letter the station opens the message with.
 *  Growing it is adding a reader here and a pair to the suite (ADR-0009 d.5). */
const READS = {
  p: power,
  H: turnout,
  i: banner,
  c: current,
  X: rejected,
};

/**
 * What the station said, in one plain sentence, or `null` where the page does
 * not recognise the line.
 *
 * @param {string} line one line of the conversation, as the station said it
 * @returns {string | null} the gloss, or nothing
 */
export function gloss(line) {
  const said = line.trim();
  if (!said.startsWith(OPEN) || !said.endsWith(CLOSE)) {
    return null;
  }
  const body = said.slice(OPEN.length, -CLOSE.length);
  if (body.includes(OPEN) || body.includes(CLOSE)) {
    return null;
  }
  const verb = body.slice(0, 1);
  if (!Object.hasOwn(READS, verb)) {
    return null;
  }
  return READS[/** @type {keyof typeof READS} */ (verb)](body.slice(1).trim());
}
