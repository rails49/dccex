// What the **journal** view draws, run.
//
// `tests/ui/test_incidents.py` holds the journals and the scenarios and this is
// what puts them through the real module: a JSON array of asks on stdin, a
// JSON array of answers on stdout, in the order they came.
//
// An ask is one of six. A journal, with the period it is read over and whether
// the routine lines are rows too, answered with the table and the list as a
// page would be drawing them:
//
//     {"journal": [{"at": "2026-10-12T18:00:00.000+00:00", "build": "g1",
//                   "said": "<p1 A>", "district": "A", "mode": "MAIN",
//                   "limit": 3000}],
//      "period": {"build": "g1"}, "routine": true}
//
// The file as the face served it, answered with the lines read out of it and
// the periods they offer:
//
//     {"served": "{\"at\": \"…\"}\n{\"at\": \"…"}
//
// A choice and when the journal was read, answered with the period it means;
// a size in bytes; a duration in milliseconds; a stamp; and the module's own
// words and columns:
//
//     {"choice": "last day", "now": "2026-10-12T18:00:00.000Z"}
//     {"bytes": 1500}
//     {"ms": 1100}
//     {"at": "2026-10-12T18:00:01.100+00:00"}
//     {"own": true}
//
// The shape is `tests/ui/journal.mjs`'s and so is the reason: the gate is
// Python (`scripts/check.sh`) and what this needs of the machine it runs on is
// a node and nothing else — no packages, no bundler, no DOM and no network.
// Stdin and stdout are `tests/ui/each.mjs`'s.

import {
  ALL,
  CANCELS,
  CLEARS,
  CONFIRMS,
  DAY,
  DOWNLOADS,
  EMPTY,
  HEADINGS,
  RELOADS,
  ROUTINE,
  SPANS,
  STATION,
  UNANSWERED,
  UNREADABLE,
  WARNS,
  WEEK,
  builds,
  choices,
  emptied,
  lasted,
  over,
  parsed,
  shown,
  size,
  when,
} from "../../ui/src/incidents.js";
import { each } from "./each.mjs";

const answered = (ask) => {
  if ("own" in ask) {
    return {
      spans: SPANS,
      headings: HEADINGS,
      says: {
        ALL,
        DAY,
        WEEK,
        STATION,
        RELOADS,
        DOWNLOADS,
        ROUTINE,
        CLEARS,
        WARNS,
        CONFIRMS,
        CANCELS,
        EMPTY,
        UNREADABLE,
        UNANSWERED,
      },
    };
  }
  if ("served" in ask) {
    const lines = parsed(ask.served);
    return { lines, builds: builds(lines), choices: choices(lines) };
  }
  if ("choice" in ask) {
    return over(ask.choice, Date.parse(ask.now));
  }
  if ("bytes" in ask) {
    return { size: size(ask.bytes), emptied: emptied(ask.bytes) };
  }
  if ("ms" in ask) {
    return lasted(ask.ms);
  }
  if ("at" in ask) {
    return when(ask.at);
  }
  return shown(ask.journal, ask.period ?? {}, ask.routine ?? false);
};

await each(answered);
