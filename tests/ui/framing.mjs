// Where the stream is, and where a line ends, run.
//
// `tests/ui/test_stream.py` holds the pairs and this is what puts them through
// the real rules: a JSON array of asks on stdin, a JSON array of answers on
// stdout, in the order they came.
//
// An ask is one of the two. An address, as a page's own and the path the
// caller built from the door's prefix:
//
//     {"where": {"href": "https://box/", "protocol": "https:"}, "path": "/p"}
//
// or a conversation arriving, as the frames it came in and the page's clock at
// each read:
//
//     {"arrived": [["<p1>\n<p", 1000], ["0>\n", 1001]]}
//
// What comes back is the address itself, or every whole line with the stamp it
// carries and what is still a partial one — folded through the reads the way
// the socket folds them (`Stream`, `ui/src/stream.ts`), because a line arriving
// across two frames is the case a single call cannot show. A stamp rides as
// milliseconds since the epoch: JSON has no `Date`, and what the pairs are
// about is which read a line was stamped with.
//
// The shape is `tests/ui/gloss.mjs`'s and so is the reason: the gate is Python
// (`scripts/check.sh`) and what this needs of the machine it runs on is a node
// and nothing else — no packages, no bundler, no DOM and no network.

import { lines, streamAt } from "../../ui/src/framing.js";

const asked = async () => {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }
  return Buffer.concat(chunks).toString("utf8");
};

const framed = (arrived) => {
  let buffered = "";
  const read = [];
  for (const [bytes, at] of arrived) {
    const [rest, said] = lines(buffered, bytes, new Date(at));
    buffered = rest;
    read.push(...said);
  }
  return {
    rest: buffered,
    said: read.map((one) => ({
      at: one.at.getTime(),
      line: one.line,
      sent: one.sent,
    })),
  };
};

const answered = (ask) =>
  "where" in ask
    ? { opened: streamAt(ask.where, ask.path) }
    : framed(ask.arrived);

const asks = JSON.parse(await asked());
process.stdout.write(JSON.stringify(asks.map(answered)));
