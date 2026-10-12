// The journal read into incidents and counts, run.
//
// `tests/ui/test_journal.py` holds the journals and this is what puts them
// through the real function: a JSON array of asks on stdin, a JSON array of
// answers on stdout, in the order they came.
//
// An ask is one of the two. A journal, with the period it is read over —
// a start and an end, a build, or nothing at all for the whole of it —
// answered with the incidents, the counts per district and the station's:
//
//     {"journal": [{"at": "2026-10-12T18:00:00.000+00:00", "build": "g1",
//                   "said": "<p1 A>", "district": "A", "mode": "MAIN",
//                   "limit": 3000}],
//      "period": {"build": "g1"}}
//
// or the module's own numbers, which are the two windows a flip is read
// against and the kinds a district's incidents are counted by:
//
//     {"own": true}
//
// The shape is `tests/ui/gloss.mjs`'s and so is the reason: the gate is Python
// (`scripts/check.sh`) and what this needs of the machine it runs on is a node
// and nothing else — no packages, no bundler, no DOM and no network. Stdin and
// stdout are `tests/ui/each.mjs`'s.

import {
  FLIPPED_MS,
  KINDS,
  REPEATED_MS,
  REPEATS,
  read,
} from "../../ui/src/journal.js";
import { each } from "./each.mjs";

const answered = (ask) => {
  if ("own" in ask) {
    return {
      flipped: FLIPPED_MS,
      repeats: REPEATS,
      repeated: REPEATED_MS,
      kinds: KINDS,
    };
  }
  return read(ask.journal, ask.period ?? {});
};

await each(answered);
