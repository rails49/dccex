/**
 * The readings the **band** and the **tile**s are made of: what the station
 * has said, and what a page draws out of it.
 *
 * Every reading about the station is the conversation, decoded on the page —
 * there is no second channel and nothing is inferred on one (ADR-0008 d.2) —
 * so what goes in here is lines and the moments they arrived, and what comes
 * out is the words on the chrome and on the tiles.
 *
 * **A pure function of what was said and of the moment it is asked for.** No
 * socket, no clock and no DOM: the page hands in its own clock, which is what
 * lets the whole of it be asserted — including what the page shows fifteen
 * seconds from now — on a machine with nothing plugged in
 * (`tests/ui/test_readings.py`). It is one of the seven modules of the page
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
 * Twenty polls' worth, so a few answers lost on a busy line are not an
 * outage on the chrome, and a station that has genuinely gone is called gone
 * within a few seconds. It is the page's own number rather than a rule about
 * the hardware: what it is measuring is the schedule the page polls on
 * (`dccex-app.ts`, ADR-0010 d.1).
 */
export const SILENT_MS = 5000;

/** What a tile reads where the page has no reading to put there. Blank rather
 *  than a dash or a zero: the tiles are the station talking, and a station
 *  that is not talking is an absence rather than a value (ADR-0008 d.3,
 *  ADR-0009 d.2). */
const BLANK = "";

/**
 * How many current readings the shown one is the mean of: two seconds' worth
 * at four polls a second.
 *
 * The station reports one instantaneous ADC sample per track. With a loco
 * running at constant speed those samples scatter between under 20 and over
 * 100 mA (measured 2026-09-25), while the real current, behind the motor's
 * inductance, changes far more slowly. The mean of the scatter is the current
 * worth showing; a median would pick one end of it or the other.
 */
export const MEAN_OF = 8;

/**
 * What the page knows about one track.
 *
 * @typedef {object} Track
 * @property {string | null} mode what the track is set to: MAIN, PROG, DC…
 * @property {boolean | null} hot whether the track has power
 * @property {number | null} milliamps the current it draws: the mean of
 *   `recent`
 * @property {readonly number[]} recent the latest readings, oldest first
 */

/** A track nothing has been said about yet. */
const UNKNOWN = /** @type {Track} */ ({
  mode: null,
  hot: null,
  milliamps: null,
  recent: [],
});

/**
 * The current to show, from the latest readings.
 *
 * @param {readonly number[]} recent at least one reading
 * @returns {number}
 */
function mean(recent) {
  return recent.reduce((sum, milliamps) => sum + milliamps, 0) / recent.length;
}

/** The letters the station names its tracks with, in the order `<jI>` gives
 *  their currents. */
const LETTERS = "ABCDEFGH";

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
 * @property {Readonly<Record<string, Track>>} tracks each track the station
 *   has said anything about, by its letter
 */

/** A page that has just been opened: nothing said yet. The station is not
 *  called away — it is not called anything, which is what a link that is down
 *  says. */
export const QUIET = /** @type {Kept} */ ({
  spokeAt: null,
  hot: null,
  build: null,
  tracks: {},
});

/**
 * The readings as they stand at one moment: what the band and the tiles are
 * drawn from.
 *
 * @typedef {object} Readings
 * @property {boolean} answering whether the station is answering — the link
 * @property {boolean | null} hot whether the rails have power
 * @property {string | null} build what the station says it is running
 * @property {Readonly<Record<string, Track>>} tracks each track, by its letter
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
 * @property {boolean} [lit] for a light rather than words: whether it is on
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
  const tracks = { ...kept.tracks };
  if (reading?.track !== undefined) {
    const track = tracks[reading.track] ?? UNKNOWN;
    tracks[reading.track] = {
      ...track,
      mode: reading.mode ?? track.mode,
      hot: reading.hot ?? track.hot,
    };
  }
  reading?.currents?.forEach((milliamps, i) => {
    const letter = LETTERS[i];
    if (letter === undefined) {
      return;
    }
    const track = tracks[letter] ?? UNKNOWN;
    const recent = [...track.recent, milliamps].slice(-MEAN_OF);
    tracks[letter] = { ...track, recent, milliamps: mean(recent) };
  });
  return {
    ...kept,
    spokeAt: at,
    hot: reading?.track === undefined ? (reading?.hot ?? kept.hot) : kept.hot,
    build: reading?.build ?? kept.build,
    tracks,
  };
}

/**
 * The readings as they stand at `now`.
 *
 * **They all blank together when the link goes down**, and that is the
 * correct reading rather than a gap: the build and the tracks are the station
 * talking, and the station is not talking (ADR-0008 d.3). The build in particular is never held over — a build from before a
 * flash reported as the one on the board would be this page saying what it
 * cannot see — and it fills again by itself when the station comes back and
 * says which one it is running.
 *
 * @param {Kept} kept what the page has been told
 * @param {number} now the page's clock, in milliseconds
 * @returns {Readings}
 */
export function asOf(kept, now) {
  const answering = kept.spokeAt !== null && now - kept.spokeAt <= SILENT_MS;
  return answering
    ? { answering, hot: kept.hot, build: kept.build, tracks: kept.tracks }
    : { answering, hot: null, build: null, tracks: {} };
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
 * What the tiles read, in the order they are drawn: a light for the **link**,
 * the **build**, then a tile per track.
 *
 * The light is the link at a glance, green or red, where the band says it in
 * words. The **build** is a tile rather than a reading on the band because it
 * is long and because it belongs beside the releases it gets compared against.
 *
 * A track reads `off` when the station says its power is off, whatever
 * current was last measured on it, and its current in milliamps otherwise. A
 * track set to `NONE` is not in use and gets no tile.
 *
 * @param {Readings} readings
 * @returns {Shown[]}
 */
export function tiles(readings) {
  const tracks = Object.entries(readings.tracks)
    .filter(([, track]) => track.mode !== "NONE")
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([letter, track]) => ({
      of: track.mode === null ? `track ${letter}` : `track ${letter} · ${track.mode}`,
      reads:
        track.hot === false
          ? "off"
          : track.milliamps === null
            ? BLANK
            : `${Math.round(track.milliamps)} mA`,
    }));
  return [
    { of: "link", reads: BLANK, lit: readings.answering },
    { of: "build", reads: readings.build ?? BLANK },
    ...tracks,
  ];
}
