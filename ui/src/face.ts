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
 * What the page asks — what **release**s the configured source carries, and how
 * far a flash in flight has got — are questions about the app rather than
 * questions with parameters, and the one thing it asks *for* names a **tag** and
 * nothing else: where releases are read from is that app's own configuration,
 * and a page that could name it would be a page deciding what the command
 * station is offered to run (control ADR-0042, `firmware.py`).
 */

import {
  UNANSWERED,
  WAITING,
  type Flashing,
  type Wrote,
  progress,
} from "./flash.js";
import { carried, type Carried } from "./releases.js";

/** The prefix the mirror's face answers under on this page's own origin, and
 *  the whole of what it claims there — the door strips it before the app sees
 *  a request (ADR-0004 d.2). */
export const FACE = "/dccex-usb";

/** Where the **release**s the configured source carries are asked for. The
 *  page asks its own app's face and never the release API: a UI talks to the
 *  bus, the store and its own app's face and nothing else (the organisation's
 *  ADR-0002), and where releases are read from is a flag on that app rather
 *  than anything a browser can name (control ADR-0042, `face.py`). */
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

/** Where a **release** is asked to be written onto the station, and where how
 *  far that writing has got is read.
 *
 *  Two things on one path, which is the face's own arrangement: a POST writes
 *  the station and a GET says what the writing has come to, so a page that
 *  asked how far it had got cannot have written anything by asking, and one
 *  that reloaded the read writes the station no second time (ADR-0012 d.2,
 *  `face.py`). */
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
 * on a LAN that carries no authentication (control ADR-0042, `firmware.py`).
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
 * sentence over that would be guessing at an answer it was given (control
 * ADR-0050). What this page says instead is `UNANSWERED`, and only where there
 * was no answer to read.
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
      return { flashed: true, says: WAITING };
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

/** What how far a flash has got comes back under: the flash in flight, or
 *  `null` where none is running (`face.py`'s `FLASHING`). One key, so that a
 *  page asking twice a second has one thing to read and no flag to read beside
 *  it (ADR-0012 d.2). */
const FLASHING = "flashing";

/**
 * How far the flash in flight has got, or `null` where none is running and
 * where the face did not say.
 *
 * **It is asked for rather than waited on** (ADR-0012, ADR-0010). The POST
 * above sits inside esptool for a minute or two and answers once; this is the
 * question a page can ask while that is happening, and any page can ask it —
 * one opened or reloaded mid-flash is told what is under way, because the
 * answer is about the mirror and not about who pressed.
 *
 * **What this does is the asking, and the reading is `flash.js`'s
 * `progress()`**, which is where a `releases` document's reading is and for the
 * same reason: the `fetch`, the status and the envelope need a browser and are
 * here, and what the page makes of the answer needs nothing and is in a module
 * a bare node runs (`tests/ui/test_flash.py`, ADR-0009 d.3).
 *
 * It answers rather than raising, as the two above do: a rejection left loose
 * on a poll running twice a second would be an unhandled rejection twice a
 * second.
 */
export async function flashing(): Promise<Flashing | null> {
  try {
    const answered = await fetch(FLASH_PATH);
    if (!answered.ok) {
      return null;
    }
    const said: unknown = await answered.json();
    if (typeof said !== "object" || said === null) {
      return null;
    }
    return progress((said as Record<string, unknown>)[FLASHING]);
  } catch {
    return null;
  }
}
