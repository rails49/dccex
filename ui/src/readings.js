/**
 * The readings the **band** and the **tile**s are made of: what the station
 * has said, and what a page draws out of it.
 *
 * Every reading about the station is the conversation, decoded on the page —
 * there is no second channel and nothing is inferred on one (ADR-0008 d.2) —
 * so what goes in here is lines and the moments they arrived, and what comes
 * out is the words on the chrome and on the tiles. The one reading that is not
 * the station's is how many **client**s are on the mirror's port, which is the
 * mirror's own business about itself and arrives from the **face** (d.4).
 *
 * **A pure function of what was said and of the moment it is asked for.** No
 * socket, no clock and no DOM: the page hands in its own clock, which is what
 * lets the whole of it be asserted — including what the page shows fifteen
 * seconds from now — on a machine with nothing plugged in
 * (`tests/ui/test_readings.py`). It is one of the four modules of the page
 * written as JavaScript with its types in JSDoc, for the reason the decoder
 * and the box's own rule are: the gate is Python with a bare node in it, and
 * what a page shows an operator asserted against the source that would produce
 * it is not asserted. `tsc` checks it as it checks the rest
 * (`ui/tsconfig.json`).
 *
 * **The link is the station answering, not a socket being open** (ADR-0008,
 * control ADR-0066). A socket stays up through a pulled cable, a station
 * switched off and a flash; what says the station is there is that it has said
 * something lately, and the page is what asks it to (ADR-0010 d.1).
 */

import { read } from "./decoder.js";

/**
 * How long the station may say nothing before the **link** is down.
 *
 * Three polls' worth, so one answer lost on a busy line is not an outage on
 * the chrome, and a station that has genuinely gone is called gone inside
 * quarter of a minute. It is the page's own number rather than a rule about
 * the hardware: what it is measuring is the schedule the page polls on
 * (`dccex-app.ts`, ADR-0010 d.1).
 */
export const SILENT_MS = 15000;

/** What a tile reads where the page has no reading to put there. Blank rather
 *  than a dash or a zero: three of the tiles are the station talking, and a
 *  station that is not talking is an absence rather than a value (ADR-0008
 *  d.3, ADR-0009 d.2). */
const BLANK = "";

/**
 * What the page has been told, and when — everything it keeps between one
 * line arriving and the next.
 *
 * Every field is the latest word on it and `null` until there has been one.
 * Nothing here is derived: whether the **link** is up is a question about the
 * moment it is asked, which is `asOf`'s.
 *
 * @typedef {object} Kept
 * @property {number | null} spokeAt when the station last said anything, on
 *   the page's clock, in milliseconds
 * @property {boolean | null} hot whether the rails have power
 * @property {string | null} build what the station says it is running
 * @property {number | null} milliamps the current on the track
 * @property {number | null} clients how many are on the mirror's port, as the
 *   face last answered
 */

/** A page that has just been opened: nothing said, and nothing asked of the
 *  face yet. The station is not called away — it is not called anything, which
 *  is what a link that is down says. */
export const QUIET = /** @type {Kept} */ ({
  spokeAt: null,
  hot: null,
  build: null,
  milliamps: null,
  clients: null,
});

/**
 * The readings as they stand at one moment: what the band and the tiles are
 * drawn from.
 *
 * @typedef {object} Readings
 * @property {boolean} answering whether the station is answering — the link
 * @property {boolean | null} hot whether the rails have power
 * @property {string | null} build what the station says it is running
 * @property {number | null} milliamps the current on the track
 * @property {number | null} clients how many are on the mirror's port
 * @property {number | null} quietFor how long since the station last said
 *   anything, in milliseconds
 */

/**
 * One reading as it is drawn: what it is called, and what it reads.
 *
 * The band and the tiles draw the same shape because they are the same kind
 * of thing — a name and a word — and what differs is where they sit and how
 * loud they are, which is the stylesheets'.
 *
 * @typedef {object} Shown
 * @property {string} of which reading it is
 * @property {string} reads the words a person sees
 */

/**
 * What the station said, folded in.
 *
 * Anything the station says counts as it speaking, whether the decoder knows
 * the line or not: this fork answers a subset of DCC-EX's vocabulary and
 * upstream adds to it (ADR-0009 d.5), and a page that called a talking station
 * dead for saying something new would be worse than one that said nothing.
 * What the line carried beyond that is the decoder's to say.
 *
 * **Only what the station said.** A line this page sent is the page speaking,
 * and folding one in would be a monitor keeping its own link up by polling —
 * the link would then say that the page is running rather than that the
 * station is answering.
 *
 * @param {Kept} kept what the page had
 * @param {string} line one line, as the station said it
 * @param {number} at the page's clock when it arrived, in milliseconds
 * @returns {Kept} what the page has now
 */
export function heard(kept, line, at) {
  const reading = read(line);
  return {
    ...kept,
    spokeAt: at,
    hot: reading?.hot ?? kept.hot,
    build: reading?.build ?? kept.build,
    milliamps: reading?.milliamps ?? kept.milliamps,
  };
}

/**
 * How many clients the face says are on the mirror's port, folded in.
 *
 * It is kept apart from the station's own readings because it is a different
 * app answering about itself, and it is why the clients tile goes on reading
 * through an outage the other three blank in: a station that has stopped
 * talking says nothing about who is listening (ADR-0008 d.4).
 *
 * A face that could not be asked answers `null` and the tile blanks: a page
 * drawing `0` for an app it could not reach would be reporting an empty port
 * it never saw, and zero is what the face says when the port is empty
 * (`face.ts`, ADR-0009 d.2).
 *
 * @param {Kept} kept what the page had
 * @param {number | null} clients what the face answered, or nothing
 * @returns {Kept} what the page has now
 */
export function counted(kept, clients) {
  return { ...kept, clients };
}

/**
 * The readings as they stand at `now`.
 *
 * **Three of them blank together when the link goes down**, and that is the
 * correct reading rather than a gap: the build, the current and the last thing
 * said are all the station talking, and the station is not talking (ADR-0008
 * d.3). The build in particular is never held over — a build from before a
 * flash reported as the one on the board would be this page saying what it
 * cannot see — and it fills again by itself when the station comes back and
 * says which one it is running.
 *
 * @param {Kept} kept what the page has been told
 * @param {number} now the page's clock, in milliseconds
 * @returns {Readings}
 */
export function asOf(kept, now) {
  const quietFor = kept.spokeAt === null ? null : now - kept.spokeAt;
  const answering = quietFor !== null && quietFor <= SILENT_MS;
  return answering
    ? {
        answering,
        hot: kept.hot,
        build: kept.build,
        milliamps: kept.milliamps,
        clients: kept.clients,
        quietFor,
      }
    : {
        answering,
        hot: null,
        build: null,
        milliamps: null,
        clients: kept.clients,
        quietFor: null,
      };
}

/**
 * What the band reads: the **link** first, then whether the rails are hot.
 *
 * Two readings and no controls. Nothing on this page commands track power —
 * `control`'s band presses ON, STOP and OFF because `layout` checks the
 * railroad is drained first, and this page is on no bus for anything to check
 * (ADR-0008 d.5) — so what the band has to say it says in words.
 *
 * The link comes first because it is the reading that survives where the band
 * is too narrow to carry both: a station that is not answering makes the other
 * reading meaningless, and a page that dropped the link to keep the rails
 * would be showing a power state nothing has confirmed for a quarter of a
 * minute (`dccex-band.styles.ts`).
 *
 * @param {Readings} readings
 * @returns {Shown[]}
 */
export function band(readings) {
  return [
    { of: "link", reads: readings.answering ? "answering" : "not answering" },
    {
      of: "rails",
      reads:
        readings.hot === null ? "unknown" : readings.hot ? "hot" : "cold",
    },
  ];
}

/**
 * What the tiles read: the station's four particulars, in the order they are
 * drawn.
 *
 * The **build** is a tile rather than a reading on the band because it is long
 * and because it belongs beside the releases it gets compared against. The
 * rails being hot is the band's for the opposite reason: it is true of the
 * whole system and short enough to live on the chrome (CONTEXT.md).
 *
 * @param {Readings} readings
 * @returns {Shown[]}
 */
export function tiles(readings) {
  return [
    { of: "build", reads: readings.build ?? BLANK },
    {
      of: "current",
      reads: readings.milliamps === null ? BLANK : `${readings.milliamps} mA`,
    },
    {
      of: "clients",
      reads: readings.clients === null ? BLANK : `${readings.clients}`,
    },
    {
      of: "last heard",
      reads: readings.quietFor === null ? BLANK : ago(readings.quietFor),
    },
  ];
}

/**
 * How long ago something was said, in the words a person reads.
 *
 * Seconds and no further, because the link is down before a minute of it and
 * the tile blanks with the link: a unit this tile can never reach would be a
 * sentence nobody ever read.
 *
 * @param {number} ms
 * @returns {string}
 */
function ago(ms) {
  const seconds = Math.floor(ms / 1000);
  return seconds === 0 ? "just now" : `${seconds}s ago`;
}
