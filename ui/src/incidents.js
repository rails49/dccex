/**
 * What the **journal** view draws: the counts in a table, the **incident**s
 * newest first with the lines each is made of, and the words its controls are
 * pressed with.
 *
 * It is the journal's other half. `journal.js` is the reading — lines and a
 * period in, incidents and counts out (ADR-0022 d.5) — and this is what a
 * person reads: the file split into lines, the periods the file offers, every
 * number turned into the words it is drawn as, and which journal lines sit
 * under which row. The same split `readings.js` is on the other side of from
 * `decoder.js`: one module reads the station's words and one says what the
 * page shows for them.
 *
 * **It is pure, and the only time it knows is what it is handed** (ADR-0009
 * d.3, ADR-0022 d.5). The stamps come off the lines and the clock comes in as
 * an argument, so a journal reads the same way for ever and every sentence an
 * operator reads is asserted by running this rather than by reading the
 * component that draws it (`tests/ui/test_incidents.py`).
 *
 * **Splitting the served file into lines is here, because it is the caller's**
 * (`journal.js`). The mirror serves the file while the translator appends to
 * it (ADR-0022 d.4), so the last line can be half written: a line that does
 * not parse is dropped and the rest of the file is read.
 *
 * **A reading nobody took is blank and every number is drawn.** A district the
 * station printed no current for and a district that was never powered have no
 * peak and no rate, and a zero somebody could count there would be a
 * measurement nobody made (ADR-0009 d.2). A count of none is a count and is
 * drawn as `0`.
 *
 * It is JavaScript with its types in JSDoc, as the modules listed in
 * `tests/ui/test_decoder.py` are, so that a bare node runs it. `tsc` checks it
 * as it checks the rest (`ui/tsconfig.json`).
 */

import { KINDS, read, reads } from "./journal.js";
import { stamped } from "./monitor.js";

/** @typedef {import("./journal.js").Line} Line */
/** @typedef {import("./journal.js").Period} Period */
/** @typedef {import("./journal.js").Incident} Incident */
/** @typedef {import("./journal.js").District} District */

/** The period a reader asks for where they ask for the whole file. */
export const ALL = "all";

/** The last day, and the last week, counted back from when the journal was
 *  read. */
export const DAY = "last day";
export const WEEK = "last 7 days";

/** The periods that are not a **build**, in the order they are offered. A
 *  build is the fourth kind and comes off the file (`choices`). */
export const SPANS = [ALL, DAY, WEEK];

/** How long the two spans are, in milliseconds. */
const DAY_MS = 86400000;
const WEEK_MS = 7 * DAY_MS;

/** What the station's own row and the station's own incidents are headed with:
 *  the link going down and the station restarting are about no district
 *  (CONTEXT.md, **station**). */
export const STATION = "station";

/** The columns of the table, in order. The kinds are the reading module's, so
 *  a kind that arrives there is a column here and not a column to add. */
export const HEADINGS = [
  "district",
  ...KINDS,
  "trips",
  "peak mA",
  "cut",
  "flips",
  "hours",
  "per hour",
];

/** What the controls say. The words are the page's and they are here rather
 *  than in the components, so that what an operator reads is run rather than
 *  read off a template (`dccex-controls.ts`). */
export const RELOADS = "reload";
export const DOWNLOADS = "download";
export const ROUTINE = "show routine lines";
export const CLEARS = "clear";

/** What a reader is told before the journal is emptied, and the two presses
 *  that answer it.
 *
 *  A clear is not undoable and the record is what nobody was watching, so the
 *  gesture says what it does and is asked a second time — the rule a flash and
 *  an Apply are on (ADR-0006 d.2, ADR-0015 d.3). It is the page's own warning:
 *  the face empties the file it is asked to empty and guards nothing
 *  (`face.py`). */
export const WARNS =
  "clearing the journal throws away every line in it, and nothing keeps a copy";
export const CONFIRMS = "yes, clear it";
export const CANCELS = "cancel";

/** What stands where the rows would be: a journal with nothing in it, and one
 *  the face did not serve.
 *
 *  Two sentences, because they are two states: a file nobody has written a
 *  line to yet is a railroad that has said nothing about power, and a face
 *  that could not be asked is a page that has not been told (ADR-0009 d.2). */
export const EMPTY = "there is nothing in the journal yet";
export const UNREADABLE = "the journal could not be read";

/** What is said where the face did not answer a clear. The face's own sentence
 *  is shown where there is one — a mirror started with no journal says so, and
 *  a page that wrote its own words over it would be guessing at an answer it
 *  was given (control ADR-0050). */
export const UNANSWERED = "the mirror did not say whether the journal was cleared";

/** What a line about the link and a line about a restart are drawn as. The
 *  station's words are drawn verbatim where it has any, and these two lines
 *  are the journal's own (ADR-0022 d.2). */
const LINK_DOWN = "link down";
const LINK_UP = "link up";
const RESTARTED = "the station restarted";

/** What the link line says when the station stopped answering. */
const DOWN = "down";

/** Milliseconds in a second and in a minute, and the seconds in a minute, for
 *  the duration a cut is drawn as. */
const SECOND_MS = 1000;
const MINUTE_MS = 60000;
const MINUTE = 60;

/** What a file's size steps up at: a thousand and a million bytes. The unit is
 *  the decimal one it is spelt as — `kB` is a thousand bytes, which is what a
 *  reader comparing it against a disk will read it as. */
const K = 1000;
const M = 1000000;

/**
 * One district's row of the table, as it is drawn.
 *
 * `cells` is one string per heading after the first, in that order, so the
 * table is a heading and a row of words rather than a component deciding which
 * number goes in which column.
 *
 * @typedef {object} Row
 * @property {string} district the letter the station named it by
 * @property {string[]} cells what is drawn in each column after it
 */

/**
 * The station's own row: the two things in the journal that are about no
 * district.
 *
 * @typedef {object} Standing
 * @property {string} district the word `station`
 * @property {string[]} says the link losses and the restarts, in words
 */

/**
 * One journal line as it is drawn under the row it belongs to.
 *
 * @typedef {object} Said
 * @property {string} at the stamp it carries, as the file has it
 * @property {string} when that stamp on the reader's own clock
 * @property {string} said the station's words, or what the line says about the
 *   link or the restart
 */

/**
 * One row of the list: an **incident**, or one line no incident took.
 *
 * A routine row carries the line's words and none of the numbers: there is
 * nothing to count about a flip nothing came of, and a blank reads as the
 * nothing it is.
 *
 * @typedef {object} Entry
 * @property {string} at the stamp the row is ordered by
 * @property {string} when that stamp on the reader's own clock
 * @property {string} district the letter, or `station` for the station's own,
 *   or empty on a line that names none
 * @property {string} kind which kind of incident, or empty on a routine line
 * @property {string} says the line's words on a routine row, and empty on an
 *   incident
 * @property {string} trips how many times the station cut the district in it
 * @property {string} milliamps the highest it printed in it
 * @property {string} cut how long the district was cut for
 * @property {boolean} routine whether it is a line no incident took
 * @property {Said[]} lines the journal lines the row is made of
 */

/**
 * What the view draws for one journal and one period.
 *
 * One function and one reading: the table and the list come off the same call
 * to `journal.js`, so a row of counts and the incidents under it cannot
 * disagree about what happened.
 *
 * @typedef {object} Shown
 * @property {Row[]} districts one per district the file names, A first
 * @property {Standing} station
 * @property {Entry[]} entries newest first
 */

/**
 * The journal, as the face served it: one JSON object per line.
 *
 * @typedef {object} Served
 * @property {Line[]} lines what the file says, in the order it was written
 * @property {number} bytes how big the file is
 */

/**
 * What became of a clear: the bytes that went, or the face's own refusal.
 *
 * @typedef {object} Cleared
 * @property {boolean} cleared whether the face said it emptied the file
 * @property {string} says what is shown about it
 */

/**
 * @param {number} value
 * @param {number} [width]
 * @returns {string}
 */
function padded(value, width = 2) {
  return String(value).padStart(width, "0");
}

/**
 * A stamp on the reader's own clock, to the day and to the millisecond.
 *
 * The day is on it because the journal is read a week later and a time alone
 * would say which minute without saying which evening. The time is the
 * **monitor**'s own `stamped()`, so a line a person is correlating with what
 * they saw reads the same on both views, and local because the person reading
 * is at the layout (`monitor.js`). The instant itself rides on the row's
 * `datetime` (`dccex-incidents.ts`), so nothing is lost to the formatting.
 *
 * @param {string} at the stamp a line carries, ISO 8601
 * @returns {string}
 */
export function when(at) {
  const stamp = new Date(Date.parse(at));
  return (
    `${stamp.getFullYear()}-${padded(stamp.getMonth() + 1)}` +
    `-${padded(stamp.getDate())} ${stamped(stamp)}`
  );
}

/**
 * A current the station printed, or nothing where it printed none.
 *
 * @param {number | null} milliamps
 * @returns {string}
 */
function current(milliamps) {
  return milliamps === null ? "" : `${milliamps} mA`;
}

/**
 * How long something lasted, in the unit a reader can hold: milliseconds under
 * a second, because a station cuts a district and retries it inside one;
 * seconds under a minute; minutes and seconds above that.
 *
 * @param {number} ms
 * @returns {string}
 */
export function lasted(ms) {
  if (ms < SECOND_MS) {
    return `${ms} ms`;
  }
  if (ms < MINUTE_MS) {
    return `${(ms / SECOND_MS).toFixed(1)} s`;
  }
  // Rounded to the second first and split afterwards, so that 119 900 ms is
  // two minutes rather than one minute and sixty seconds.
  const seconds = Math.round(ms / SECOND_MS);
  return `${Math.floor(seconds / MINUTE)} m ${padded(seconds % MINUTE)} s`;
}

/**
 * How big the journal is.
 *
 * @param {number} bytes
 * @returns {string}
 */
export function size(bytes) {
  if (bytes < K) {
    return `${bytes} byte${bytes === 1 ? "" : "s"}`;
  }
  return bytes < M
    ? `${(bytes / K).toFixed(1)} kB`
    : `${(bytes / M).toFixed(1)} MB`;
}

/**
 * How many of something, with the word for it. Both words are given, because
 * one of them is not the other with an `s` on it.
 *
 * @param {number} count
 * @param {string} one what one of them is called
 * @param {string} more what several of them are called
 * @returns {string}
 */
function many(count, one, more) {
  return `${count} ${count === 1 ? one : more}`;
}

/**
 * The journal's lines, read off what the face served.
 *
 * A line that does not parse is dropped and nothing else is: the file is
 * served while the translator appends to it, so the last line can be half
 * written (ADR-0022 d.4). A line with no stamp is dropped too — everything
 * below is of when something happened.
 *
 * @param {string} served the file's bytes as text
 * @returns {Line[]}
 */
export function parsed(served) {
  /** @type {Line[]} */
  const lines = [];
  for (const written of served.split("\n")) {
    if (written === "") {
      continue;
    }
    /** @type {unknown} */
    let line = null;
    try {
      line = JSON.parse(written);
    } catch {
      // A line the translator had not finished writing when the face read the
      // file. There is no reading to make of half a line.
      continue;
    }
    if (typeof line !== "object" || line === null || Array.isArray(line)) {
      continue;
    }
    const fields = /** @type {Record<string, unknown>} */ (line);
    if (typeof fields.at === "string") {
      lines.push(/** @type {Line} */ (line));
    }
  }
  return lines;
}

/**
 * The **build**s the journal carries, newest first.
 *
 * Newest first because the last one in the file is what the station is running
 * now, and a reader asking what happened under a build is usually asking about
 * that one. The empty build is not one of them: it is the station not
 * answering rather than something it was running (CONTEXT.md, **build**).
 *
 * @param {readonly Line[]} lines the journal, in the order it was written
 * @returns {string[]}
 */
export function builds(lines) {
  /** @type {Set<string>} */
  const found = new Set();
  for (const line of lines) {
    const build = line.build ?? "";
    if (build !== "") {
      // Deleted and added again, so the order is where each one was last
      // spoken of rather than where it was first.
      found.delete(build);
      found.add(build);
    }
  }
  return [...found].reverse();
}

/**
 * The periods on offer: the three spans, and one per build in the journal.
 *
 * @param {readonly Line[]} lines the journal, in the order it was written
 * @returns {string[]}
 */
export function choices(lines) {
  return [...SPANS, ...builds(lines)];
}

/**
 * The period a choice means, as `journal.js` reads one.
 *
 * A choice is one of `SPANS` or a build, which is what makes a chooser one
 * list rather than two controls. The two spans are counted back from `now`,
 * which is when the journal was read: the page hands its clock in, so nothing
 * here keeps one (ADR-0009 d.1).
 *
 * @param {string} choice one of `choices()`
 * @param {number} now when the journal was read, on the page's clock
 * @returns {Period}
 */
export function over(choice, now) {
  if (choice === DAY) {
    return { start: new Date(now - DAY_MS).toISOString() };
  }
  if (choice === WEEK) {
    return { start: new Date(now - WEEK_MS).toISOString() };
  }
  return choice === ALL ? {} : { build: choice };
}

/**
 * What one journal line is drawn as.
 *
 * @param {Line} line
 * @returns {Said}
 */
function drawn(line) {
  const said =
    line.said ??
    (line.restart === true
      ? RESTARTED
      : line.link === DOWN
        ? LINK_DOWN
        : line.link === undefined
          ? ""
          : LINK_UP);
  return { at: line.at, when: when(line.at), said };
}

/**
 * One incident as a row, with the lines it is made of under it.
 *
 * **Which lines those are is the reading module's and not this one's**
 * (ADR-0022 d.3). An incident names them, by their place in the journal it was
 * read out of, so the flip a short outlived is under the row it caused and the
 * flips a burst took are under the burst — which no window read off the start
 * and the end of an incident would get right, because an incident starts at
 * the line that opened it and a flip comes before that one.
 *
 * @param {Incident} incident
 * @param {readonly Line[]} lines the journal, as it was handed in
 * @returns {Entry}
 */
function row(incident, lines) {
  return {
    at: incident.start,
    when: when(incident.start),
    district: incident.district ?? STATION,
    kind: incident.kind,
    says: "",
    trips: String(incident.trips),
    milliamps: current(incident.milliamps),
    cut: lasted(incident.cut),
    routine: false,
    lines: incident.taken.map((index) => drawn(lines[index])),
  };
}

/**
 * One line no incident took, as a row of its own.
 *
 * @param {Line} line
 * @returns {Entry}
 */
function routinely(line) {
  const said = drawn(line);
  return {
    at: line.at,
    when: said.when,
    district: line.district ?? "",
    kind: "",
    says: said.said,
    trips: "",
    milliamps: "",
    cut: "",
    routine: true,
    lines: [said],
  };
}

/**
 * One district's counts as a row of words.
 *
 * @param {string} district the letter the station named it by
 * @param {District} held what it did over the period
 * @returns {Row}
 */
function counts(district, held) {
  return {
    district,
    cells: [
      ...KINDS.map((kind) => String(held.incidents[kind] ?? 0)),
      String(held.trips),
      current(held.milliamps),
      lasted(held.cut),
      String(held.flips),
      `${held.hours.toFixed(2)} h`,
      held.rate === null ? "" : held.rate.toFixed(2),
    ],
  };
}

/**
 * The journal drawn: the counts per district, the station's own row, and the
 * incidents newest first.
 *
 * **Newest first**, because the question a person opens the view with is what
 * happened last. Where a routine line and an incident carry the same stamp the
 * incident is first: it is the thing to look at.
 *
 * **The routine lines are shown only when they are asked for.** A flip nothing
 * came of, a programming track's alert on an acknowledgement and every `<p…>`
 * are the railroad working, and a list that put them beside the incidents
 * would bury the five lines somebody came to read (CONTEXT.md, **incident**).
 *
 * @param {readonly Line[]} lines the journal, in the order it was written
 * @param {Period} [period] which of them to read; all of them by default
 * @param {boolean} [routine] whether the lines no incident took are rows too
 * @returns {Shown}
 */
export function shown(lines, period = {}, routine = false) {
  const held = read(lines, period);
  /** @type {Entry[]} */
  const entries = held.incidents.map((incident) => row(incident, lines));
  if (routine) {
    const taken = new Set(held.incidents.flatMap((incident) => incident.taken));
    for (const [index, line] of lines.entries()) {
      if (!taken.has(index) && reads(line, period)) {
        entries.push(routinely(line));
      }
    }
  }
  return {
    districts: Object.entries(held.districts).map(([district, counted]) =>
      counts(district, counted),
    ),
    station: {
      district: STATION,
      says: [
        many(held.station.links, "link loss", "link losses"),
        many(held.station.restarts, "restart", "restarts"),
      ],
    },
    entries: entries.sort((first, second) => {
      const apart = Date.parse(second.at) - Date.parse(first.at);
      return apart === 0
        ? Number(first.routine) - Number(second.routine)
        : apart;
    }),
  };
}

/**
 * What the face said about a clear, as it is shown.
 *
 * @param {number} bytes how many bytes it said went
 * @returns {string}
 */
export function emptied(bytes) {
  return `the journal is empty: ${size(bytes)} cleared`;
}
