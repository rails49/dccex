/**
 * The **journal** read: the lines the translator kept in, the **incident**s a
 * person should look at and the counts beside them out.
 *
 * The file is what the station said about power and nothing more — the
 * translator decides nothing about a line (ADR-0022 d.2, d.3) — so being an
 * incident is a reading this module makes, and a rule that changes here is run
 * over the whole journal again under itself (docs/ui/README.md). The
 * station prints no flip count and no peak current; what is below counts them
 * out of its words.
 *
 * **One pure function of the lines and the period** (ADR-0022 d.5, as the
 * decoder, ADR-0009 d.1). No socket, no clock and no DOM: the only time it
 * knows is the `at` each line carries, so the same file reads the same way for
 * ever and is asserted as lines in and incidents out on a machine with nothing
 * plugged in (`tests/ui/test_journal.py`).
 *
 * **It reads the station's words and not a reading somebody made of them.** A
 * `<p…>` goes through the **decoder**, which is where the `<…>` syntax is
 * known (ADR-0009 d.3); a `<* TRACK X … *>` is read here, being the line the
 * decoder has no gloss for. A line's `district` says the same letter the
 * message does; its `mode` and `limit` are the one thing a reader cannot get
 * back afterwards and are taken from the line.
 *
 * **Splitting the file into lines is the caller's.** What arrives here is the
 * lines already parsed, so that a truncated last line — the file is served
 * while the translator appends to it (ADR-0022 d.4) — is the page's to drop
 * rather than this module's to guess at.
 *
 * It is JavaScript with its types in JSDoc, as `decoder.js`, `message.js`,
 * `readings.js`, `releases.js`, `flash.js`, `framing.js`, `monitor.js` and
 * `incidents.js` are: the modules the gate runs rather than reads, listed in
 * `tests/ui/test_decoder.py`. `tsc` checks this file as it checks the rest
 * (`ui/tsconfig.json`).
 */

import { read as decoded } from "./decoder.js";

/**
 * How soon after a flip an alert or a trip is the flip's, in milliseconds.
 *
 * A reverser that flipped and cleared the short is the railroad working; one
 * that flipped and did not is the thing to look at, and what tells the two
 * apart is how close together they are. The number is the page's and not the
 * hardware's — the station prints no flip count — and it is here to be changed
 * when the journal says what the right one is (ADR-0022, context).
 */
export const FLIPPED_MS = 250;

/** How many flips on one district inside `REPEATED_MS` are a reverser that
 *  cannot settle. The third is the one that says so: two is a district
 *  reversed and reversed back. */
export const REPEATS = 3;

/** How long `REPEATS` flips fall inside to be read as one, in milliseconds. */
export const REPEATED_MS = 1000;

/** An incident with a trip in it: a district the station cut itself
 *  (GLOSSARY.md, **trip**). */
const TRIP = "trip";

/** A current over the district's limit that did not become a trip. */
const SPIKE = "spike";

/** A flip the short outlived: an alert or a trip within `FLIPPED_MS` of one. */
const REVERSAL = "reversal";

/** A reverser that cannot settle: `REPEATS` flips on one district inside
 *  `REPEATED_MS`. */
const REPEATED = "repeated reversal";

/** A flip the station did not call fast. */
const SLOW = "slow reversal";

/** The link going down: the station stopped answering, and every district's
 *  readings went with it (GLOSSARY.md, **link**). */
const LINK = "link";

/** The station restarting under a railroad that was running (ADR-0021). */
const RESTART = "restart";

/**
 * The kinds a district's incidents are counted by, in the order the kind of
 * one is decided: the most specific reading of what happened wins.
 *
 * A reverser that repeated is read as having repeated even where a trip
 * followed, because the reverser is the thing to look at; a flip a trip
 * followed is a reversal rather than a trip, because what the district did is
 * why it cut. A `link` and a `restart` are the station's and are counted
 * there.
 */
export const KINDS = [REPEATED, REVERSAL, SLOW, TRIP, SPIKE];

/** What the station calls a flip, and the word that makes it a fast one. */
const INVERT = "INVERT";
const FAST = "(fast)";

/** The words the station cuts a district with (ADR-0016 d.3 as amended).
 *  `FAULT PIN detected` and not `FAULT PIN`: `FAULT PIN (100ms ignore)` is a
 *  fault the station rode out, which is not a cut. */
const TRIPS = ["POWER OVERLOAD", "FAST OVERLOAD", "FAULT PIN detected"];

/** The station retrying a district it cut, which ends the time it was cut for
 *  and nothing else: it is powered again at `NORMAL`. */
const RESTORE = "POWER RESTORE";

/** The district is itself again, which closes an incident. */
const NORMAL = "NORMAL";

/** The current on a district is over its limit (ADR-0016 d.4). */
const ALERT = "ALERT";

/** What a programming track is set to. An alert on one is a decoder
 *  acknowledging, which is the track working (docs/ui/README.md). */
const PROG = "PROG";

/** What the link line says when the station stopped answering. */
const DOWN = "down";

/** Milliseconds in an hour: what the powered time is counted in, and what it
 *  is reported in. */
const HOUR_MS = 3600000;

/**
 * One line of the journal, as the translator wrote it (ADR-0022 d.2,
 * `docs/dccex/README.md`).
 *
 * `mode` and `limit` are `null` where the station had said nothing yet, which
 * is an ordinary state of the first second of a link; `build` is empty
 * whenever the station is not answering (GLOSSARY.md, **build**).
 *
 * @typedef {object} Line
 * @property {string} at when the line arrived, ISO 8601
 * @property {string} [railroad] which railroad was loaded
 * @property {string} [build] what the station said it was running
 * @property {string} [said] the whole `<…>` message, verbatim
 * @property {string} [district] the district the message names
 * @property {string | null} [mode] what that district was set to
 * @property {number | null} [limit] the most it could draw, in milliamps
 * @property {string} [link] `down` or `up`, on a line about the link
 * @property {boolean} [restart] true on a line about the station restarting
 */

/**
 * Which lines are read: a start and an end, a build, or any of the three
 * together. A field left out is not a bound.
 *
 * A build is a period because that is how the question is asked — what
 * happened while the station was running this — and every line carries one
 * (ADR-0022 d.2).
 *
 * @typedef {object} Period
 * @property {string} [start] the first stamp read, inclusive
 * @property {string} [end] the last stamp read, inclusive
 * @property {string} [build] only the lines the station said this on
 */

/**
 * One thing in the journal a person should look at.
 *
 * `district` is `null` on the two that are the station's: the link going down
 * and the station restarting. `end` is the stamp of the line that closed it,
 * and the last line read where nothing did — a journal that stops while a
 * district is still shorted says nothing about when it came back.
 *
 * `milliamps` is the highest the station printed inside it, and `null` where
 * it printed none: an `ALERT FAULT` carries no number, and a zero nobody
 * measured is a reading nobody took (ADR-0009 d.2).
 *
 * @typedef {object} Incident
 * @property {string} kind one of `KINDS`, or `link` or `restart`
 * @property {string | null} district which district, or `null` for the
 *   station's own
 * @property {string} start the stamp of the line that opened it
 * @property {string} end the stamp of the line that closed it
 * @property {number} trips how many times the station cut the district in it
 * @property {number | null} milliamps the highest it printed in it
 * @property {number} cut how long the district was cut for, in milliseconds
 * @property {number[]} taken which journal lines it is made of, by their place
 *   in the lines this was handed, in the order they were written
 */

/**
 * What a district did over the period.
 *
 * `hours` is the time it was powered: from a `<p1 X>` until a `<p0 X>`, a link
 * loss or a trip, and again from a `NORMAL`. `rate` is its incidents over
 * those hours, and `null` where it was never powered — a rate over no time is
 * a number nobody can read.
 *
 * `flips` counts the flips nothing came of, which is the reverser doing its
 * job. A flip an incident took is counted in that incident instead.
 *
 * @typedef {object} District
 * @property {Record<string, number>} incidents how many of each of `KINDS`
 * @property {number} trips how many times the station cut it
 * @property {number} cut how long it was cut for, in milliseconds
 * @property {number | null} milliamps the highest the station printed about it
 * @property {number} flips the flips nothing came of
 * @property {number} hours how long it was powered
 * @property {number | null} rate incidents per hour powered
 */

/**
 * What the whole station did over the period: the two things in the journal
 * that are about no district.
 *
 * @typedef {object} Station
 * @property {number} links how many times the link went down
 * @property {number} restarts how many times the station restarted
 */

/**
 * The journal read.
 *
 * @typedef {object} Read
 * @property {Incident[]} incidents in the order they opened
 * @property {Record<string, District>} districts by letter, A first
 * @property {Station} station
 */

/**
 * What one `<* TRACK X … *>` line says, or `null` where it is a diagnostic
 * this does not read.
 *
 * @typedef {object} Diagnostic
 * @property {string} district the letter the line names
 * @property {string} word `trip`, `restore`, `normal`, `alert` or `flip`
 * @property {boolean} fast whether a flip carried the station's `(fast)`
 * @property {number | null} milliamps the highest current the line printed
 */

/** What a `<* TRACK X … *>` line is, and where its words start. */
const DIAGNOSTIC = /^<\* TRACK ([A-H]) (.+) \*>$/;

/** A current the station printed, with the district's limit told apart from
 *  it: `3120mA (max 3000mA)` is one reading and one setting. */
const MILLIAMPS = /(max )?(\d+)mA/g;

/**
 * The highest current the line printed, or `null` where it printed none.
 *
 * The limit is not one of them. `POWER OVERLOAD 3120mA (max 3000mA)` says what
 * the district drew and what it was allowed, and a reader counting the highest
 * mA printed is asking the first.
 *
 * @param {string} said the words of the line
 * @returns {number | null}
 */
function milliamps(said) {
  /** @type {number | null} */
  let most = null;
  for (const found of said.matchAll(MILLIAMPS)) {
    if (found[1] === undefined) {
      most = Math.max(most ?? 0, Number(found[2]));
    }
  }
  return most;
}

/**
 * The higher of two currents, either of which may be nothing at all.
 *
 * @param {number | null} most what has been printed so far
 * @param {number | null} said what this line printed
 * @returns {number | null}
 */
function highest(most, said) {
  return said === null ? most : Math.max(most ?? 0, said);
}

/**
 * What a `<* TRACK X … *>` line says, or `null` for one this does not read.
 *
 * Silence rather than a guess, as the decoder's (ADR-0009 d.2): a
 * `CURRENT (… ignore)` and a `FAULT PIN (100ms ignore)` are the station
 * talking about a district it did not cut, and an incident read off them is
 * one nobody had.
 *
 * @param {string} said the whole message, verbatim
 * @returns {Diagnostic | null}
 */
function diagnosed(said) {
  const found = DIAGNOSTIC.exec(said);
  if (found === null) {
    return null;
  }
  const [, district, rest] = found;
  const word = TRIPS.some((trip) => rest.startsWith(trip))
    ? "trip"
    : rest.startsWith(RESTORE)
      ? "restore"
      : rest.startsWith(NORMAL)
        ? "normal"
        : rest.startsWith(ALERT)
          ? "alert"
          : rest.startsWith(INVERT)
            ? "flip"
            : null;
  if (word === null) {
    return null;
  }
  return {
    district,
    word,
    fast: rest.includes(FAST),
    milliamps: milliamps(rest),
  };
}

/**
 * Whether a line belongs to the period: milliseconds against milliseconds, so
 * that two stamps written at different offsets compare as the instants they
 * are.
 *
 * @param {number} at when the line arrived
 * @param {Line} line the line itself, for the build it carries
 * @param {Period} period what is being read
 * @returns {boolean}
 */
function inside(at, line, period) {
  if (period.build !== undefined && (line.build ?? "") !== period.build) {
    return false;
  }
  if (period.start !== undefined && at < Date.parse(period.start)) {
    return false;
  }
  return period.end === undefined || at <= Date.parse(period.end);
}

/**
 * Whether the period reads `line`, which is the question `read` below asks of
 * every line and the one the view asks again of the lines it draws.
 *
 * One rule and one place: the lines an **incident** is made of and the ones no
 * incident took are the period's as much as the counts are, so a second
 * spelling of it in `incidents.js` would be a second answer to which lines a
 * reader is looking at (#266).
 *
 * A line nobody can place in time is read as nothing at all: every count here
 * is of when something happened.
 *
 * @param {Line} line one line of the journal
 * @param {Period} [period] which lines are read; all of them by default
 * @returns {boolean}
 */
export function reads(line, period = {}) {
  const at = Date.parse(line.at);
  return !Number.isNaN(at) && inside(at, line, period);
}

/**
 * A district as it is counted up, before the hours are divided out.
 *
 * @typedef {object} Counted
 * @property {Record<string, number>} incidents
 * @property {number} trips
 * @property {number} cut
 * @property {number | null} milliamps
 * @property {number} flips
 * @property {number} powered how long it has been powered, in milliseconds
 * @property {number | null} since when it was powered from, or `null`
 */

/**
 * An incident while it is still open: what is on it, and what its kind is
 * decided from when it closes.
 *
 * @typedef {object} Reading
 * @property {string | null} district
 * @property {string} start
 * @property {string | null} fixed the kind where it is not read off what
 *   happened, which is the link's and the restart's
 * @property {number} trips
 * @property {number | null} milliamps
 * @property {number} cut
 * @property {number | null} from when the district was cut from, or `null`
 * @property {string | null} mode what the station had said the district was
 * @property {boolean} tripped
 * @property {boolean} alerted
 * @property {boolean} normal whether the station said it was normal again
 * @property {boolean} repeated whether a flip of it was the third in a second
 * @property {boolean} slow whether a flip of it was not a fast one
 * @property {boolean} caused whether an alert or a trip followed a flip of it
 * @property {number[]} taken which lines have been folded into it
 */

/**
 * A flip the journal carries, and whether an incident has taken it.
 *
 * @typedef {object} Flip
 * @property {string} district
 * @property {number} at
 * @property {number} index where its line sits in the journal
 * @property {boolean} fast
 * @property {boolean} spent whether an incident has taken it
 */

/**
 * An incident nothing has happened in yet.
 *
 * @param {string | null} district which district, or `null` for the station's
 * @param {string} start the stamp of the line that opened it
 * @param {string | null} mode what the station had said that district was
 * @param {number} index where the line that opened it sits in the journal
 * @param {string | null} [fixed] the kind, where it is not read off what
 *   happened
 * @returns {Reading}
 */
function reading(district, start, mode, index, fixed = null) {
  return {
    district,
    start,
    fixed,
    taken: [index],
    trips: 0,
    milliamps: null,
    cut: 0,
    from: null,
    mode,
    tripped: false,
    alerted: false,
    normal: false,
    repeated: false,
    slow: false,
    caused: false,
  };
}

/**
 * The kind of a reading: the most specific of what happened in it (`KINDS`).
 *
 * @param {Reading} held
 * @returns {string}
 */
function kind(held) {
  if (held.fixed !== null) {
    return held.fixed;
  }
  if (held.repeated) {
    return REPEATED;
  }
  if (held.caused) {
    return REVERSAL;
  }
  if (held.slow) {
    return SLOW;
  }
  return held.tripped ? TRIP : SPIKE;
}

/**
 * Whether `flip` was the `REPEATS`th on its district inside `REPEATED_MS`.
 *
 * Asked of a flip an alert or a trip has just taken, which is how a burst that
 * ended in a short reads as the reverser it was.
 *
 * @param {readonly Flip[]} flips every flip read so far
 * @param {Flip} flip the one the incident took
 * @returns {boolean}
 */
function repeats(flips, flip) {
  const within = flips.filter(
    (found) =>
      found.district === flip.district &&
      found.at <= flip.at &&
      flip.at - found.at < REPEATED_MS,
  );
  return within.length >= REPEATS;
}

/**
 * The last flip no later than `at` and inside `FLIPPED_MS` of it, or
 * `undefined` where there is none. On any district: a reverser flipping one
 * shorts whatever is across the join (ADR-0022, context).
 *
 * @param {readonly Flip[]} flips every flip read so far
 * @param {number} at when the alert or the trip arrived
 * @returns {Flip | undefined}
 */
function flipped(flips, at) {
  const flip = flips.at(-1);
  return flip !== undefined && at - flip.at <= FLIPPED_MS ? flip : undefined;
}

/**
 * One district's counts, with the time it was powered in hours and the rate
 * divided out.
 *
 * @param {Counted} held
 * @returns {District}
 */
function drawn(held) {
  const hours = held.powered / HOUR_MS;
  const incidents = Object.values(held.incidents).reduce(
    (all, count) => all + count,
    0,
  );
  return {
    incidents: held.incidents,
    trips: held.trips,
    cut: held.cut,
    milliamps: held.milliamps,
    flips: held.flips,
    hours,
    rate: hours === 0 ? null : incidents / hours,
  };
}

/**
 * What a line before the period says about which districts were powered.
 *
 * The journal keeps a `<p…>` only where it changed (ADR-0022 d.2 as amended),
 * so a period that opens with a district already on may carry no `<p1 X>` for
 * it; this is what the period starts from instead (#275). A link that went and
 * a station that restarted are followed by a `<p…>` for every district, so
 * what came before them is forgotten.
 *
 * @param {Map<string, boolean>} powered by district, whether it was on
 * @param {Line} line
 */
function was(powered, line) {
  if (line.link === DOWN || line.restart === true) {
    powered.clear();
    return;
  }
  if (line.said === undefined) {
    return;
  }
  const power = decoded(line.said);
  if (power !== null && power.hot !== undefined) {
    if (power.track !== undefined) {
      powered.set(power.track, power.hot);
    }
    return;
  }
  const told = diagnosed(line.said);
  if (told?.word === "trip") {
    powered.set(told.district, false);
  } else if (told?.word === "normal") {
    powered.set(told.district, true);
  }
}

/**
 * The incidents in `lines`, and the counts per district and for the station.
 *
 * @param {readonly Line[]} lines the journal, in the order it was written
 * @param {Period} [period] which of them to read; all of them by default
 * @returns {Read}
 */
export function read(lines, period = {}) {
  /** @type {Incident[]} */
  const incidents = [];
  /** @type {Map<string, Counted>} */
  const districts = new Map();
  /** @type {Map<string, Reading>} */
  const open = new Map();
  /** @type {Flip[]} */
  const flips = [];
  const station = { links: 0, restarts: 0 };
  /** @type {Reading | null} */
  let outage = null;
  let ended = "";
  let at = 0;
  /** @type {Map<string, boolean> | null} */
  let before = new Map();

  /**
   * The district's counts, started where this is the first line about it: a
   * district the file names is a row on the page, whatever it went on to do.
   *
   * @param {string} name
   * @returns {Counted}
   */
  const counted = (name) => {
    let held = districts.get(name);
    if (held === undefined) {
      /** @type {Record<string, number>} */
      const none = {};
      for (const each of KINDS) {
        none[each] = 0;
      }
      held = {
        incidents: none,
        trips: 0,
        cut: 0,
        milliamps: null,
        flips: 0,
        powered: 0,
        since: null,
      };
      districts.set(name, held);
    }
    return held;
  };

  /**
   * One incident closed and counted, unless what it reads as is the railroad
   * working.
   *
   * @param {Reading} held
   */
  const closed = (held) => {
    if (held.from !== null) {
      held.cut += at - held.from;
      held.from = null;
    }
    const how = kind(held);
    // The programming track answering a decoder: an alert that ended in
    // normal, nothing cut, on a district the station said was PROG
    // (docs/ui/README.md).
    if (how === SPIKE && held.normal && held.mode === PROG) {
      return;
    }
    incidents.push({
      kind: how,
      district: held.district,
      start: held.start,
      end: ended,
      trips: held.trips,
      milliamps: held.milliamps,
      cut: held.cut,
      // The flips a burst took are folded in after the line that opened the
      // reading, and a line reached twice is one line: what goes out is the
      // journal's own order, once each.
      taken: [...new Set(held.taken)].sort((first, second) => first - second),
    });
    if (held.district !== null) {
      const counts = counted(held.district);
      counts.incidents[how] += 1;
      counts.trips += held.trips;
      counts.cut += held.cut;
    }
  };

  /**
   * One district's incident closed.
   *
   * The line that closed it is part of what it is made of — the `NORMAL`, the
   * power going off, the link going — and is named where there is one. The
   * journal running out is not one: the last line of the file closes whatever
   * is open, and it is somebody else's line.
   *
   * @param {string} name
   * @param {number | null} [index] where the line that closed it sits
   */
  const closes = (name, index = null) => {
    const held = open.get(name);
    if (held !== undefined) {
      open.delete(name);
      if (index !== null) {
        held.taken.push(index);
      }
      closed(held);
    }
  };

  /** @param {string} name */
  const powers = (name) => {
    const held = counted(name);
    if (held.since === null) {
      held.since = at;
    }
  };

  /** @param {string} name */
  const unpowers = (name) => {
    const held = counted(name);
    if (held.since !== null) {
      held.powered += at - held.since;
      held.since = null;
    }
  };

  for (const [index, line] of lines.entries()) {
    const when = Date.parse(line.at);
    if (!reads(line, period)) {
      if (before !== null) {
        was(before, line);
      }
      continue;
    }
    if (before !== null) {
      // The period starts powered where the lines before it left a district
      // on, from its start where it has one.
      at = period.start === undefined ? when : Date.parse(period.start);
      for (const [name, on] of before) {
        if (on) {
          powers(name);
        }
      }
      before = null;
    }
    at = when;
    ended = line.at;
    if (line.link === DOWN) {
      station.links += 1;
      for (const name of [...open.keys()]) {
        closes(name, index);
      }
      for (const name of [...districts.keys()]) {
        unpowers(name);
      }
      outage ??= reading(null, line.at, null, index, LINK);
    } else if (line.link !== undefined && outage !== null) {
      outage.taken.push(index);
      closed(outage);
      outage = null;
    }
    if (line.restart === true) {
      station.restarts += 1;
      closed(reading(null, line.at, null, index, RESTART));
    }
    if (line.said === undefined) {
      continue;
    }
    const power = decoded(line.said);
    if (power !== null && power.hot !== undefined) {
      // A `<p…>` naming no district is passed over, as `replies.kept` passes
      // it over in the translator: the bare `<p0>` and `<p1>`, and the ones
      // naming MAIN, PROG or JOIN, are printed in `broadcastPower()` alone and
      // always after a `<pN X>` line for each district, so they say nothing
      // those do not (ADR-0022 d.2 as amended, #269). A journal written before
      // that still carries them, and read as every district's they would close
      // every open incident and move every powered clock.
      if (power.track === undefined) {
        continue;
      }
      if (power.hot) {
        powers(power.track);
      } else {
        closes(power.track, index);
        unpowers(power.track);
      }
      continue;
    }
    const told = diagnosed(line.said);
    if (told === null) {
      continue;
    }
    const name = told.district;
    const district = counted(name);
    district.milliamps = highest(district.milliamps, told.milliamps);
    if (told.word === "flip") {
      const within = flips.filter(
        (found) => found.district === name && at - found.at < REPEATED_MS,
      );
      const flip = { district: name, at, index, fast: told.fast, spent: false };
      flips.push(flip);
      const repeated = within.length + 1 >= REPEATS;
      let held = open.get(name);
      if (held === undefined && (repeated || !told.fast)) {
        held = reading(name, line.at, line.mode ?? null, index);
        open.set(name, held);
      }
      if (held !== undefined) {
        held.repeated = held.repeated || repeated;
        held.slow = held.slow || !told.fast;
        flip.spent = true;
        held.taken.push(index);
        // The flips the third one counted are part of what it says, so a burst
        // of three is one reading and not an incident with two good flips
        // beside it.
        for (const counting of within) {
          counting.spent = true;
          held.taken.push(counting.index);
        }
      }
      continue;
    }
    if (told.word === "restore") {
      const held = open.get(name);
      if (held !== undefined) {
        held.taken.push(index);
        if (held.from !== null) {
          held.cut += at - held.from;
          held.from = null;
        }
      }
      continue;
    }
    if (told.word === "normal") {
      const held = open.get(name);
      if (held !== undefined) {
        held.normal = true;
        held.milliamps = highest(held.milliamps, told.milliamps);
        closes(name, index);
      }
      powers(name);
      continue;
    }
    // An alert or a trip: the district is the thing to look at from here.
    let held = open.get(name);
    if (held === undefined) {
      held = reading(name, line.at, line.mode ?? null, index);
      open.set(name, held);
    }
    held.taken.push(index);
    held.milliamps = highest(held.milliamps, told.milliamps);
    const flip = flipped(flips, at);
    if (flip !== undefined) {
      held.caused = true;
      held.repeated = held.repeated || repeats(flips, flip);
      flip.spent = true;
      // The flip the short outlived is part of the incident rather than a flip
      // the reverser got away with, so the line it is on is one of this
      // incident's.
      held.taken.push(flip.index);
    }
    if (told.word === "trip") {
      held.tripped = true;
      held.trips += 1;
      held.from ??= at;
      unpowers(name);
    } else {
      held.alerted = true;
    }
  }

  // The journal stops. What is still open ends on its last line, and what is
  // still powered was powered until then.
  for (const name of [...open.keys()]) {
    closes(name);
  }
  if (outage !== null) {
    closed(outage);
  }
  for (const name of [...districts.keys()]) {
    unpowers(name);
  }
  for (const flip of flips) {
    if (!flip.spent && flip.fast) {
      counted(flip.district).flips += 1;
    }
  }
  /** @type {Record<string, District>} */
  const counts = {};
  for (const name of [...districts.keys()].sort()) {
    counts[name] = drawn(counted(name));
  }
  return { incidents, districts: counts, station };
}
