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
// It may also carry the `releases` document the face answered *with*, before
// the page has made anything of it, and then what comes back says what the
// page's reader made of it — the releases, or `null` where the document is
// not a list of releases at all.
//
//     {"document": [{"message": "Not Found"}]}      ->  read: null
//
// What comes back is the listing itself, that reading, and the four sentences
// the page can say about a release or about the list, so that the words an
// operator reads are asserted as words rather than against the source that
// would produce them. Nothing here reaches a network: a scenario is the
// face's answer already, which is the whole of what this page knows about a
// release.
//
// The shape is `tests/ui/readings.mjs`'s and so is the reason: what it needs
// of the machine it runs on is a node and nothing else — no packages, no
// bundler, no DOM and no network. Stdin and stdout are `tests/ui/each.mjs`'s.

import {
  NONE,
  NO_FIRMWARE,
  ON_STATION,
  UNREADABLE,
  carried,
  listing,
} from "../../ui/src/releases.js";
import { each } from "./each.mjs";

const drawn = (scenario) => ({
  listing: listing(scenario.carried ?? null, scenario.build ?? null),
  read: carried(scenario.document ?? null),
  says: { ON_STATION, NO_FIRMWARE, UNREADABLE, NONE },
});

await each(drawn);
