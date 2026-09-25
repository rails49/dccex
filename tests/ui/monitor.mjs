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
// The day an instant falls on is the machine's business and not the stamp's:
// what comes back is a time and no date, which is what a person reading a
// conversation as it arrives is correlating against.
//
// The shape is `tests/ui/gloss.mjs`'s and so is the reason: the gate is Python
// (`scripts/check.sh`) and what this needs of the machine it runs on is a node
// and nothing else — no packages, no bundler, no DOM and no network. Stdin and
// stdout are `tests/ui/each.mjs`'s.

import { atBottom, quieted, stamped } from "../../ui/src/monitor.js";
import { each } from "./each.mjs";

// A day to hang a reading on. The stamp draws no date, so which one it is
// reaches nothing; what it is here for is that `new Date(y, m, d, …)` reads
// its arguments as the machine's own zone, which is what a clock at the layout
// is.
const DAY = [2026, 0, 1];

const answered = (ask) => {
  if ("scroller" in ask) {
    return { bottom: atBottom(ask.scroller) };
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
