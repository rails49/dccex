/**
 * The readings the **band** and the **tile**s are made of: what the station
 * has said, and what a page draws out of it.
 *
 * Every reading about the station is the conversation, decoded on the page —
 * there is no second channel and nothing is inferred on one (ADR-0008 d.2) —
 * so what goes in here is lines and the moments they arrived, and what comes
 * out is the words on the chrome and on the tiles.
 *
 * **The railroad's power is the one reading that is not the station's.** It is
 * a row `layout` reports on the bus, because `layout` is what the band asks
 * for power and what the station is told by the translator (ADR-0017). So this
 * module reads that payload too and folds it into the band's one control, and
 * the two are not mixed: a track's power on a **tile** is still the station's
 * `<p…>`, and nothing here reads one off the other.
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

/** What the band and a tile read where the page has no reading to put there.
 *  Blank rather than a dash or a zero: they are the station talking, and a
 *  station that is not talking is an absence rather than a value (ADR-0008
 *  d.3, ADR-0009 d.2). */
const BLANK = "";

/** What `layout` reports the railroad's power as, and what a press asks it for
 *  (ADR-0017 d.1, d.2, `control`'s `docs/BUS.md`). `stopped` is reported and
 *  never asked for here: the band's power button is the way out of it, and the
 *  press that asks for it is #208's. */
const ON = "on";
const OFF = "off";
const STOPPED = "stopped";

/**
 * What `layout` says about the railroad's power, as the page reads it off the
 * bus (ADR-0017).
 *
 * `power` is the latest payload on `tc49/layout/state/power`, read by
 * `reported`, and `null` until one has arrived — which is a different reading
 * from `off`: a railroad nobody has reported the power of is not a railroad
 * with the power off (ADR-0009 d.2), and it is what the button is disabled on.
 *
 * @typedef {object} Layout
 * @property {boolean} connected whether the page has the broker
 * @property {string | null} power what `layout` last reported — `on`, `off` or
 *   `stopped` — and `null` until it has reported
 */

/** A page that has not reached the broker: no connection, and nothing
 *  reported. It is what a band nobody handed a bus reading to carries, and it
 *  is what the page holds until the broker answers (`bus.ts`). */
export const UNREACHABLE = /** @type {Layout} */ ({
  connected: false,
  power: null,
});

/**
 * What `layout` reports the power as, off one payload on its state row.
 *
 * **A payload this page cannot read reads as `off`** (ADR-0017 d.2, #205).
 * That is the one reading here that is not what was said, and it is the safe
 * one: the button then offers the press that turns power on, which is a press
 * `layout` checks for itself, where a button drawn green over a payload nobody
 * could read would tell an operator the rails are hot on no evidence. Anything
 * but `on` or `stopped` is one of these — a row that is not JSON, a document
 * with no `power` in it, a word this page does not know.
 *
 * @param {string} payload the row as it arrived
 * @returns {string} `on`, `off` or `stopped`
 */
export function reported(payload) {
  /** @type {unknown} */
  let said;
  try {
    said = JSON.parse(payload);
  } catch {
    return OFF;
  }
  const power =
    typeof said === "object" && said !== null
      ? /** @type {{ power?: unknown }} */ (said).power
      : undefined;
  return power === ON || power === STOPPED ? power : OFF;
}

/** Why the power button cannot be pressed, in the order it is asked: no
 *  broker, no station answering, and no word from `layout` yet (ADR-0017 d.3,
 *  #205). The first that is true is what the button is titled, because a
 *  reader who cannot press it is owed the nearest reason rather than the last
 *  one. */
const NO_BUS = "no bus";
const NO_STATION = "no station";
const NO_LAYOUT = "no layout";

/** What the power button says while it can be pressed, which is what a press
 *  will do rather than the state it is in — as the monitor's pause is named,
 *  so that a reader on a busy railroad is never working out which state they
 *  are in. */
const CUTTING = "power off";
const HEATING = "power on";

/** What the link reads in words. The dot is the reading for a reader looking at
 *  it and these are the same reading for one who is not, so the band hands them
 *  to a reader either way; it draws them beside the dot while the station is not
 *  answering, because a fault is owed a sentence (issue 168, #138). */
const ANSWERING = "answering";
const OFFLINE = "dcc-ex offline";

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
 * @property {number | null} most the most it may draw, in milliamps, as the
 *   station's `<jG …>` gives it
 * @property {readonly number[]} recent the latest readings, oldest first
 */

/** A track nothing has been said about yet. */
const UNKNOWN = /** @type {Track} */ ({
  mode: null,
  hot: null,
  milliamps: null,
  most: null,
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
 * @property {string | null} build what the station says it is running
 * @property {Readonly<Record<string, Track>>} tracks each track the station
 *   has said anything about, by its letter
 */

/** A page that has just been opened: nothing said yet. The station is not
 *  called away — it is not called anything, which is what a link that is down
 *  says. */
export const QUIET = /** @type {Kept} */ ({
  spokeAt: null,
  build: null,
  tracks: {},
});

/**
 * The readings as they stand at one moment: what the band and the tiles are
 * drawn from.
 *
 * @typedef {object} Readings
 * @property {boolean} answering whether the station is answering — the link
 * @property {string | null} build what the station says it is running
 * @property {Readonly<Record<string, Track>>} tracks each track, by its letter
 */

/**
 * One **tile**: one track's readings, as they are drawn (CONTEXT.md **tile**,
 * issue 170).
 *
 * The power is what it is rather than a word, because the tile draws it as a
 * symbol and the words it is labelled with are the component's. The other
 * three are words, blank where the station has not said: a `0 mA` nobody
 * measured is a reading nobody took (ADR-0009 d.2).
 *
 * The letter is the tile's name and is not one of the three words drawn on it
 * (issue 170): it is the order the tiles come in, and it is what the power
 * symbol's words name the track by.
 *
 * @typedef {object} Tile
 * @property {string} track the letter the station names it by
 * @property {boolean | null} hot whether the track has power, which is what
 *   colours the symbol: `null` where the station has said nothing about it
 * @property {string} says whether the track has power, in words, which is what
 *   a reader who cannot see the colour is given
 * @property {string} mode what the track is set to — MAIN, PROG, DC…
 * @property {string} draws the current it draws, in milliamps
 * @property {string} most the most it may draw, in milliamps, after `max`
 */

/**
 * What the band's power button reads, is titled, and asks `layout` for
 * (ADR-0017 d.1, d.2, d.3).
 *
 * `reads` is the chip it wears and is `null` for every moment it presses
 * nothing: a chip drawn over a reading nobody can act on is a control round a
 * reading, and the three reasons it cannot be pressed are reasons the reading
 * is not one to draw either.
 *
 * @typedef {object} Power
 * @property {string | null} reads what `layout` reports the power as — `on`,
 *   `off` or `stopped` — and `null` where the button presses nothing
 * @property {string} title what the button is titled: why it cannot be
 *   pressed, or what a press will do
 * @property {string | null} wants what a press asks `layout` for, and `null`
 *   where it presses nothing
 */

/**
 * What the band carries: the **build**, the **link** and the power button.
 *
 * One value rather than a list of readings, because the three are three
 * different things — a word the station said, a light, and a control — and
 * what they have in common is only the chrome they sit on.
 *
 * @typedef {object} Band
 * @property {string} build what the station says it is running, blank while
 *   the link is down
 * @property {boolean} answering whether the station is answering — the link,
 *   which is the dot's colour
 * @property {string} says what the link reads in words, which is what a reader
 *   who cannot see the dot is given: `answering`, or `dcc-ex offline` while the
 *   station is not answering, where it is drawn beside the dot as well
 * @property {Power} power
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
  reading?.limits?.forEach((milliamps, i) => {
    const letter = LETTERS[i];
    if (letter === undefined) {
      return;
    }
    tracks[letter] = { ...(tracks[letter] ?? UNKNOWN), most: milliamps };
  });
  return {
    ...kept,
    spokeAt: at,
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
    ? { answering, build: kept.build, tracks: kept.tracks }
    : { answering, build: null, tracks: {} };
}

/**
 * What the power button reads, is titled, and asks `layout` for.
 *
 * **It is `layout`'s row and not the station's** (ADR-0017 d.1, d.2,
 * superseding ADR-0011 d.1). `layout` refuses an OFF while a run is going and
 * zeroes every locomotive's speed before a cut, and the translator runs the
 * **script**'s power handler (`control` ADR-0062): a press that sent `<1>` or
 * `<0>` through the **face** skipped all of it. So the colour is the row
 * `layout` reports and the press is a row the page writes, and the station's
 * own `<p…>` is a track's reading on a **tile** rather than this.
 *
 * **It presses nothing without all three of them** (ADR-0017 d.3, #205): the
 * broker, a station that is answering, and a word from `layout`. Each is a
 * different absence and the title says which — a press with no broker reaches
 * nothing, a press with no station is a railroad `layout` cannot apply it to,
 * and a railroad whose power nobody has reported has no state to offer the
 * other of (ADR-0009 d.2).
 *
 * @param {Readings} readings
 * @param {Layout} layout
 * @returns {Power}
 */
function power(readings, layout) {
  const title = !layout.connected
    ? NO_BUS
    : !readings.answering
      ? NO_STATION
      : layout.power === null
        ? NO_LAYOUT
        : layout.power === ON
          ? CUTTING
          : HEATING;
  const presses =
    layout.connected && readings.answering && layout.power !== null;
  return {
    reads: presses ? layout.power : null,
    title,
    wants: presses ? (layout.power === ON ? OFF : ON) : null,
  };
}

/**
 * What the band carries: the **build**, the **link**, and the power button
 * (ADR-0017, CONTEXT.md **band**).
 *
 * **Two channels meet here and nowhere else.** The build and the link are the
 * station talking, decoded off the **stream** (ADR-0008 d.2); the power is a
 * row `layout` reports on the bus (`bus.ts`). The button needs both — it is
 * disabled with no station as readily as with no broker — and this is where
 * they are put together, because what a band carries is one value and the
 * component that draws it works out no reading of its own.
 *
 * The link is a light rather than words, with the words beside it while it is
 * down: a station that is not answering is a fault and is owed a sentence, and
 * one that is answering is owed a glance (issue 168). The words are there in
 * either state all the same, because the band is what a reader who cannot see
 * the dot is given them by. The **build** goes with
 * the link, blanked by `asOf`, because a build from before a flash reported as
 * the one on the board would be this page saying what it cannot see.
 *
 * @param {Readings} readings
 * @param {Layout} layout
 * @returns {Band}
 */
export function band(readings, layout) {
  return {
    build: readings.build ?? BLANK,
    answering: readings.answering,
    says: readings.answering ? ANSWERING : OFFLINE,
    power: power(readings, layout),
  };
}

/**
 * Milliamps as a tile reads them, or blank where nothing has been measured.
 *
 * @param {number | null} measured
 * @returns {string}
 */
function milliamps(measured) {
  return measured === null ? BLANK : `${Math.round(measured)} mA`;
}

/**
 * What a track's power reads in words: the label the tile's symbol carries, so
 * that a reader who cannot see the colour is given the same reading — as the
 * **link**'s words are on the band (issue 168).
 *
 * `unknown` rather than `off` where the station has said nothing about the
 * track: a state nobody confirmed drawn as a state is a reading nobody took
 * (ADR-0009 d.2).
 *
 * @param {string} letter which track
 * @param {boolean | null} hot whether it has power
 * @returns {string}
 */
function says(letter, hot) {
  const state = hot === null ? "unknown" : hot ? "on" : "off";
  return `track ${letter} power is ${state}`;
}

/**
 * One **tile** per track the station names, in letter order (CONTEXT.md
 * **tile**, issue 170).
 *
 * The station's answer to `<=>` lists every track its firmware is built with,
 * so a track set to `NONE` has a tile too. A track the station has given a
 * current for and not yet a mode has one as well, and its mode is blank until
 * the answer to `<=>` arrives.
 *
 * **The whole row goes when the link goes down**, because `asOf` has taken the
 * tracks away: the tiles are the station talking and the station is not
 * talking (ADR-0008 d.3). The **link** and the **build** are the **band**'s and
 * are not tiles — the band carries both at every width one of them is drawn at
 * (issue 168, issue 170).
 *
 * @param {Readings} readings
 * @returns {Tile[]}
 */
export function tiles(readings) {
  return Object.entries(readings.tracks)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([letter, track]) => ({
      track: letter,
      hot: track.hot,
      says: says(letter, track.hot),
      mode: track.mode ?? BLANK,
      draws: milliamps(track.milliamps),
      most: track.most === null ? BLANK : `max ${milliamps(track.most)}`,
    }));
}
