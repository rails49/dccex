// What the band and the tiles show, run.
//
// `tests/ui/test_readings.py` holds the scenarios and this is what puts them
// through the real functions: a JSON array of scenarios on stdin, a JSON array
// of what a page would be drawing on stdout, in the order they came.
//
// A scenario is what a page would have: the lines the station said and when,
// the moment on the page's clock the readings are wanted for, and what the bus
// says about the railroad's power (ADR-0017).
//
//     {"said": [["<p1 A>", 0]], "now": 1000,
//      "layout": {"connected": true, "power": "on"}}
//
// A scenario that says nothing about the bus is a page that has not reached
// the broker, which is what one has until it answers. A scenario whose bus
// names no `railroad` is one whose railroad is unreported, which is what the
// value carries as `undefined`: no railroad row has arrived since the
// connection came up (#242).
//
// What comes back is the readings themselves and the two things drawn out of
// them — the band's readings and the tiles', each as what it is called and
// what it reads — and what a payload on each of `layout`'s two rows reads as,
// for a scenario that carries one: the power row's through `reported`
// (ADR-0017 d.2) and the railroad row's through `named` (the organisation's
// ADR-0014, #239).
//
// That is the assertion `control`'s band test makes: hand it
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
  UNREACHABLE,
  asOf,
  band,
  heard,
  named,
  reported,
  tiles,
} from "../../ui/src/readings.js";
import { each } from "./each.mjs";

const drawn = (scenario) => {
  let kept = QUIET;
  for (const [line, at] of scenario.said ?? []) {
    kept = heard(kept, line, at);
  }
  const readings = asOf(kept, scenario.now ?? 0);
  const layout = scenario.layout ?? UNREACHABLE;
  return {
    readings,
    band: band(readings, layout),
    tiles: tiles(readings),
    reported: (scenario.payload ?? []).map(reported),
    named: (scenario.loaded ?? []).map(named),
  };
};

await each(drawn);
