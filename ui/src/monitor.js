/**
 * The monitor's rules that are not drawing: whether the reader is at the
 * bottom of the conversation, the time a line arrived as a clock says it,
 * which of the station's repeats are worth showing, and what waits behind a
 * pause.
 *
 * The page is `ui/src/ui/dccex-monitor.ts`, and everything about it that
 * needs a browser stays there — the rows, the box at the foot, the controls,
 * the rectangles a held row is measured with, and the view being put back.
 * What is here is what that component and the page around it work out from
 * numbers, a `Date` and a list, which is what lets every one of them be run
 * with the pairs that matter on a machine with no browser in it
 * (`tests/ui/test_monitor.py`).
 *
 * None of them is a reading of the railroad. What the **band** and the
 * **tile**s show is `readings.js`'s and what a line means is the
 * **decoder**'s; these are about a person reading a page — where they are in
 * it, the clock beside what they are reading, and what the page is holding
 * back while they read (#125).
 *
 * It is JavaScript with its types in JSDoc, as `decoder.js`, `message.js`,
 * `readings.js`, `releases.js`, `flash.js` and `framing.js` are: the modules
 * the gate runs rather than reads, listed in `tests/ui/test_decoder.py`. They
 * were read for as long as there was no node to run them with, and a stamp an
 * hour out leaves a source saying every right word (#78, #101). `tsc` checks
 * this file as strictly as it checks the rest (`ui/tsconfig.json`).
 */

/** How close to the bottom still counts as being at it, in CSS pixels. A
 *  scroller that is one rounded sub-pixel from the end is a reader who has not
 *  scrolled up. */
const SLACK_PX = 4;

/**
 * As much of a scroller as being at the bottom of it is a question about: how
 * tall what is in it is, how far down it has been scrolled, and how much of it
 * a reader can see.
 *
 * An `Element` is one, and so is a plain object with the three numbers —
 * which is what lets the rule below be run under a bare node. Nothing here
 * touches a browser value; it reads three numbers off one.
 *
 * @typedef {{
 *   readonly scrollHeight: number,
 *   readonly scrollTop: number,
 *   readonly clientHeight: number,
 * }} Scroller
 */

/**
 * Whether the reader is at the bottom of `scroller`.
 *
 * A scroller with less in it than it can show is at its own bottom: there is
 * nowhere to have scrolled up to, and a reader looking at three lines is
 * following the tail.
 *
 * @param {Scroller} scroller what the conversation is drawn in
 * @returns {boolean}
 */
export function atBottom(scroller) {
  return (
    scroller.scrollHeight - scroller.scrollTop - scroller.clientHeight <=
    SLACK_PX
  );
}

/**
 * @param {number} value
 * @param {number} [width]
 * @returns {string}
 */
function padded(value, width = 2) {
  return String(value).padStart(width, "0");
}

/**
 * The time a line arrived, as the operator's own clock says it.
 *
 * Local time, because the person reading is at the layout correlating what
 * they saw with what the station said, and to the millisecond, because a burst
 * of `<…>` messages arrives inside one second. The instant itself rides on
 * the element's `datetime` (`dccex-monitor.ts`), so nothing about when a line
 * arrived is lost to the formatting.
 *
 * @param {Date} at when the line arrived, on the page's clock
 * @returns {string}
 */
export function stamped(at) {
  return (
    `${padded(at.getHours())}:${padded(at.getMinutes())}` +
    `:${padded(at.getSeconds())}.${padded(at.getMilliseconds(), 3)}`
  );
}

/** The subjects the monitor never shows: see `subject`. */
const MEASURED = new Set(["jI", "jG"]);

/**
 * What a status line is about, or `null` for a line that is not one.
 *
 * The station answers every poll with the same handful of lines: its banner,
 * the power on each track, the power as a whole and the display. Another
 * client asking `<#>` every thirty seconds gets `<# 120>`, how many locos the
 * station can hold, and every client sees that too. A line whose
 * subject last said the same thing tells a reader nothing new, so the monitor
 * shows one of these only when it changed. Every other line is always shown.
 *
 * The measured currents (`<jI …>`) and limits (`<jG …>`) are never shown: the
 * current moves on nearly every poll, and the tiles are where it is read.
 *
 * @param {string} line a whole `<…>` message
 * @returns {string | null}
 */
export function subject(line) {
  const said =
    /^<(?:p[01]( [A-Z]+)?|(i)DCC-EX\b.*|(@ \d+ \d+) .*|(j[A-Z]) .*|(= [A-Z]) .*|(#) \d+)>$/.exec(
      line,
    );
  if (said === null) {
    return null;
  }
  const [, track, banner, display, currents, mode, slots] = said;
  return (
    banner ?? display ?? currents ?? mode ?? slots ?? `p${track ?? ""}`
  );
}

/**
 * Which lines are worth showing, and what each subject last said.
 *
 * A line this page sent is always shown and is not the station saying
 * anything, so it neither shows nor hides what the station says next.
 *
 * @param {Readonly<Record<string, string>>} last what each subject last said
 * @param {readonly { line: string, sent: boolean }[]} said what arrived or
 *   went, in order
 * @returns {{ shown: boolean[], last: Record<string, string> }}
 */
export function quieted(last, said) {
  const now = { ...last };
  const shown = said.map(({ line, sent }) => {
    const about = sent ? null : subject(line);
    if (about === null) {
      return true;
    }
    const changed = !MEASURED.has(about) && now[about] !== line;
    now[about] = line;
    return changed;
  });
  return { shown, last: now };
}

/**
 * What is behind a pause: the lines that arrived while the monitor was
 * holding, and how many were dropped off the front to make room for them.
 *
 * The lines are whatever the page keeps a conversation as — this module counts
 * them and never reads one, so what a line is stays the page's business and
 * the queue is a queue of anything.
 *
 * @template T
 * @typedef {object} Behind
 * @property {readonly T[]} lines what is waiting, oldest first
 * @property {number} dropped how many went off the front because the queue was
 *   full
 */

/**
 * A queue with nothing in it and nothing dropped.
 *
 * What a monitor that is not paused holds, and what resuming and clearing
 * leave behind. The lines it holds are of no type at all, which is what lets
 * every queue start here whatever the page keeps a conversation as.
 *
 * @type {Behind<never>}
 */
export const EMPTIED = { lines: [], dropped: 0 };

/**
 * How many lines the page keeps.
 *
 * A page left open on a busy railroad is handed every byte of an evening, and
 * a monitor is what the station is saying now: the oldest lines are dropped
 * rather than held until the browser cannot draw the page. Nothing was lost by
 * the mirror doing it — it keeps no history either (ADR-0010) — and this is
 * the page saying how much of the conversation it can show, which is its own
 * business.
 *
 * It is here rather than on the page because the queue below is a quarter of
 * it: the number was `dccex-app.ts`'s and the quarter was written out beside
 * this sentence, so the two could part with every word of both still reading
 * true (#152).
 */
export const KEPT = 2000;

/**
 * How many lines wait behind a pause before the oldest of them go.
 *
 * A quarter of what the page keeps, because the queue is appended to the
 * conversation when the reader resumes and the usual capacity trim applies
 * from there: a queue as long as the conversation would mean resuming
 * replaced the whole of what the pause was holding still, which is the one
 * thing a pause is for. At a quarter, a reader who resumes from a full queue
 * still has three quarters of what they paused on above it.
 *
 * It is the quarter as arithmetic rather than as prose. What a pause promises
 * is that nothing on screen is trimmed; what it cannot promise is that a
 * station talking for an hour is all still there behind it.
 */
export const QUEUE = KEPT / 4;

/**
 * The queue after `said` arrived behind a pause.
 *
 * Past the cap the oldest *queued* lines go, and every one of them is counted
 * — for the whole of the pause and not for the last arrival, so what the
 * monitor says is how much of the conversation went rather than how much went
 * in the last read. Nothing on screen is touched: the lines a reader is
 * looking at are what the pause is holding still.
 *
 * @template T
 * @param {Behind<T>} behind what was waiting
 * @param {readonly T[]} said what has just arrived, in the order it did
 * @returns {Behind<T>}
 */
export function queued(behind, said) {
  const lines = [...behind.lines, ...said];
  const over = lines.length - QUEUE;
  return over <= 0
    ? { lines, dropped: behind.dropped }
    : { lines: lines.slice(over), dropped: behind.dropped + over };
}

/**
 * What the monitor says about `behind`, or `null` where it says nothing.
 *
 * A count rather than the lines, because the lines are what the pause is
 * keeping out of sight. What was dropped is said beside it and is never left
 * out: a queue that quietly forgot the oldest of what it was holding would
 * have the page pretending the station was quiet, which is the observation
 * nobody made (ADR-0009 d.2).
 *
 * Nothing waiting and nothing dropped reads as nothing at all, so a monitor
 * nobody has paused does not carry a `0 waiting` for the whole of an evening.
 *
 * @param {Behind<unknown>} behind what is waiting
 * @returns {string | null}
 */
export function waiting(behind) {
  if (behind.lines.length === 0 && behind.dropped === 0) {
    return null;
  }
  const said = `${behind.lines.length} waiting`;
  return behind.dropped === 0 ? said : `${said}, ${behind.dropped} dropped`;
}
