# The GONE warning during an outage

The script view does not keep the `GONE` warning and its `discard them`
button on screen while the railroad is unreported.

## Why this is out of scope

`#gone()` in `ui/src/ui/dccex-script.ts` is worked out from two names: the
railroad the editor is open on and the railroad `control` reports as loaded.
While the railroad is unreported there is no second name, so nothing
disagrees (issue 242). Keeping the warning would mean storing the last
reported name, a second answer to a question the two names already answer.

The cost of not storing it is small. Apply does nothing during an outage, and
the warning comes back when the retained railroad row arrives after the
broker reconnects. The edits stay in the editor the whole time.

## Prior requests

- #249: "script view: an outage hides a `GONE` warning that is already open"
