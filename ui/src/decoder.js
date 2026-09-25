/**
 * The decoder: one line of the station's conversation in, what the page makes
 * of it out, or nothing.
 *
 * What it makes of a line is two things and they are one reading: the **gloss**
 * the monitor puts beside the bytes, and the fact the band and the tiles are
 * built out of — the rails hot, the **build** on the station, each track's
 * power, mode and milliamps. Both come off the same line and the same regular
 * expression, so the page cannot show a sentence it has not made a reading of
 * or a reading it cannot say (ADR-0008 d.2).
 *
 * A pure function of the line and nothing else (ADR-0009 d.1) — no socket, no
 * state carried between calls, no clock and no DOM — so what it makes of a
 * line is the same for ever and is asserted as that line and that reading on a
 * machine with nothing plugged in (`tests/ui/test_decoder.py`).
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
 * It is JavaScript with its types in JSDoc, as `message.js`, `readings.js`,
 * `releases.js`, `flash.js`, `framing.js` and `monitor.js` are: the seven the
 * gate runs rather than reads, being what decides what a person reads, what
 * reaches the station, what the chrome says of it, what the station could be
 * written with, what is done to the railroad before one is written, where the
 * conversation arrives and how it is read off the page. The gate is Python and cannot
 * run a bundler, and a gloss asserted against the source that would produce it
 * is not asserted; what a bare node can run, the gate can put pairs through
 * (`tests/ui/test_decoder.py`). `tsc` checks this file as it checks the rest
 * (`ui/tsconfig.json`).
 */

/** What the station wraps every message in. */
const OPEN = "<";
const CLOSE = ">";

/**
 * What the page makes of one line: the sentence a reader is shown, and
 * whatever fact the line carried.
 *
 * A line says at most one of them. Most say none — a turnout thrown is a
 * sentence and no reading, because nothing on this page is about a railroad
 * (ADR-0008) — and a field that is not on the line is not on the reading,
 * rather than being a zero somebody could draw.
 *
 * @typedef {object} Reading
 * @property {string} say the plain sentence the monitor shows beside the bytes
 * @property {boolean} [hot] whether the rails have power
 * @property {string} [build] what the station says it is running
 * @property {string} [track] which track, A to H, a power or mode line is about
 * @property {string} [mode] what a track is set to: MAIN, PROG, DC and so on
 * @property {number[]} [currents] the milliamps on each track, A first
 */

/**
 * Track power, on or off: `<p0>`, `<p1>`, and either with the track it is
 * about — `<p1 MAIN>`.
 *
 * It is the **band**'s second reading: whether the rails are hot. A line about
 * one named track says it of the rails all the same — this page has no track
 * row and no railroad to hang one on, and what the station last said about
 * power is the whole of what it knows (ADR-0008).
 *
 * @param {string} rest what follows the `p`
 * @returns {Reading | null}
 */
function power(rest) {
  const said = /^([01])(?: ([A-Z]+))?$/.exec(rest);
  if (said === null) {
    return null;
  }
  const hot = said[1] === "1";
  const state = hot ? "on" : "off";
  const track = /^[A-H]$/.test(said[2] ?? "") ? { track: said[2] } : {};
  return {
    say:
      said[2] === undefined
        ? `track power is ${state}`
        : `${said[2]} track power is ${state}`,
    hot,
    ...track,
  };
}

/**
 * A turnout the station has thrown or closed: `<H 12 1>`, `<H 12 0>`.
 *
 * The id is the station's own number for it and not a name. A command station
 * holds no names — the page is about the station and about nothing on a
 * railroad (docs/ui/README.md) — so the number is what there is to say.
 *
 * @param {string} rest what follows the `H`
 * @returns {Reading | null}
 */
function turnout(rest) {
  const said = /^(\d+) ([01])$/.exec(rest);
  if (said === null) {
    return null;
  }
  const how = said[2] === "1" ? "thrown" : "closed";
  return { say: `turnout ${said[1]} is ${how}` };
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
 * @returns {Reading | null}
 */
function banner(rest) {
  const said = /^DCC-EX V-(\S+) \/ (\S+) \/ \S+ G-(\S+)$/.exec(rest);
  if (said === null) {
    return null;
  }
  return {
    say:
      `the station came up running DCC-EX ${said[1]} on ${said[2]}, ` +
      `build ${said[3]}`,
    build: said[3],
  };
}

/**
 * The current on a track: `<c CurrentMAIN 123 C Milli 0 0 4000 1000>`.
 *
 * Milliamps or nothing. The unit is on the line because the station may send
 * another, and a number read as milliamps because it was assumed to be is a
 * reading nobody took.
 *
 * @param {string} rest what follows the `c`
 * @returns {Reading | null}
 */
function current(rest) {
  const said = /^Current(\S+) (-?\d+) C Milli(?: -?\d+)+$/.exec(rest);
  if (said === null) {
    return null;
  }
  return {
    say: `the ${said[1]} track is drawing ${said[2]} milliamps`,
  };
}

/**
 * The current on every track, as the station measures it: `<jI 13 2 0 0>`,
 * in milliamps, track A first. `<JI>` asks for it.
 *
 * Only the `I` form is read. `<jG …>` is the same shape and is each track's
 * limit rather than what it is drawing.
 *
 * @param {string} rest what follows the `j`
 * @returns {Reading | null}
 */
function currents(rest) {
  const said = /^I((?: -?\d+)+)$/.exec(rest);
  if (said === null) {
    return null;
  }
  const milliamps = said[1].trim().split(" ").map(Number);
  return {
    say: `the tracks are drawing ${milliamps.join(", ")} milliamps`,
    currents: milliamps,
  };
}

/**
 * What a track is set to: `<= A MAIN>`. `<=>` asks for every track.
 *
 * A DC track carries its cab after the mode (`<= C DC 3>`); the mode is what
 * is read, and the cab is left on the line.
 *
 * @param {string} rest what follows the `=`
 * @returns {Reading | null}
 */
function mode(rest) {
  const said = /^([A-H]) ([A-Z]+)(?: \d+)?$/.exec(rest);
  if (said === null) {
    return null;
  }
  return {
    say: `track ${said[1]} is ${said[2]}`,
    track: said[1],
    mode: said[2],
  };
}

/**
 * What the station says to a message it would not take: `<X>`.
 *
 * Which message is not on the line — the station does not say — so the
 * sentence does not either.
 *
 * @param {string} rest what follows the `X`
 * @returns {Reading | null}
 */
function rejected(rest) {
  return rest === "" ? { say: "the station rejected that command" } : null;
}

/** What the decoder knows, by the letter the station opens the message with.
 *  Growing it is adding a reader here and a pair to the suite (ADR-0009 d.5). */
const READS = {
  p: power,
  H: turnout,
  i: banner,
  c: current,
  j: currents,
  "=": mode,
  X: rejected,
};

/**
 * What the page makes of one line the station said, or `null` where it does
 * not recognise it.
 *
 * @param {string} line one line of the conversation, as the station said it
 * @returns {Reading | null} the sentence and whatever fact went with it
 */
export function read(line) {
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

/**
 * What the station said, in one plain sentence, or `null` where the page does
 * not recognise the line.
 *
 * The half of a reading the monitor draws. It is `read` and nothing else, so
 * a line cannot be glossed without having been read or read without being
 * sayable.
 *
 * @param {string} line one line of the conversation, as the station said it
 * @returns {string | null} the gloss, or nothing
 */
export function gloss(line) {
  const reading = read(line);
  return reading === null ? null : reading.say;
}
