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
 * **Every address here carries nothing on it but a railroad.** What the page
 * asks about the station — what **release**s the configured source carries, and
 * how far a flash in flight has got — are questions about the app rather than
 * questions with parameters, and the one thing it asks *for* there names a
 * **tag** and nothing else: where releases are read from is that app's own
 * configuration, and a page that could name it would be a page deciding what
 * the command station is offered to run (control ADR-0042, `firmware.py`). The
 * railroad whose **script** is being edited is the exception and is a level of
 * the address, because it is what is being edited rather than where to edit it
 * — the store is the mirror's configuration in exactly the way the release API
 * is (ADR-0015 d.5, `face.py`).
 *
 * **The store is asked through here and never directly.** A UI talks to the
 * bus, the store and its own app's face (the organisation's ADR-0002), and the
 * store this page's script lives in is on the box's own network where a browser
 * cannot reach it: the face is what reads and writes the document, and this
 * page's half is the three addresses below.
 */

import {
  UNANSWERED,
  WAITING,
  type Flashing,
  type Wrote,
  progress,
} from "./flash.js";
import { carried, type Carried } from "./releases.js";
import {
  UNANSWERED as UNANSWERED_APPLY,
  type Applied,
  type Opened,
  opened,
  stored,
} from "./script.js";

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

/** Where the railroads `control`'s store holds are asked for. The store is not
 *  asked directly: a browser on this origin cannot reach it, so the face lists
 *  them and the page picks one (ADR-0015 d.5, the organisation's ADR-0002). */
export const RAILROADS_PATH = `${FACE}/railroads`;

/** What the list comes back under. */
const RAILROADS = "railroads";

/**
 * The railroads the store holds, in the order the store lists them, or `null`
 * where the face did not say.
 *
 * **Nothing said is not no railroads**, so anything but an answer comes back
 * as `null`: a face that is away, a store that is away behind it, an answer
 * that is not a list of names — an empty list drawn for any of them would be
 * this page reporting a store it never read (ADR-0009 d.2). A store that holds
 * none is a different sentence and it is the face's `[]`.
 *
 * None of them is marked as the one that is running. Which railroad that is is
 * the bus's to say and is a row in `control`'s UI, not a reading this page can
 * make (ADR-0015 d.5).
 */
export async function railroads(): Promise<string[] | null> {
  try {
    const answered = await fetch(RAILROADS_PATH);
    if (!answered.ok) {
      return null;
    }
    const said: unknown = await answered.json();
    if (typeof said !== "object" || said === null) {
      return null;
    }
    const listed = (said as Record<string, unknown>)[RAILROADS];
    if (!Array.isArray(listed)) {
      return null;
    }
    return (listed as unknown[]).filter(
      (name: unknown): name is string => typeof name === "string" && name !== "",
    );
  } catch {
    return null;
  }
}

/** Where one railroad's **script** is read and applied: the railroad is a
 *  level of the address, escaped as one, so a name with a space or a slash in
 *  it is a name and never a route (`face.py`'s `under()`).
 *
 *  Two things on one address, which is the face's own arrangement: a GET reads
 *  the text and a PUT applies one, so a page that reloaded the read has applied
 *  nothing (ADR-0015 d.1, d.5). */
export function scriptPath(railroad: string): string {
  return `${FACE}/scripts/${encodeURIComponent(railroad)}`;
}

/** How a script is applied, and what the text rides in. The railroad is the
 *  address and the store is the mirror's configuration, so the body names the
 *  text and nothing else (`face.py`). */
const PUT = "PUT";
const TEXT = "text";

/** What the answer names an applied script under. */
const APPLIED = "applied";

/** What the face answers a railroad it holds no script for with. The one
 *  status this page reads, because it is the one that is an answer about the
 *  railroad rather than about the asking (`face.py`). */
const NOT_FOUND = 404;

/**
 * One railroad's **script**, as the box opens with it: the store's text, the
 * sample where the store holds none, or nothing where it could not be read
 * (`script.ts`'s `opened()`).
 *
 * **A railroad with no script and a script that could not be read are
 * different answers**, and the face draws the line for this page: a `404` is a
 * railroad nobody has written one for, which opens on the sample, and anything
 * else is a page that has not been told what the store holds and must not offer
 * to overwrite it (ADR-0009 d.2, ADR-0015 d.5).
 *
 * What this does is the asking, and the reading is `script.ts`'s, which is the
 * seam the releases and the flash are split on: the `fetch`, the status and the
 * envelope need a browser and are here, and what the page makes of the answer
 * is run without one (`ui/test/script.test.ts`).
 */
export async function script(railroad: string): Promise<Opened> {
  try {
    const answered = await fetch(scriptPath(railroad));
    if (answered.status === NOT_FOUND) {
      return opened(null);
    }
    if (!answered.ok) {
      return opened(undefined);
    }
    const said: unknown = await answered.json();
    if (typeof said !== "object" || said === null) {
      return opened(undefined);
    }
    const text = (said as Record<string, unknown>)[TEXT];
    return opened(typeof text === "string" ? text : undefined);
  } catch {
    return opened(undefined);
  }
}

/**
 * A railroad's **script** applied: the text sent to the face, which compiles
 * it and puts it to the store, and what became of that.
 *
 * **The compiling is the face's and so is the storing** (ADR-0015 d.5). A text
 * that does not compile comes back refused with the line and the message, which
 * is what the page shows: the mirror says what it turned an Apply down for, and
 * a page that wrote its own sentence over that would be guessing at an answer it
 * was given (control ADR-0050). What this page says instead is `UNANSWERED`, and
 * only where there was no answer to read.
 *
 * It answers rather than raising, as the three above do: a rejection left loose
 * would be a sequence that stopped with nothing said.
 */
export async function applies(
  railroad: string,
  text: string,
): Promise<Applied> {
  try {
    const answered = await fetch(scriptPath(railroad), {
      method: PUT,
      headers: { "content-type": JSON_TYPE },
      body: JSON.stringify({ [TEXT]: text }),
    });
    const said: unknown = await answered.json().catch(() => null);
    const fields =
      typeof said === "object" && said !== null
        ? (said as Record<string, unknown>)
        : {};
    if (answered.ok && typeof fields[APPLIED] === "string") {
      return { applied: true, says: stored(railroad) };
    }
    const reason = fields[REASON];
    return {
      applied: false,
      says:
        typeof reason === "string" && reason !== "" ? reason : UNANSWERED_APPLY,
    };
  } catch {
    return { applied: false, says: UNANSWERED_APPLY };
  }
}
