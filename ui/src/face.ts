/**
 * Where the mirror's face is, on this page's own origin.
 *
 * A **face** is an app's own interface, about that app rather than about a
 * railroad, and this page's one counterparty is the mirror's (CONTEXT.md,
 * ADR-0008 d.1). It answers under a prefix the door strips before the app
 * sees a request, so the page and the face share one origin and one
 * certificate and nothing here is a host or a port (ADR-0004 d.2).
 *
 * The prefix is written once, here, and everything the page asks for is built
 * from it: the stream the conversation rides (`stream.ts`) as much as anything
 * fetched. A second spelling of it somewhere on the page would be a second
 * answer to where the app is, and the day the door's route moves only one of
 * them would follow.
 *
 * **Every address here is built from that prefix and carries nothing on it.**
 * The one thing the page asks — what **release**s the configured source
 * carries — is a question about the app rather than a question with
 * parameters, and the one thing it asks *for* names a **tag** and nothing
 * else: where releases are read from is that app's own configuration, and a
 * page that could name it would be a page deciding what the command station is
 * offered to run (ADR-0042, `firmware.py`).
 */

import { UNANSWERED, WROTE, type Wrote } from "./flash.js";
import { carried, type Carried } from "./releases.js";

/** The prefix the mirror's face answers under on this page's own origin, and
 *  the whole of what it claims there — the door strips it before the app sees
 *  a request (ADR-0004 d.2). */
export const FACE = "/dccex-usb";

/** Where the **release**s the configured source carries are asked for. The
 *  page asks its own app's face and never the release API: a UI talks to the
 *  bus, the store and its own app's face and nothing else (the organisation's
 *  ADR-0002), and where releases are read from is a flag on that app rather
 *  than anything a browser can name (ADR-0042, `face.py`). */
export const RELEASES_PATH = `${FACE}/releases`;

/** What the list comes back under. */
const RELEASES = "releases";

/**
 * The releases the configured source carries, or `null` where the face did
 * not say.
 *
 * **Nothing said is not nothing published**, so anything but an answer
 * comes back as `null`: a face that is away, an answer that is not a list of
 * releases, a status that is not a 200 — an empty list drawn for any of them
 * would be this page reporting a source it never read, and would send somebody
 * to a release API that is perfectly well (ADR-0009 d.2). The source carrying
 * nothing is a different sentence and it is the face's `[]`.
 *
 * **What this does is the asking, and the reading is `releases.js`'s
 * `carried()`.** The document is read one field at a time, as the app reads
 * the release API, and a list that carries entries and names no release among
 * them comes back as `null` rather than as an empty list — the rule is
 * `face.py`'s `carried()`, which draws the same line on the same document at
 * the app's end of the wire, and the page's half is written as that one is so
 * that whoever changes either finds the other (#66, #95).
 *
 * The two halves of this function are split where a browser stops: the
 * `fetch`, the status and the envelope need one and are here, and what the
 * page makes of a release document needs nothing and is in a module a bare
 * node can run, so that the three answers it can give are asserted by running
 * it (`tests/ui/test_releases.py`, ADR-0009 d.3). It is the same seam
 * `stream.ts` and `framing.js` are split on.
 */
export async function releases(): Promise<Carried[] | null> {
  try {
    const answered = await fetch(RELEASES_PATH);
    if (!answered.ok) {
      return null;
    }
    const said: unknown = await answered.json();
    if (typeof said !== "object" || said === null) {
      return null;
    }
    return carried((said as Record<string, unknown>)[RELEASES]);
  } catch {
    return null;
  }
}

/** Where a **release** is asked to be written onto the station. Asked for and
 *  never read: there is nothing at this address to see, and a page that
 *  reloaded one would write the station twice (`face.py`). */
export const FLASH_PATH = `${FACE}/flash`;

/** How a flash is asked for, what the tag it names rides in, and what it
 *  names the release to write under. */
const POST = "POST";
const JSON_TYPE = "application/json";
const TAG = "tag";

/** What the answer names the release it wrote under, and what it says a
 *  refusal was for. */
const FLASHED = "flashed";
const REASON = "reason";

/**
 * A named release written onto the station, and what became of it.
 *
 * **It names a tag and nothing else.** Where releases are read from is the
 * app's configuration and no request can reach it, so a body that named a
 * source would be a page choosing what the command station is offered to run
 * on a LAN that carries no authentication (ADR-0042, `firmware.py`).
 *
 * **It waits for the write.** The face answers when esptool has finished,
 * which is a minute or two: what the caller asked is whether the station now
 * runs that build, and that is not knowable before the tool has run
 * (`face.py`). What the page does meanwhile is say which step is running
 * (`flash.js`).
 *
 * **A refusal is the face's sentence and not one of this page's.** The mirror
 * says what it turned a flash down for — a tag with no release, a source that
 * could not be asked, a release with no asset or no digest, a station that is
 * not there, a flash already in flight — and a page that wrote its own
 * sentence over that would be guessing at an answer it was given (ADR-0050).
 * What this page says instead is `UNANSWERED`, and only where there was no
 * answer to read.
 *
 * It answers rather than raising, as `releases` above does: a
 * rejection left loose would be a sequence that stopped with nothing said.
 */
export async function flash(tag: string): Promise<Wrote> {
  try {
    const answered = await fetch(FLASH_PATH, {
      method: POST,
      headers: { "content-type": JSON_TYPE },
      body: JSON.stringify({ [TAG]: tag }),
    });
    const said: unknown = await answered.json().catch(() => null);
    const fields =
      typeof said === "object" && said !== null
        ? (said as Record<string, unknown>)
        : {};
    if (answered.ok && typeof fields[FLASHED] === "string") {
      return { flashed: true, says: WROTE };
    }
    const reason = fields[REASON];
    return {
      flashed: false,
      says: typeof reason === "string" && reason !== "" ? reason : UNANSWERED,
    };
  } catch {
    return { flashed: false, says: UNANSWERED };
  }
}
