/**
 * The flash sequence: what the page does to the railroad before a **release**
 * is written onto the **station**, and the order it does it in.
 *
 * Choosing a release resets the board. The rails go dead, every throttle loses
 * the station, anything moving keeps moving until friction stops it, and it
 * takes a minute or two. **Nothing behind the page guards that** — the mirror
 * checks the **tag**, the release, the digest, the device and whether it is
 * already writing, and it checks nothing about a railroad, because on a box
 * with a command station and no layout there is no dispatcher to ask
 * (ADR-0006, `firmware.py`). So the care is here: the page says plainly what
 * is about to happen, stops the locomotives, cuts track power, and only then
 * asks the face to write.
 *
 * **The order is the whole of it.** The stop goes first because a locomotive
 * coasting on dead rails is what is left if power is cut under it, and the
 * write goes last because it is the step that takes the station away. A step
 * that did not leave the page stops the sequence where it is: a page that
 * asked for a write after failing to stop anything would have done the one
 * dangerous half of this. What it says names the step that did not go and is
 * right about the one before it: a cut that did not go leaves the locomotives
 * stopped and the rails hot, which is the state of the railroad the operator
 * is the only guard on.
 *
 * **What it is doing is said while it does it**, because the last step is a
 * minute or two of nothing at all and a page with nothing on it reads as a
 * hang.
 *
 * **And how far the writing itself has got is asked for.** The mirror reads
 * esptool's output as it runs and answers the stage and the percentage on a
 * route of its own, so the page asks twice a second while a flash is in flight
 * and draws a bar over what it is told (ADR-0012, `face.py`). What that answer
 * means — the stages, and the one stage anything counts — is at the foot of this
 * module, beside the words: it is the same flash and the same person reading
 * about it, and the asking is `face.ts`'s as the rest of the asking is.
 *
 * **Success is not replied to; it is observed.** What comes back from the face
 * says the write was asked for and finished, and what is on the station is
 * read off the station — the stream drops, comes back, and the banner says
 * which **build** it is running (ADR-0006 d.3, ADR-0008 d.3). So the answer to
 * the POST is not the end of the flash: the page waits for the station, and a
 * build that is not the tag is a flash that did not land whatever the mirror
 * answered (ADR-0012 d.4). That reading is `became()` at the foot of this
 * module.
 *
 * It reaches nothing itself. What sends a message up the **stream**, what asks
 * the face to write and what shows a step are handed in, so the whole
 * sequence — what goes down the cable, in what order, and what is said at each
 * step — is run on a machine with no command station, no browser and no
 * network in reach (`tests/ui/test_flash.py`). It is one of the modules of the
 * page written as JavaScript with its types in JSDoc — they are named in
 * `tests/ui/test_decoder.py`'s docstring, which is where they are counted so
 * that a header need not (#110) — for the reason the rest are: the gate is
 * Python with a bare node in it, and a rule about what goes down a cable to a
 * command station asserted against the source that would produce it is not
 * asserted. `tsc` checks it as it checks the rest (`ui/tsconfig.json`).
 */

/** What stops the locomotives: the emergency stop, which halts everything
 *  moving and leaves the rails hot. It is the first step because a locomotive
 *  that was coasting when the power went is a locomotive nobody stopped. */
export const STOPS = "<!>";

/** What cuts track power. It is a step of this sequence rather than a control
 *  of its own: the one control that commands power is the **band**'s button,
 *  which sends this same message where any track is on (ADR-0011 d.1), and
 *  what a flash cuts is cut because a release is about to be written. */
export const CUTS = "<0>";

/** What an operator is told before they are asked, and the whole reason the
 *  sequence exists: the guard is the person, and a person can only be one if
 *  they are told what the gesture does (ADR-0006 d.2). */
export const WARNS =
  "flashing resets the station and drops every throttle:" +
  " the rails go dead, anything moving keeps moving until friction stops it," +
  " and it takes a minute or two";

/** What the control on a release says. */
export const CHOOSES = "flash";

/** What says yes to the warning. It names the gesture rather than agreeing
 *  with a question, so a press is a thing somebody meant. */
export const CONFIRMS = "write it";

/** What declines it. A sequence the operator declines is a flash that was not
 *  asked for rather than one that was refused (ADR-0006 d.2). */
export const CANCELS = "cancel";

/** The first step, said while it runs. */
export const STOPPING = "stopping the locomotives";

/** The second. */
export const CUTTING = "cutting track power";

/** What is said where the stop did not leave the page. The stream is the only
 *  way anything reaches the station from here, so a stop that did not go is a
 *  railroad nobody stopped — nothing was done to it, and nothing is written
 *  after one (ADR-0009 d.2). */
export const UNSTOPPED =
  "the station's conversation is not open, so the locomotives were not" +
  " stopped and nothing was written";

/** What is said where the stop went and the cut did not. The sentence above
 *  is the wrong half of the truth here and the dangerous half: the locomotives
 *  are stopped and the rails are still hot, and what the page says about the
 *  state of the railroad is the whole of what the guard has to go on
 *  (ADR-0006 d.2). */
export const UNCUT =
  "the station's conversation is not open, so track power was not cut: the" +
  " locomotives are stopped, the power is still on, and nothing was written";

/** What is said where the face could not be asked at all, or answered with
 *  something this page cannot read. Nothing said is not nothing done: the
 *  sentence says the mirror was not reached rather than that the station was
 *  not written, because a page that could not read an answer did not get
 *  one. */
export const UNANSWERED =
  "the mirror could not be asked to write it, so what is on the station now" +
  " is what its banner says";

/** What is said where the write finished and the station has not said what it
 *  is running yet. The write being over is not the flash having landed: what is
 *  on the station is the station's to say, on the banner it sends when it comes
 *  back up, and until then the true sentence is that the page is waiting for it
 *  (ADR-0006 d.3, ADR-0012 d.4). */
export const WAITING = "waiting for the station";

/**
 * The third step, said while it runs.
 *
 * It names the tag and says how long it takes, because this is the step that
 * is a minute or two of silence: the station is away for the whole of it, the
 * stream drops with it, and a page that said only "writing" would be
 * indistinguishable from a page that had stopped.
 *
 * @param {string} tag the release being written
 * @returns {string}
 */
export function writing(tag) {
  return `writing ${tag} onto the station — a minute or two, and the station is away for it`;
}

/**
 * What became of a flash: whether it was written, and the sentence that says
 * which.
 *
 * One sentence, because what is on the other end is a person — the same shape
 * the mirror answers a gesture with, for the same reason (`firmware.py`,
 * control ADR-0050).
 *
 * @typedef {object} Wrote
 * @property {boolean} flashed whether the release was written
 * @property {string} says what happened, in words a person reads
 */

/**
 * What the page hands the sequence to do it with.
 *
 * Three things and no more: this module reaches no socket, no face and no DOM
 * of its own, which is what lets the ordering be asserted with none of them in
 * reach.
 *
 * @typedef {object} Hands
 * @property {(typed: string) => string | null} sends what puts one whole
 *   message up the stream, answering what went or `null` where nothing did
 * @property {(tag: string) => Promise<Wrote>} writes what asks the face to
 *   write a named release onto the station
 * @property {(step: string) => void} shows what says which step is running
 */

/**
 * One flash, from the release chosen to the station written.
 *
 * The operator has already been warned and has already said yes: this is what
 * happens after that, and the warning is `WARNS` above, drawn where the choice
 * is made.
 *
 * @param {string} tag the release to write
 * @param {Hands} hands what to do it with
 * @returns {Promise<Wrote>} what became of it
 */
export async function sequence(tag, hands) {
  for (const [step, typed, unsent] of [
    [STOPPING, STOPS, UNSTOPPED],
    [CUTTING, CUTS, UNCUT],
  ]) {
    hands.shows(step);
    if (hands.sends(typed) === null) {
      return { flashed: false, says: unsent };
    }
  }
  hands.shows(writing(tag));
  return await hands.writes(tag);
}

/* -- how far it has got ---------------------------------------------------- */

/**
 * The stages a flash goes through, in the order it goes through them, as the
 * **face** names them (ADR-0012 d.2, `firmware.py`'s `Stage`).
 *
 * The words are the mirror's and are drawn as they arrive. The list is here so
 * that what the page shows can be asserted against the four the app sends, and
 * not so that the page can look a stage up: a stage this list does not carry is
 * still a flash that is running, and it is drawn under the word the face said
 * (ADR-0009 d.2, d.5).
 */
export const STAGES = ["fetching", "checking", "writing", "verifying"];

/** The one stage anything counts. esptool counts the blocks it sends; nothing
 *  counts a fetch, a hash or a verify, so this is the one stage a percentage
 *  arrives for and the one the bar fills for (ADR-0012 d.2). */
const COUNTED = "writing";

/**
 * How far the flash in flight has got, as the face answers it.
 *
 * @typedef {object} Flashing
 * @property {string} tag the release being written
 * @property {string} stage the part of the flash that is under way, in the
 *   face's own words — one of `STAGES`
 * @property {number | null} percent how far the writing has got, and `null`
 *   outside it and wherever the face put no number the page can read
 */

/** The three fields a flash in flight carries, as the face names them
 *  (`face.py`'s `progress()`). The tag is under the same word a flash is asked
 *  for by, because it is the same thing being named. */
const TAG = "tag";
const STAGE = "stage";
const PERCENT = "percent";

/** How full a bar may be drawn. A number outside it is not a percentage. */
const FULL = 100;

/**
 * The flash in flight in `answer`, or `null` where none is running.
 *
 * **Nothing running and nothing said read alike here**, which is the one place
 * this page draws that line the short way: what the page does with either is
 * draw no bar, and it has the face's own answer to the POST for whether a write
 * is under way of its own (`face.ts`). A sentence about a flash nobody can see
 * would be a page reporting a station it is not watching (ADR-0009 d.2).
 *
 * Read one field at a time, as the releases are (`releases.js`'s `carried()`):
 * this arrives from another app over a wire, and a reader that reached into it
 * would be taken down by whatever that app answered the day it answered
 * something else. An answer that names no tag or no stage is not a flash this
 * page can say anything about; a percentage that is not a number between none
 * and full is no count, and the stage still stands.
 *
 * @param {unknown} answer what the face answered under `flashing`
 * @returns {Flashing | null}
 */
export function progress(answer) {
  if (typeof answer !== "object" || answer === null || Array.isArray(answer)) {
    return null;
  }
  const fields = /** @type {Record<string, unknown>} */ (answer);
  const tag = fields[TAG];
  const stage = fields[STAGE];
  if (typeof tag !== "string" || tag === "") {
    return null;
  }
  if (typeof stage !== "string" || stage === "") {
    return null;
  }
  const percent = fields[PERCENT];
  return {
    tag,
    stage,
    percent:
      typeof percent === "number" &&
      Number.isFinite(percent) &&
      percent >= 0 &&
      percent <= FULL
        ? percent
        : null,
  };
}

/**
 * One bar: what it reads, and how full it is.
 *
 * The word is the issue's and is not the **band** — this is the bar a flash
 * fills on the releases view (issue 172).
 *
 * @typedef {object} Bar
 * @property {string} says the stage, with the percentage beside it where there
 *   is one
 * @property {number | null} percent how full, out of a hundred, and `null`
 *   where there is nothing to count — a bar that is running and not counting
 */

/**
 * The bar over the flash in flight, or `null` where none is running.
 *
 * **The writing is the one stage that counts.** esptool prints how far it has
 * got as it sends blocks and nothing prints anything for a fetch, a hash or a
 * verify, so those stages are a bar that runs without a number: a bar drawn at
 * a percentage nobody measured is a reading nobody took (ADR-0009 d.2,
 * ADR-0012 d.2).
 *
 * @param {Flashing | null} flashing how far the flash has got
 * @returns {Bar | null}
 */
export function bar(flashing) {
  if (flashing === null) {
    return null;
  }
  const counted = flashing.stage === COUNTED ? flashing.percent : null;
  return {
    says:
      counted === null
        ? flashing.stage
        : `${flashing.stage} ${Math.round(counted)} %`,
    percent: counted,
  };
}

/* -- what became of it ----------------------------------------------------- */

/**
 * What is said where the station came back running the release that was
 * written.
 *
 * @param {string} tag the release that was written
 * @returns {string}
 */
export function running(tag) {
  return `the station came back running ${tag}`;
}

/**
 * What is said where it came back running something else.
 *
 * Both are named. Which build came back is what whoever looks into it has to go
 * on, and a sentence that said only that the flash failed would leave an
 * operator reading the list to work out what is on the board (ADR-0012 d.4).
 *
 * @param {string} tag the release that was written
 * @param {string} build what the station says it is running
 * @returns {string}
 */
export function instead(tag, build) {
  return `the station came back running ${build} and not ${tag}`;
}

/**
 * What became of a flash once the station has been looked at: whether the
 * release that was written is the **build** the station reports, and the
 * sentence that says so.
 *
 * `landed` is `null` while the station has not said. It is not a failure and
 * not a success: the minute a write takes is a minute of the station being
 * away, and either answer drawn there would be one nobody had made (ADR-0009
 * d.2).
 *
 * @typedef {object} Became
 * @property {boolean | null} landed whether the station is running what was
 *   written, and `null` while it has not said
 * @property {string} says what became of it, in words a person reads
 */

/**
 * What became of the last flash, read against what the station says it is
 * running.
 *
 * **Three answers and the station gives the last two** (ADR-0012 d.4). A
 * refusal is what the face or the sequence said and is what the operator reads,
 * whatever the station is running: nothing was written, so the build on the
 * board is not about this gesture. A write that finished is waited on until the
 * station says which build it is running — the link goes down with the write and
 * the build goes with the link (ADR-0008 d.3) — and then the build either is the
 * tag or is not, which is the whole of what says a flash landed (ADR-0006 d.3).
 *
 * @param {Wrote | null} wrote what the sequence came back with, or `null` where
 *   no flash has been asked for
 * @param {string | null} tag the release it was asked to write
 * @param {string | null} build what the station says it is running, and `null`
 *   while it is not answering
 * @returns {Became | null} what became of it, or `null` where there is nothing
 *   to say
 */
export function became(wrote, tag, build) {
  if (wrote === null || tag === null) {
    return null;
  }
  if (!wrote.flashed) {
    return { landed: false, says: wrote.says };
  }
  if (build === null) {
    return { landed: null, says: WAITING };
  }
  return build === tag
    ? { landed: true, says: running(tag) }
    : { landed: false, says: instead(tag, build) };
}
