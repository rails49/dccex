// What the page does to the railroad before it asks for a release to be
// written, run.
//
// `tests/ui/test_flash.py` holds the scenarios and this is what puts them
// through the real sequence: a JSON array of scenarios on stdin, a JSON array
// of what happened on stdout, in the order they came.
//
// A scenario is the page's two hands answering: how many messages the stream
// takes before it is shut, and what the face answers when it is asked to
// write.
//
//     {"tag": "v1", "sends": 1, "wrote": {"flashed": false, "says": "…"}}
//
// What comes back is what went down the cable and what was asked of the face,
// in one list and in the order it happened — which is the whole of the
// ordering the railroad depends on — along with the steps the page showed, what
// became of the flash, and the words it can say. Nothing here reaches a
// station, a face, a socket or a DOM: the sequence is handed everything it
// does, which is what lets all of it run under a bare node.
//
// The shape is `tests/ui/releases.mjs`'s and so is the reason: what it needs of
// the machine it runs on is a node and nothing else — no packages, no bundler,
// no DOM and no network.

import {
  CANCELS,
  CHOOSES,
  CONFIRMS,
  CUTS,
  CUTTING,
  STOPPING,
  STOPS,
  UNANSWERED,
  UNSENT,
  WARNS,
  WROTE,
  sequence,
  writing,
} from "../../ui/src/flash.js";

const asked = async () => {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }
  return Buffer.concat(chunks).toString("utf8");
};

const ran = async (scenario) => {
  const tag = scenario.tag ?? "v5.6.4-rails49.1";
  const takes = scenario.sends ?? 2;
  const order = [];
  const shown = [];
  let sent = 0;
  const hands = {
    sends: (typed) => {
      if (sent >= takes) {
        return null;
      }
      sent += 1;
      order.push(`sent ${typed}`);
      return typed;
    },
    writes: async (asked) => {
      order.push(`wrote ${asked}`);
      return scenario.wrote ?? { flashed: true, says: WROTE };
    },
    shows: (step) => {
      shown.push(step);
    },
  };
  return {
    order,
    shown,
    wrote: await sequence(tag, hands),
    writing: writing(tag),
    sends: { STOPS, CUTS },
    says: {
      WARNS,
      CHOOSES,
      CONFIRMS,
      CANCELS,
      STOPPING,
      CUTTING,
      UNSENT,
      UNANSWERED,
      WROTE,
    },
  };
};

const scenarios = JSON.parse(await asked());
const drawn = [];
for (const scenario of scenarios) {
  drawn.push(await ran(scenario));
}
process.stdout.write(JSON.stringify(drawn));
