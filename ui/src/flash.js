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
 * **Success is not replied to; it is observed.** What comes back from the face
 * says the write was asked for and finished, and what is on the station is
 * read off the station — the stream drops, comes back, and the banner says
 * which **build** it is running (ADR-0006 d.3, ADR-0008 d.3).
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

/** What cuts track power. The one thing on this page that commands it — the
 *  **band** presses nothing, because this page is on no bus for anything to
 *  check first (ADR-0008 d.5) — and it is a step of this sequence rather than
 *  a control of its own. */
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

/** What is said where the write finished. What is on the station is not this
 *  sentence's to say: the station says it, on the banner it sends when it
 *  comes back up (ADR-0006 d.3). */
export const WROTE =
  "written — the station is coming back, and the build it reports is what is" +
  " on it";

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
 * ADR-0050).
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
