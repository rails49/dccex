// The decoder, run.
//
// `tests/ui/test_decoder.py` holds the pairs and this is what puts a line
// through the real function: a JSON array of lines on stdin, a JSON array of
// glosses — a sentence or `null` — on stdout, in the order they came.
//
// It is here rather than in the UI's own toolchain because the gate is Python
// (`scripts/check.sh`). What it needs is a node and nothing else: no packages,
// no bundler, no DOM and no network, which is why the decoder is written as
// JavaScript (`ui/src/decoder.js`), as the box's own rule is
// (`ui/src/message.js`, `tests/ui/message.mjs`).

import { gloss } from "../../ui/src/decoder.js";

const read = async () => {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }
  return Buffer.concat(chunks).toString("utf8");
};

const lines = JSON.parse(await read());
process.stdout.write(JSON.stringify(lines.map((line) => gloss(line) ?? null)));
