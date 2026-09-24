// Every ask on stdin, answered on stdout.
//
// The runners beside this file are each one mapping of the page's, and this is
// the part all seven of them had: read stdin to a string, `JSON.parse`, map,
// `JSON.stringify` to stdout, in the order they came. It was written once per
// issue, each copy taken from the last, which is what `tests/ui/node.py` is on
// the other side of the same boundary (#98).
//
// An answer may be a promise — one of the seven runs a sequence the page
// awaits (`tests/ui/flash.mjs`) — and the asks are answered one after another
// so that what comes back is in the order it was asked whatever the mapping
// does.
//
// What this asks of the machine it runs on is a node and nothing else — no
// packages, no bundler, no DOM and no network — which is what the modules it
// runs are written as JavaScript for (`tests/ui/test_decoder.py`).

export const each = async (answer) => {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }
  const asks = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  const answered = [];
  for (const ask of asks) {
    answered.push(await answer(ask));
  }
  process.stdout.write(JSON.stringify(answered));
};
