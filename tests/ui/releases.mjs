// What the page lists the releases as, run.
//
// `tests/ui/test_releases.py` holds the scenarios and this is what puts them
// through the real function: a JSON array of scenarios on stdin, a JSON array
// of what a page would be drawing on stdout, in the order they came.
//
// A scenario is what a page would have: what the face answered — or `null`
// where it could not be asked — and what the station says it is running.
//
//     {"carried": [{"tag": "v1", "published": "2025-01-02T03:04:05Z",
//                   "flashable": true}], "build": "v1"}
//
// What comes back is the listing itself and the four sentences the page can
// say about a release or about the list, so that the words an operator reads
// are asserted as words rather than against the source that would produce
// them. Nothing here reaches a network: the scenarios are the face's answer
// already, which is the whole of what this page knows about a release.
//
// The shape is `tests/ui/readings.mjs`'s and so is the reason: what it needs
// of the machine it runs on is a node and nothing else — no packages, no
// bundler, no DOM and no network.

import {
  NONE,
  NO_FIRMWARE,
  ON_STATION,
  UNREADABLE,
  listing,
} from "../../ui/src/releases.js";

const asked = async () => {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }
  return Buffer.concat(chunks).toString("utf8");
};

const drawn = (scenario) => ({
  listing: listing(scenario.carried ?? null, scenario.build ?? null),
  says: { ON_STATION, NO_FIRMWARE, UNREADABLE, NONE },
});

const scenarios = JSON.parse(await asked());
process.stdout.write(JSON.stringify(scenarios.map(drawn)));
