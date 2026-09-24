/**
 * The monitor's two rules that are not drawing: whether the reader is at the
 * bottom of the conversation, and the time a line arrived as a clock says it.
 *
 * The page is `ui/src/ui/dccex-monitor.ts`, and everything about it that
 * needs a browser stays there — the rows, the box at the foot, the rectangles
 * a held row is measured with, and the view being put back. What is here is
 * what that component works out from numbers and a `Date`, which is what lets
 * both be run with the pairs that matter on a machine with no browser in it
 * (`tests/ui/test_monitor.py`).
 *
 * Neither is a reading of the railroad. What the **band** and the **tile**s
 * show is `readings.js`'s and what a line means is the **decoder**'s; these two
 * are about a person reading a page — where they are in it, and the clock
 * beside what they are reading.
 *
 * It is JavaScript with its types in JSDoc, as `decoder.js`, `message.js`,
 * `readings.js`, `releases.js`, `flash.js` and `framing.js` are: the seven the
 * gate runs rather than reads. These two were read for as long as there was no
 * node to run them with, and a stamp an hour out leaves a source saying every
 * right word (#78, #101). `tsc` checks this file as strictly as it checks the
 * rest (`ui/tsconfig.json`).
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
