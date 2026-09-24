// What the box at the foot sends, run.
//
// `tests/ui/test_message.py` holds the pairs and this is what puts what was
// typed through the real function: a JSON array of what an operator typed on
// stdin, a JSON array of what goes up the stream — one whole `<…>` message or
// `null` — on stdout, in the order they came.
//
// The shape is `tests/ui/gloss.mjs`'s and so is the reason: the gate is Python
// (`scripts/check.sh`) and what this needs of the machine it runs on is a node
// and nothing else — no packages, no bundler, no DOM and no network. Stdin and
// stdout are `tests/ui/each.mjs`'s.

import { message } from "../../ui/src/message.js";
import { each } from "./each.mjs";

await each((what) => message(what) ?? null);
