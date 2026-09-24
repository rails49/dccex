// What the band and the tiles show, run.
//
// `tests/ui/test_readings.py` holds the scenarios and this is what puts them
// through the real functions: a JSON array of scenarios on stdin, a JSON array
// of what a page would be drawing on stdout, in the order they came.
//
// A scenario is what a page would have: the lines the station said and when,
// how many clients the face last answered with, and the moment on the page's
// clock the readings are wanted for.
//
//     {"said": [["<p1>", 0]], "clients": 2, "now": 1000}
//
// What comes back is the readings themselves and the two things drawn out of
// them — the band's readings and the tiles', each as what it is called and
// what it reads. That is the assertion `control`'s band test makes: hand it
// the facts a page would hand it and read what it draws. What this cannot do
// is put those through Lit: this is a bare node with no packages in it
// (`tests/ui/test_decoder.py`); what draws these is held
// against the components' sources instead.
//
// The shape is `tests/ui/gloss.mjs`'s and so is the reason: what it needs of
// the machine it runs on is a node and nothing else — no packages, no bundler,
// no DOM and no network. Stdin and stdout are `tests/ui/each.mjs`'s.

import {
  QUIET,
  asOf,
  band,
  counted,
  heard,
  tiles,
} from "../../ui/src/readings.js";
import { each } from "./each.mjs";

const drawn = (scenario) => {
  let kept = QUIET;
  for (const [line, at] of scenario.said ?? []) {
    kept = heard(kept, line, at);
  }
  if ("clients" in scenario) {
    kept = counted(kept, scenario.clients);
  }
  const readings = asOf(kept, scenario.now ?? 0);
  return { readings, band: band(readings), tiles: tiles(readings) };
};

await each(drawn);
