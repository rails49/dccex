/**
 * The monitor's rules that are not drawing: whether the reader is at the
 * bottom of the conversation, the time a line arrived as a clock says it,
 * which of the station's repeats are worth showing, and the conversation
 * itself — what is on screen, what waits behind a pause, and what a pause, a
 * resume and a clear do to either.
 *
 * The page is `ui/src/ui/dccex-monitor.ts`, and everything about it that
 * needs a browser stays there — the rows, the box at the foot, the controls,
 * the rectangles a held row is measured with, and the view being put back.
 * What is here is what that component and the page around it work out from
 * numbers, a `Date` and a list, which is what lets every one of them be run
 * with the pairs that matter on a machine with no browser in it
 * (`tests/ui/test_monitor.py`).
 *
 * **The conversation is one value and three functions** (#144). What a line
 * arriving, a pause, a resume and a clear do to what is on screen was written
 * as private methods of the page, where the only thing that could be held to
 * it was a reader of `dccex-app.ts` — and two of the rules it was holding
 * were wrong in ways a reader walked past twice (#142, #143). They are here
 * now, as a value in and a value out, so that the pairs that matter go
 * through them under a bare node.
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
 * It is here because the trim is here: what the conversation holds and what
 * goes off the front of it are the one rule, and the number was on the page
 * while the queue below called itself a quarter of it — a quarter nothing
 * computed and nothing held (#152).
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
 * The queue after `said` arrived behind a pause, and what went to make room.
 *
 * Past the cap the oldest *queued* lines go, and every one of them is counted
 * — for the whole of the pause and not for the last arrival, so what the
 * monitor says is how much of the conversation went rather than how much went
 * in the last read. Nothing on screen is touched: the lines a reader is
 * looking at are what the pause is holding still.
 *
 * What went is handed back as well as counted, because the caller has
 * something to forget about it: a status line that never reached the
 * conversation must not go on standing for what its subject last said
 * (`arrived`, #142).
 *
 * @template T
 * @param {Behind<T>} behind what was waiting
 * @param {readonly T[]} said what has just arrived, in the order it did
 * @returns {{ behind: Behind<T>, went: readonly T[] }}
 */
export function queued(behind, said) {
  const lines = [...behind.lines, ...said];
  const over = lines.length - QUEUE;
  return over <= 0
    ? { behind: { lines, dropped: behind.dropped }, went: [] }
    : {
        behind: {
          lines: lines.slice(over),
          dropped: behind.dropped + over,
        },
        went: lines.slice(0, over),
      };
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

/**
 * A line of the conversation as the page keeps it: what was said, when it
 * arrived, which end of the conversation it is, and the key it was kept
 * under.
 *
 * It is `Said` (`framing.js`) with a key on it, written out here rather than
 * borrowed: a module a bare node runs imports nothing, so what a line is is
 * described the way `Scroller` above describes an element's three numbers.
 *
 * The key is assigned once, is never reused and is never wound back. The
 * monitor draws a row per key, and a key made of what a line says or of when
 * it arrived would draw two identical lines in one millisecond as one row
 * (#74).
 *
 * @typedef {{
 *   readonly line: string,
 *   readonly at: Date,
 *   readonly sent: boolean,
 *   readonly key: number,
 * }} Line
 */

/**
 * The page's own note in the conversation, keyed as a line is.
 *
 * Not something the station said and not something this page sent: the page
 * telling the reader what became of the conversation itself. So far there is
 * one — the lines that went while the view was held (`held`, #143).
 *
 * It carries no time, because it is not an arrival: what a stamp beside it
 * would say is when a gap was noticed rather than when anything happened. It
 * is trimmed and cleared like any other entry, because it is part of what is
 * on screen.
 *
 * @typedef {{
 *   readonly note: string,
 *   readonly key: number,
 * }} Note
 */

/**
 * One entry of the conversation: a line, or the page's own note about it.
 *
 * @typedef {Line | Note} Shown
 */

/**
 * The conversation as the page keeps it.
 *
 * Everything an arriving line, a pause, a resume and a clear touch, in one
 * value: what is on screen, what is waiting out of sight behind a pause,
 * whether the view is held, what each subject last said, and what the next
 * entry kept is keyed by. The three functions below are the only things that
 * change it and each is a value in and a value out — no import, no clock and
 * no DOM — so what the page does to a conversation is asserted by putting
 * conversations through it (`tests/ui/test_monitor.py`).
 *
 * @typedef {object} Conversation
 * @property {readonly Shown[]} said what is on screen, oldest first
 * @property {Behind<Line>} behind what is waiting behind a pause
 * @property {boolean} paused whether the view is held
 * @property {Readonly<Record<string, string>>} last what each subject last
 *   said, so that a poll answered the same way twice is shown once
 * @property {number} keys what the next entry kept is keyed by
 */

/**
 * A conversation nothing has been said in: what a page opens with.
 *
 * @type {Conversation}
 */
export const OPENED = {
  said: [],
  behind: EMPTIED,
  paused: false,
  last: {},
  keys: 0,
};

/**
 * `said` with the oldest past capacity dropped.
 *
 * The one place the trim is, so what a reader resumes into is trimmed exactly
 * as a line that arrived is and there is one answer to how much of the
 * conversation the page shows.
 *
 * @param {readonly Shown[]} said
 * @returns {readonly Shown[]}
 */
function trimmed(said) {
  return said.length > KEPT ? said.slice(said.length - KEPT) : said;
}

/**
 * What the page's note says where a pause dropped lines.
 *
 * A count and the reason, in the page's own words, so that the twelve lines
 * that went are a gap a reader can see rather than a conversation that reads
 * as though the station was quiet (ADR-0009 d.2). Singular where one went: it
 * is a sentence a person reads, and `1 lines` is the page not reading what it
 * wrote.
 *
 * @param {number} dropped how many went while the view was held
 * @returns {string}
 */
function gap(dropped) {
  return `${dropped} line${dropped === 1 ? "" : "s"} dropped while paused`;
}

/**
 * `last` with the subjects of `went` forgotten.
 *
 * A status line the queue dropped never reached the conversation, so the page
 * must not go on treating the next line that says the same thing as a repeat.
 * Paused, a `<p1>` pushed off the front of a full queue would otherwise leave
 * every later answer about the power suppressed as nothing new, and the
 * conversation would never say the power came on (#142).
 *
 * Only a subject whose last word is the line that went is forgotten: a later
 * line about the same subject is still in the queue, and it is still what was
 * last said about it.
 *
 * @param {Readonly<Record<string, string>>} last what each subject last said
 * @param {readonly Line[]} went the lines the queue dropped
 * @returns {Record<string, string>}
 */
function forgotten(last, went) {
  const now = { ...last };
  for (const line of went) {
    const about = line.sent ? null : subject(line.line);
    if (about !== null && now[about] === line.line) {
      delete now[about];
    }
  }
  return now;
}

/**
 * The conversation after `said` arrived.
 *
 * **A status line is kept only when it changed.** Every poll is answered with
 * the same banner and power lines, and a monitor full of them hides what is
 * new (`quieted`). What the readings hear is the page's business and is not
 * touched here: every line reaches them, shown or not, paused or not
 * (`dccex-app.ts`).
 *
 * **A paused conversation queues what is worth showing and appends nothing.**
 * The trim never runs, which is the whole of what a pause promises a reader:
 * the line they are reading is not taken off the front while they read it. A
 * line this page sent queues with the rest — the view is one thing, and
 * letting the operator's own line through would be the append a pause exists
 * to stop.
 *
 * @param {Conversation} conversation the conversation as it stands
 * @param {readonly { line: string, at: Date, sent: boolean }[]} said what
 *   arrived or went, in the order it did
 * @returns {Conversation}
 */
export function arrived(conversation, said) {
  const { shown, last } = quieted(conversation.last, said);
  let keys = conversation.keys;
  const worth = said
    .filter((_line, i) => shown[i])
    .map((line) => ({ ...line, key: keys++ }));
  if (!conversation.paused) {
    return {
      ...conversation,
      said: trimmed([...conversation.said, ...worth]),
      last,
      keys,
    };
  }
  const { behind, went } = queued(conversation.behind, worth);
  return { ...conversation, behind, last: forgotten(last, went), keys };
}

/**
 * The conversation held still, or let go.
 *
 * One transition and not two, as the control that runs it is one control:
 * what a press does is whatever the view is not doing now.
 *
 * Held, nothing else changes. What arrives goes to the queue from here, and
 * the lines on screen stay where the reader left them.
 *
 * Let go, what waited is appended in the order it arrived and through the one
 * trim there is. Where the queue dropped lines, one note goes in ahead of
 * them, saying how many: the gap is exactly there, and the count the monitor
 * was carrying goes away with the pause that made it — so a resume that said
 * nothing would leave a reader with a silent twelve-line hole in the
 * conversation (#143, ADR-0009 d.2). A resume that dropped nothing adds no
 * note.
 *
 * @param {Conversation} conversation the conversation as it stands
 * @returns {Conversation}
 */
export function held(conversation) {
  if (!conversation.paused) {
    return { ...conversation, paused: true };
  }
  const { lines, dropped } = conversation.behind;
  let keys = conversation.keys;
  /** @type {readonly Shown[]} */
  const noted = dropped === 0 ? [] : [{ note: gap(dropped), key: keys++ }];
  return {
    ...conversation,
    said: trimmed([...conversation.said, ...noted, ...lines]),
    behind: EMPTIED,
    paused: false,
    keys,
  };
}

/**
 * The conversation emptied, and any queue behind it.
 *
 * And nothing else. What each subject last said is kept, so a poll answered
 * the same way after a clear is still not news, and the keys go on where they
 * were: a key is assigned once and never reused, and winding the counter back
 * would draw the next line on a row a cleared one had. Whether the view is
 * held is the reader's and is not theirs to have taken from them by emptying
 * what is in front of them.
 *
 * @param {Conversation} conversation the conversation as it stands
 * @returns {Conversation}
 */
export function cleared(conversation) {
  return { ...conversation, said: [], behind: EMPTIED };
}
