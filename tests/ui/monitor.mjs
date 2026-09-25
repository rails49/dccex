// What the monitor works out without drawing, run.
//
// `tests/ui/test_monitor.py` holds the pairs and this is what puts them
// through the real rules: a JSON array of asks on stdin, a JSON array of
// answers on stdout, in the order they came.
//
// An ask is one of the two. A scroller, as the three numbers being at the
// bottom of one is a question about:
//
//     {"scroller": {"scrollHeight": 1000, "scrollTop": 800, "clientHeight": 200}}
//
// or a time to stamp, either as the reading a clock in the operator's own zone
// would give — the hour, the minute, the second and the millisecond, which is
// what the stamp is made of and carries no zone with it —
//
//     {"clock": [13, 4, 5, 7]}
//
// or as an instant, in milliseconds since the epoch, which is what says the
// zone is the machine's and not UTC:
//
//     {"at": 1767272645007}
//
// or lines to quiet, each with whether this page sent it, and what each
// subject last said before they arrived:
//
//     {"quiet": {"last": {"p A": "<p1 A>"}, "said": [["<p1 A>", false]]}}
//
// or lines arriving behind a pause, with what was already waiting — answered
// with the queue and what went off the front of it to make room:
//
//     {"queue": {"behind": {"lines": [], "dropped": 0}, "said": ["<p1 A>"]}}
//
// or the module's own three: how many lines the page keeps, how many the queue
// holds, and the queue with nothing in it and nothing dropped, which is what a
// monitor that is not paused holds:
//
//     {"own": true}
//
// or what the monitor says about a queue:
//
//     {"waiting": {"lines": ["<p1 A>"], "dropped": 0}}
//
// or a conversation, kept: a run of what happens to one, from the conversation
// a page opens with, answered with the conversation the run left. A step is
// lines arriving, each with whether this page sent it, or a press of the
// pause, or a press of the clear:
//
//     {"keeping": [{"said": [["<p1 A>", false]]}, {"held": true},
//                  {"said": [["<X>", false]]}, {"cleared": true}]}
//
// The moment a line arrived is the page's and the rules never read one, so a
// step names none and every line in a run is stamped the same.
//
// The day an instant falls on is the machine's business and not the stamp's:
// what comes back is a time and no date, which is what a person reading a
// conversation as it arrives is correlating against.
//
// The shape is `tests/ui/gloss.mjs`'s and so is the reason: the gate is Python
// (`scripts/check.sh`) and what this needs of the machine it runs on is a node
// and nothing else — no packages, no bundler, no DOM and no network. Stdin and
// stdout are `tests/ui/each.mjs`'s.

import {
  EMPTIED,
  KEPT,
  OPENED,
  QUEUE,
  arrived,
  atBottom,
  cleared,
  held,
  queued,
  quieted,
  stamped,
  waiting,
} from "../../ui/src/monitor.js";
import { each } from "./each.mjs";

// A day to hang a reading on. The stamp draws no date, so which one it is
// reaches nothing; what it is here for is that `new Date(y, m, d, …)` reads
// its arguments as the machine's own zone, which is what a clock at the layout
// is.
const DAY = [2026, 0, 1];

// The stamp every line in a kept conversation carries. The rules copy it and
// never read it, so one for all of them says as much as one each would.
const ARRIVED = new Date(...DAY, 13, 4, 5, 7);

// The conversation `steps` leaves behind, from the one a page opens with.
const keeping = (steps) =>
  steps.reduce((conversation, step) => {
    if ("said" in step) {
      const said = step.said.map(([line, sent]) => ({
        line,
        at: ARRIVED,
        sent,
      }));
      return arrived(conversation, said);
    }
    return "held" in step ? held(conversation) : cleared(conversation);
  }, OPENED);

const answered = (ask) => {
  if ("scroller" in ask) {
    return { bottom: atBottom(ask.scroller) };
  }
  if ("own" in ask) {
    return { kept: KEPT, queue: QUEUE, emptied: EMPTIED };
  }
  if ("waiting" in ask) {
    return { says: waiting(ask.waiting) };
  }
  if ("keeping" in ask) {
    return keeping(ask.keeping);
  }
  if ("queue" in ask) {
    const { behind, went } = queued(ask.queue.behind, ask.queue.said);
    return { ...behind, went };
  }
  if ("quiet" in ask) {
    const said = ask.quiet.said.map(([line, sent]) => ({ line, sent }));
    return quieted(ask.quiet.last, said);
  }
  const at =
    "clock" in ask ? new Date(...DAY, ...ask.clock) : new Date(ask.at);
  return { stamp: stamped(at) };
};

await each(answered);
