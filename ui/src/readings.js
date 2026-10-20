/**
 * The readings the **band** and the **tile**s are made of: what the station
 * has said, and what a page draws out of it.
 *
 * Every reading about the station is the conversation, decoded on the page —
 * the station has no second channel and nothing is inferred on one (ADR-0008
 * d.2) — so what goes in here is lines and the moments they arrived, and what
 * comes out is the words on the chrome and on the tiles.
 *
 * **Two of the readings are not the station's.** The railroad's power is a row
 * `layout` reports on the bus, because `layout` is what the band asks for power
 * and what the station is told by the translator (ADR-0017); which railroad
 * `control` has loaded is a second row on the same connection (the
 * organisation's ADR-0014, #239). So this module reads both payloads and folds
 * them into the band, and the two channels are not mixed: a track's power on a
 * **tile** is still the station's `<p…>`, and nothing here reads one off the
 * other.
 *
 * **A pure function of what was said and of the moment it is asked for.** No
 * socket, no clock and no DOM: the page hands in its own clock, which is what
 * lets the whole of it be asserted — including what the page shows fifteen
 * seconds from now — on a machine with nothing plugged in
 * (`tests/ui/test_readings.py`). It is one of the modules of the page
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
 *  (ADR-0026 d.2, d.3, `control` ADR-0078). The toggle asks for `draining`
 *  from `on` and for `on` otherwise; STOP asks for `off`. */
const ON = "on";
const DRAINING = "draining";
const OFF = "off";

/** look's press words, as `look-power` fires them: the toggle's `on` and
 *  `off`, and the stop sign's `stopped` (ADR-0023). */
const PRESSED_STOP = "stopped";

/**
 * What `layout` says about the railroad's power, as the page reads it off the
 * bus (ADR-0017).
 *
 * `power` is the latest payload on `tc49/layout/state/power`, read by
 * `reported`, and `null` until one has arrived — which is a different reading
 * from `off`: a railroad nobody has reported the power of is not a railroad
 * with the power off (ADR-0009 d.2), and it is what the button is disabled on.
 *
 * `railroad` is the name off `tc49/layout/state/railroad`, read by `named`.
 * It is the one reading here that is about the railroad rather than about the
 * rails, and it is on this value because it comes up the same connection (the
 * organisation's ADR-0014, #239).
 *
 * **It has three answers and not two** (#242). The name is the railroad
 * `control` has loaded. `null` is a railroad row that says none is, which is
 * an ordinary state of a box (control #727). `undefined` is unreported: no
 * railroad row has arrived since the connection came up, which is the whole of
 * an outage and the gap between a reconnect and the retained row landing. The
 * three are three readings on the band — the name, `no railroad loaded`, and a
 * blank slot (#246) — and the **script** view acts on them differently: a row
 * that says none is loaded leaves nothing to edit, and an outage leaves the
 * editor where it is (`dccex-script.ts`).
 *
 * @typedef {object} Layout
 * @property {boolean} connected whether the page has the broker
 * @property {string | null} power what `layout` last reported — `on`,
 *   `draining` or `off` — and `null` until it has reported
 * @property {string | null | undefined} railroad which railroad `control` has
 *   loaded: the name, `null` where a row says none is, and `undefined` where
 *   none has been reported since the connection came up
 */

/** A page that has not reached the broker: no connection, and nothing
 *  reported. It is what a band nobody handed a bus reading to carries, and it
 *  is what the page holds until the broker answers (`bus.ts`). The railroad is
 *  unreported rather than none loaded — nothing has said which railroad
 *  `control` has, and a page that lost the broker is in this state as much as
 *  one that never reached it (#242). */
export const UNREACHABLE = /** @type {Layout} */ ({
  connected: false,
  power: null,
  railroad: undefined,
});

/**
 * What `layout` reports the power as, off one payload on its state row.
 *
 * **A payload this page cannot read reads as `off`** (ADR-0026 d.3, #205).
 * That is the one reading here that is not what was said, and it is the safe
 * one: the button then offers the press that turns power on, which is a press
 * `layout` checks for itself, where a button drawn green over a payload nobody
 * could read would tell an operator the rails are hot on no evidence. Anything
 * but `on` or `draining` is one of these — a row that is not JSON, a document
 * with no `power` in it, a word this page does not know, `stopped` included
 * (ADR-0026 d.3).
 *
 * @param {string} payload the row as it arrived
 * @returns {string} `on`, `draining` or `off`
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
  return power === ON || power === DRAINING ? power : OFF;
}

/**
 * Which railroad `control` has loaded, off one payload on its railroad row.
 *
 * The `name` field, which is the field the **translator** reads the same row
 * for (the organisation's ADR-0014, `src/dccex/translator.py`). `""` is a box
 * that has loaded no railroad, which is an ordinary state of one (control
 * #727), and it reads as `null` — as does a payload that is not JSON, one with
 * no `name` in it, and a `name` that is not a string. What the band says in
 * that state is `band()`'s sentence rather than a word invented here: a
 * reading nobody took is an absence (ADR-0009 d.2).
 *
 * @param {string} payload the row as it arrived
 * @returns {string | null} the name, or `null` where none was named
 */
export function named(payload) {
  /** @type {unknown} */
  let said;
  try {
    said = JSON.parse(payload);
  } catch {
    return null;
  }
  const name =
    typeof said === "object" && said !== null
      ? /** @type {{ name?: unknown }} */ (said).name
      : undefined;
  return typeof name === "string" && name !== "" ? name : null;
}

/** Why neither press can be pressed: no broker, or no word from `layout`
 *  yet. One reason for both (ADR-0026 d.4). */
const WAITING = "Waiting for the station";

/** What the power button says while it can be pressed, which is what a press
 *  will do rather than the state it is in — as the monitor's pause is named,
 *  so that a reader on a busy railroad is never working out which state they
 *  are in. */
const DRAINS = "power off once every train is at rest";
const HEATING = "power on";

/** What the STOP press says while it can be pressed, which is what a press
 *  does rather than the state it leaves the railroad in. */
const STOPS = "cut the power at once";

/** What the link reads in words. The dot is the reading for a reader looking at
 *  it and these are the same reading for one who is not, so the band hands them
 *  to a reader either way; it draws them beside the dot while the station is not
 *  answering, because a fault is owed a sentence (issue 168, #138). */
const ANSWERING = "answering";
const OFFLINE = "dcc-ex offline";

/** What the band says where a railroad row says `control` has loaded none
 *  (#239). A sentence rather than a blank: nothing where a name goes reads as
 *  a name that went missing, and a box with no railroad loaded is an ordinary
 *  state of one (control #727, ADR-0009 d.2).
 *
 *  It is not what an unreported railroad reads as. Nothing has said which
 *  railroad `control` has there, so the slot is blank (#246). */
const NO_RAILROAD = "no railroad loaded";

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
 * (ADR-0026 d.2, d.3, d.4).
 *
 * `reads` is the chip it wears and is `null` for every moment it presses
 * nothing: a chip drawn over a reading nobody can act on is a control round a
 * reading, and the reason it cannot be pressed is a reason the reading is not
 * one to draw either.
 *
 * @typedef {object} Power
 * @property {string | null} reads what `layout` reports the power as — `on`,
 *   `draining` or `off` — and `null` where the button presses nothing
 * @property {string} title what the button is titled: why it cannot be
 *   pressed, or what a press will do
 * @property {string | null} wants what a press asks `layout` for, and `null`
 *   where it presses nothing
 */

/**
 * What the band's STOP press is titled and asks `layout` for (ADR-0026 d.2,
 * d.4).
 *
 * No `reads`: it wears one chip in every state and draws no reading of the
 * railroad at all (ADR-0020 d.4). What it asks for is the same word every
 * time, and it is here rather than in the component for the reason the power
 * button's ask is — the band works out no reading of its own.
 *
 * @typedef {object} Stop
 * @property {string} title what the press is titled: what it does, or why it
 *   cannot be pressed
 * @property {string | null} wants `off`, and `null` where it presses nothing
 */

/**
 * What the band carries: the railroad, the **link** and the power button.
 *
 * One value rather than a list of readings, because they are different things
 * — a word `layout` said, a light, and a control — and what they have in
 * common is only the chrome they sit on.
 *
 * @typedef {object} Band
 * @property {string} railroad which railroad `control` has loaded,
 *   `no railroad loaded` where a row says none is, and blank while no row has
 *   arrived since the connection came up
 * @property {boolean} answering whether the station is answering — the link,
 *   which is the dot's colour
 * @property {string} says what the link reads in words, which is what a reader
 *   who cannot see the dot is given: `answering`, or `dcc-ex offline` while the
 *   station is not answering, where it is drawn beside the dot as well
 * @property {Power} power
 * @property {Stop} stop
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
 * What `layout` is asked for, off the word look's `look-power` fires (ADR-0026
 * d.2). `control`'s `asked()` in `ui/src/model/commands.ts` is the same map.
 *
 * The toggle's `off` drains, its `on` asks for `on` and ends a drain, and the
 * stop sign's `stopped` cuts the power at once. A word look does not fire asks
 * for nothing.
 *
 * @param {string} pressed what `look-power` fired
 * @returns {string | null} what `tc49/layout/power_wanted` carries, or `null`
 */
export function asked(pressed) {
  return pressed === OFF
    ? DRAINING
    : pressed === ON
      ? ON
      : pressed === PRESSED_STOP
        ? OFF
        : null;
}

/**
 * Whether the band's presses can be pressed: the broker, and a word from
 * `layout` (ADR-0026 d.4). `control`'s `supply()` is the same rule.
 *
 * @param {Layout} layout
 * @returns {boolean}
 */
function live(layout) {
  return layout.connected && layout.power !== null;
}

/**
 * What the power button reads, is titled, and asks `layout` for.
 *
 * **It is `layout`'s row and not the station's** (ADR-0026 d.2). `layout`
 * drains the railroad on `draining` and zeroes every locomotive's speed before
 * it cuts on `off` (`control` ADR-0078), and the translator runs the
 * **script**'s power handler: a press that sent `<1>` or `<0>` through the
 * **face** skipped all of it. So the colour is the row `layout` reports and
 * the press is a row the page writes, and the station's own `<p…>` is a
 * track's reading on a **tile** rather than this.
 *
 * It asks for what look's toggle fires, through `asked`: `draining` from `on`
 * and `on` otherwise (ADR-0026 d.2). It is dead on the same rule as STOP.
 *
 * @param {Layout} layout
 * @returns {Power}
 */
function power(layout) {
  if (!live(layout)) {
    return { reads: null, title: WAITING, wants: null };
  }
  const hot = layout.power === ON;
  return {
    reads: layout.power,
    title: hot ? DRAINS : HEATING,
    wants: asked(hot ? OFF : ON),
  };
}

/**
 * What the band's STOP press is titled and asks `layout` for: `off`, whatever
 * the railroad is doing (ADR-0026 d.2), and dead on the same rule as the
 * toggle (d.4).
 *
 * @param {Layout} layout
 * @returns {Stop}
 */
function stop(layout) {
  return live(layout)
    ? { title: STOPS, wants: asked(PRESSED_STOP) }
    : { title: WAITING, wants: null };
}

/**
 * What the band carries: the railroad, the **link**, and the two presses
 * (ADR-0017, ADR-0026, docs/ui/README.md). The **build** is not on it
 * (ADR-0027).
 *
 * **Two channels meet here and nowhere else.** The link is the station
 * talking, decoded off the **stream** (ADR-0008 d.2); the power and the
 * railroad's name are rows `layout` reports on the bus (`bus.ts`). This is
 * where they are put together, because what a band carries is one value and
 * the component that draws it works out no reading of its own.
 *
 * **The railroad does not go with the link.** It is `layout`'s row rather than
 * the station's, so a station that has stopped answering is still a railroad
 * `control` has loaded; what takes it away is the bus going, which hands this
 * module `UNREACHABLE` (`bus.ts`).
 *
 * **A railroad nobody has reported is blank and not a sentence** (#246). An
 * outage, and the gap after a reconnect, leave the railroad unreported, and
 * `control` may have one loaded the whole time — so `no railroad loaded` there
 * is the page reporting a state nobody told it (ADR-0009 d.2). Blank, and the
 * presses beside it are already dead. A row that says none is loaded is the
 * other state and keeps the sentence (#242, `Layout`).
 *
 * **Both presses are dead on one rule** (ADR-0026 d.4): while the bus is
 * unreachable or `layout` has not reported the power. A silent station does
 * not hold either.
 *
 * The link is a light rather than words, with the words beside it while it is
 * down: a station that is not answering is a fault and is owed a sentence, and
 * one that is answering is owed a glance (issue 168). The words are there in
 * either state all the same, because the band is what a reader who cannot see
 * the dot is given them by.
 *
 * @param {Readings} readings
 * @param {Layout} layout
 * @returns {Band}
 */
export function band(readings, layout) {
  return {
    railroad:
      layout.railroad === undefined ? BLANK : (layout.railroad ?? NO_RAILROAD),
    answering: readings.answering,
    says: readings.answering ? ANSWERING : OFFLINE,
    power: power(layout),
    stop: stop(layout),
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
 * talking (ADR-0008 d.3). The **link** is the **band**'s and is not a tile
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
