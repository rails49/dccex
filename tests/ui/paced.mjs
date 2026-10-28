// What the box at the foot sends, and when, run.
//
// `tests/ui/test_paced.py` holds the cases and this puts them through the real
// rules: a JSON array of asks on stdin, a JSON array of answers on stdout, in
// the order they came.
//
// An ask is one of three. Typing, answered with the messages it is split into:
//
//     {"listed": "<W 32 0> <W 263 128>"}
//
// or typing, answered with what the box remembers for it:
//
//     {"recalled": "<W 32 0> <W 263 128>"}
//
// or a run of what happens while the page sends, from a page that is sending
// nothing. A step is typing sent from the box, a line the station said, the
// wait for a reply running out, or the stream closing:
//
//     {"run": [{"typed": "<W 32 0><R>"}, {"heard": "<r 32 0>"},
//              {"silent": true}, {"closed": true}]}
//
// answered with what went up and the notes the page put in, in order:
//
//     [{"sent": "<W 32 0>"}, {"note": "1 command not sent: ..."}]
//
// The loop that sends what `next` hands back is the page's (`dccex-app.ts`),
// written again here in its five lines. Stdin and stdout are
// `tests/ui/each.mjs`'s.

import {
  CLOSED,
  IDLE,
  added,
  answered,
  listed,
  next,
  recalled,
  stopped,
  waited,
} from "../../ui/src/paced.js";
import { each } from "./each.mjs";

const run = (steps) => {
  const said = [];
  let pacing = IDLE;
  const drain = () => {
    for (;;) {
      const going = next(pacing);
      if (going.send === null) {
        return;
      }
      pacing = going.pacing;
      said.push({ sent: going.send });
    }
  };
  const stop = ({ pacing: now, note }) => {
    pacing = now;
    if (note !== null) {
      said.push({ note });
    }
  };
  for (const step of steps) {
    if ("typed" in step) {
      pacing = added(pacing, listed(step.typed));
    } else if ("heard" in step) {
      stop(answered(pacing, step.heard));
    } else if ("silent" in step) {
      stop(waited(pacing));
    } else {
      stop(stopped(pacing, CLOSED));
    }
    drain();
  }
  return said;
};

await each((ask) => {
  if ("listed" in ask) {
    return listed(ask.listed);
  }
  if ("recalled" in ask) {
    return recalled(ask.recalled);
  }
  return run(ask.run);
});
