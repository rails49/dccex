// The decoder, run.
//
// `tests/ui/test_decoder.py` holds the pairs and this is what puts a line
// through the real function: a JSON array of lines on stdin, a JSON array of
// readings — a `say` with whatever fact went with it, or `null` — on stdout,
// in the order they came. Both halves, because both are what the page shows:
// the sentence beside the bytes and the fact the band and the tiles are made
// of come off the same line (#7).
//
// It is here rather than in the UI's own toolchain because the gate is Python
// (`scripts/check.sh`). What it needs is a node and nothing else: no packages,
// no bundler, no DOM and no network, which is why the decoder is written as
// JavaScript (`ui/src/decoder.js`), as the box's own rule is
// (`ui/src/message.js`, `tests/ui/message.mjs`).
//
// Stdin and stdout are `tests/ui/each.mjs`'s, which the seven runners share.

import { read } from "../../ui/src/decoder.js";
import { each } from "./each.mjs";

await each((line) => read(line) ?? null);
