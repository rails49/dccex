/**
 * The decoder: one line of the station's conversation in, what the page makes
 * of it out, or nothing.
 *
 * What it makes of a line is two things and they are one reading: the **gloss**
 * the monitor puts beside the bytes, and the fact the band and the tiles are
 * built out of — the rails hot, the **build** on the station, each track's
 * power, mode, the milliamps it draws and the most it may draw. Both come off
 * the same line and the same regular expression, so the page cannot show a
 * sentence it has not made a reading of or a reading it cannot say
 * (ADR-0008 d.2).
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
 * next door, which turns desired values into these messages
 * (docs/ui/README.md).
 *
 * It is JavaScript with its types in JSDoc, as every module the gate runs
 * rather than reads is. The gate is Python and cannot run a bundler, and a
 * gloss asserted against the source that would produce it is not asserted;
 * what a bare node can run, the gate can put pairs through
 * (`tests/ui/test_decoder.py`, which lists them). `tsc` checks this file as it
 * checks the rest (`ui/tsconfig.json`).
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
 * @property {number[]} [limits] the most each track may draw, in milliamps, A
 *   first
 */

/**
 * Track power, on or off: `<p0>`, `<p1>`, and either with the track it is
 * about — `<p1 MAIN>`.
 *
 * It is what the **band**'s power button is coloured by: whether the rails are
 * hot. A line about one named track says it of the rails all the same — this
 * page has no track row and no railroad to hang one on, and what the station
 * last said about power is the whole of what it knows (ADR-0008).
 *
 * `<p1 JOIN>` says the PROG track carries MAIN. The station sends it while
 * joined whether or not the tracks are on, so its sentence is not about power.
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
  let say = `track power is ${state}`;
  if (said[2] === "JOIN" && hot) {
    say = "the PROG track is joined to MAIN";
  } else if (said[2] !== undefined) {
    say = `${said[2]} track power is ${state}`;
  }
  return { say, hot, ...track };
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
 * the fact a **release** is compared against (GLOSSARY.md, ADR-0008 d.3). A
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
 * The milliamps on every track, as the station measures them, track A first:
 * what each is drawing (`<jI 13 2 0 0>`) and the most each may draw
 * (`<jG 1233 1233 1233 1233>`). `<JI>` and `<JG>` ask for them.
 *
 * The two are one shape and are read together because they are one **tile**'s
 * reading in two halves: the current, and the limit under it
 * (docs/ui/README.md, issue 170). The letter says which. A `j` line in any
 * other letter is not read here; `clock` reads `jC`.
 *
 * @param {string} rest what follows the `j`
 * @returns {Reading | null}
 */
function measured(rest) {
  const said = /^([IG])((?: -?\d+)+)$/.exec(rest);
  if (said === null) {
    return null;
  }
  const milliamps = said[2].trim().split(" ").map(Number);
  return said[1] === "I"
    ? {
        say: `the tracks are drawing ${milliamps.join(", ")} milliamps`,
        currents: milliamps,
      }
    : {
        say: `the tracks may draw up to ${milliamps.join(", ")} milliamps`,
        limits: milliamps,
      };
}

/**
 * The station's fast clock: `<jC 390 4>`, the minute of the day and the rate,
 * or `<jC 390>`, the answer to a bare `<JC>`. The translator sets it with
 * `<JC>` (#348).
 *
 * @param {string} rest what follows the `j`
 * @returns {Reading | null}
 */
function clock(rest) {
  const said = /^C (\d+)(?: (\d+))?$/.exec(rest);
  const minute = Number(said?.[1]);
  if (said === null || minute >= 24 * 60) {
    return null;
  }
  const time =
    `${String(Math.floor(minute / 60)).padStart(2, "0")}:` +
    String(minute % 60).padStart(2, "0");
  const rate = said[2] === undefined ? "" : ` ×${said[2]}`;
  return { say: `fast clock ${time}${rate}` };
}

/**
 * A `j` line, the station's answer to a `<J…>`: the milliamps or the fast
 * clock.
 *
 * @param {string} rest what follows the `j`
 * @returns {Reading | null}
 */
function jLine(rest) {
  return measured(rest) ?? clock(rest);
}

/** The modifier letters the station puts after MAIN or BOOST, and the word
 *  the `<=` command takes for them.
 *  @type {Record<string, string>} */
const MODIFIERS = { A: "AUTO", I: "INV", "A I": "AUTO_INV" };

/**
 * What a track is set to: `<= A MAIN>`. `<=>` asks for every track.
 *
 * A DC track carries its cab after the mode (`<= C DC 3>`); the mode is what
 * is read, and the cab is left on the line.
 *
 * MAIN and BOOST may carry modifiers: `A` for auto-reverse, `I` for inverted,
 * `A I` for both (`<= C MAIN A>`). The mode is read as the word the `<=`
 * command takes for it: `MAIN_AUTO`, `MAIN_INV` or `MAIN_AUTO_INV`.
 *
 * @param {string} rest what follows the `=`
 * @returns {Reading | null}
 */
function mode(rest) {
  const said =
    /^([A-H]) (?:(MAIN|BOOST) (A I|A|I)|([A-Z]+)(?: \d+)?)$/.exec(rest);
  if (said === null) {
    return null;
  }
  const named = said[4] ?? `${said[2]}_${MODIFIERS[said[3]]}`;
  return {
    say: `track ${said[1]} is ${named}`,
    track: said[1],
    mode: named,
  };
}

/**
 * A loco's speed, direction and functions: `<l 3 0 154 1>`.
 *
 * The second field is the slot, `-1` where the cab has none. In the speed
 * byte, bit 7 is the direction, 1 forward; the low 7 bits are 0 for stop, 1
 * for emergency stop and n for step n-1. Bit n of the last field is Fn, and
 * the field is negative when F31 is on.
 *
 * @param {string} rest what follows the `l`
 * @returns {Reading | null}
 */
function loco(rest) {
  const said = /^(\d+) (-1|\d+) (\d+) (-?\d+)$/.exec(rest);
  if (said === null) {
    return null;
  }
  const cab = said[1];
  if (said[2] === "-1") {
    return { say: `loco ${cab} has no slot` };
  }
  const speed = Number(said[3]);
  if (speed > 255) {
    return null;
  }
  const way = speed & 0x80 ? "forward" : "reverse";
  const step = speed & 0x7f;
  let say = `loco ${cab} ${way} at step ${step - 1}`;
  if (step === 0) {
    say = `loco ${cab} ${way}, stopped`;
  } else if (step === 1) {
    say = `loco ${cab} ${way}, emergency stop`;
  }
  const functions = Number(said[4]) >>> 0;
  /** @type {string[]} */
  const on = [];
  for (let n = 0; n < 32; n++) {
    if ((functions >>> n) & 1) {
      on.push(`F${n}`);
    }
  }
  return { say: on.length === 0 ? say : `${say}, ${on.join(" ")} on` };
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
 *  Growing it is adding a reader here and a pair to the suite (ADR-0009
 *  d.5). */
const READS = {
  p: power,
  H: turnout,
  i: banner,
  c: current,
  j: jLine,
  "=": mode,
  l: loco,
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
