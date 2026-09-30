/**
 * The **script** the page edits, and the rules that are not drawing.
 *
 * A script is a railroad's Python document in `control`'s store, one per
 * railroad, holding the **handler**s the translator runs for this railroad's
 * station (CONTEXT.md, ADR-0013, ADR-0015). The page is where it is written:
 * the person picks a railroad, the text opens in a box, and Apply sends it to
 * the **face**, which compiles it and puts it to the store (ADR-0015 d.5).
 *
 * What is here is everything about that a browser is not needed for — the text
 * a railroad with no script opens with, whether what is in the box is the text
 * that was applied, and what a Tab does to it — so that the rules can be run
 * rather than read (`ui/test/script.test.ts`, the seam `view.ts` is split on).
 * The asking is `face.ts`'s and the drawing is `dccex-script.ts`'s.
 *
 * **The sample is the translator's own**, copied here rather than fetched: the
 * mirror imports nothing but the standard library and itself, so the app that
 * serves the face cannot read the translator's sample and there is nothing on
 * the wire to ask for it (`tests/test_nothing_reaches_in.py`). What holds the
 * copy to the original is a check in the gate, which reads both
 * (`tests/ui/test_script.py`).
 *
 * **Nothing here stops a railroad and nothing here reaches a store.** Applying
 * a script stands the railroad down at the translator's next fetch (ADR-0015
 * d.3), which is what the words below are for: the guard is the person, and a
 * person can only be one if they are told what the gesture does before they
 * are asked (ADR-0006 d.2, as the flash's warning is).
 */

/** The sample **script**, as `dccex/sample.py` writes it: what a railroad
 *  with none of its own opens with, commented out (ADR-0015 d.5).
 *
 *  It is the translator's text verbatim but for the back quotes in its prose,
 *  which a template literal cannot carry unescaped. The gate holds the two
 *  equal (`tests/ui/test_script.py`), so the values in it stay this
 *  installation's rather than drifting into a second recommendation. */
export const SAMPLE = `# Handlers for this railroad's DCC-EX station (ADR-0013, ADR-0015).
#
# \`on(row, address=None)\` keys a handler on an event. The rows are power,
# point, signal, traction, function, and for what the station reported
# reported_power and reported_point.
#
# A handler on a desired value runs in place of the command the translator
# would have sent; \`t.default()\` sends that command as well. \`t.send(text)\`
# sends one raw message. \`t.desired(row, address=None)\` reads the desired
# picture and \`t.reported(row, address=None)\` the last reports; a value the
# bus has not given reads None.


@on("power")
def power(t):
    t.default()
    for district, ma in {"A": 3000, "B": 3000, "C": 1500, "D": 1500}.items():
        t.send(f"<= {district} LIMIT {ma}>")
    reverser(t)


@on("point", "12")
def point_12(t):
    t.default()
    reverser(t)


def reverser(t):
    # District D is the reversing loop behind point 12.
    mode = "MAIN_INV" if t.desired("point", "12") == "thrown" else "MAIN"
    t.send(f"<= D {mode}>")


@on("point", "20")
@on("point", "21")
def signal_5(t):
    t.default()
    closed = t.desired("point", "20") == t.desired("point", "21") == "closed"
    t.send("<A 5 2>" if closed else "<A 5 0>")
`;

/** What a Tab puts in the box. Spaces and not a tab: a script is Python, where
 *  a mixed indentation is a document that does not compile, and four is what
 *  the sample and every module of the package are written with (PEP 8). */
export const SPACES = 4;

/** What is said where the railroads could not be read: the face did not
 *  answer, or the store behind it did not. Nothing said is not no railroads,
 *  so it is a different sentence from the one below (ADR-0009 d.2, the shape
 *  `releases.js` draws the same line in). */
export const UNLISTED = "the railroads could not be read";

/** What is said where the store holds no railroads at all, which is a box
 *  whose store is empty rather than one that could not be asked. */
export const NO_RAILROADS = "the store holds no railroads yet";

/** What is said above a railroad with no script of its own: the box is not
 *  empty, and what is in it is not the railroad's yet. */
export const NONE =
  "this railroad has no script: what is in the box is the sample," +
  " commented out";

/** What is said where the face could not be asked, or answered with something
 *  this page cannot read. Nothing said is not nothing stored: the sentence
 *  says the script could not be read rather than that the railroad has none,
 *  because a page that could not read an answer did not get one (ADR-0009
 *  d.2). */
export const UNREAD =
  "the mirror could not be asked for this railroad's script";

/** What the control that stores the text says. The word is the issue's and it
 *  is the one gesture on this view that leaves the page. */
export const APPLIES = "apply";

/** What an operator is told before they are asked, and the whole reason the
 *  warning exists: a script takes effect from power off, so applying one
 *  stands the railroad down (ADR-0015 d.3, ADR-0006 d.2). */
export const STOPS =
  "applying stops the railroad: the translator exits on the new text," +
  " which cuts track power, and the script takes effect at the next ON";

/** What says yes to it. It names the gesture rather than agreeing with a
 *  question, so a press is a thing somebody meant. */
export const CONFIRMS = "apply it";

/** What declines it. A script that was not applied leaves the edits in the
 *  box: nothing was sent, and there is nothing to report. */
export const CANCELS = "cancel";

/** What is said where the edits in the box are not the text that was applied
 *  and the person is leaving them — another railroad picked, or the page
 *  closed. Unapplied edits stay in the page and nowhere else (ADR-0015 d.5),
 *  so what is on the other side of this question is losing them. */
export const UNAPPLIED =
  "this railroad's script has edits that were not applied," +
  " and leaving it discards them";

/** What says yes to that. */
export const DISCARDS = "discard them";

/** What declines it, which is staying where the edits are. */
export const KEEPS = "keep editing";

/** What is said where the face could not be asked to apply one, or answered
 *  with something this page cannot read. The mirror's own refusals are the
 *  mirror's words and are shown as they came — a script that does not compile
 *  is the line and the message it gave (control ADR-0050, `face.py`). */
export const UNANSWERED =
  "the mirror could not be asked to apply it, so what the store holds is" +
  " what it held";

/** What says which railroad the box is showing, where none is picked yet: a
 *  view opened on nothing is a view that says what to do rather than an empty
 *  box that reads as a railroad with an empty script. */
export const PICK = "pick a railroad to edit its script";

/**
 * What one railroad's script opened as: the text in the box, whether it is
 * the store's, and what is said about it.
 *
 * `text` is `null` where there is nothing to edit, which is the face not
 * having answered: a box offering the sample for a railroad whose script
 * could not be read would be a page inviting somebody to overwrite a document
 * it never saw (ADR-0009 d.2).
 */
export type Opened = {
  /** The text the box opens with, or `null` where there is nothing to edit. */
  text: string | null;
  /** Whether that text is the one the store holds. False is the sample. */
  stored: boolean;
  /** What is said above the box, and `""` where there is nothing to say. */
  says: string;
};

/**
 * What became of an Apply: whether the text is the railroad's script now, and
 * the sentence that says which.
 *
 * One sentence, because what is on the other end is a person — the same shape
 * a flash answers with, for the same reason (`flash.js`, control ADR-0050).
 */
export type Applied = {
  /** Whether the store holds the text now. */
  applied: boolean;
  /** What happened, in words a person reads. */
  says: string;
};

/**
 * `text` with every line of it a comment.
 *
 * A line that is already one, and a line with nothing on it, are left as they
 * are: the sample is half prose already, and `# #` in front of its first
 * sentence is a page that cannot comment out a comment. What comes back
 * registers no **handler** at all, which is a railroad the translator sends
 * its own commands for (ADR-0013 d.2).
 */
export function commented(text: string): string {
  return text
    .split("\n")
    .map((line: string) =>
      line.trim() === "" || line.trimStart().startsWith("#")
        ? line
        : `# ${line}`,
    )
    .join("\n");
}

/**
 * What the box opens with for a railroad, given the text the store holds.
 *
 * Three answers and the page draws all three. The store's text is what is
 * edited. A railroad the store has no script for opens on the sample,
 * commented out, and says so — which is the one place this page puts words in
 * a box a person is about to store, and it is why they are commented: applying
 * it unchanged is a railroad with a script that does nothing, and not a
 * railroad running this installation's districts because a page suggested
 * them. A script that could not be read opens with nothing at all.
 *
 * @param text the text the store holds, `null` where it holds none, and
 *   `undefined` where the face did not say
 */
export function opened(text: string | null | undefined): Opened {
  if (text === undefined) {
    return { text: null, stored: false, says: UNREAD };
  }
  if (text === null) {
    return { text: commented(SAMPLE), stored: false, says: NONE };
  }
  return { text, stored: true, says: "" };
}

/**
 * Whether what is in the box is not what was applied.
 *
 * The comparison is the whole of it: edits stay in the page until Apply, so
 * what says there are unapplied ones is the text differing from the one this
 * railroad opened with or was last applied with (ADR-0015 d.5). A box nobody
 * has typed in — the sample a railroad with no script opens on — is not an
 * edit, and leaving it discards nothing anybody wrote.
 *
 * @param box what is in the box
 * @param applied the text the railroad opened with, or was applied with
 */
export function unapplied(box: string, applied: string | null): boolean {
  return applied !== null && box !== applied;
}

/**
 * What one Tab does: the box's text with spaces where the selection was, and
 * where the caret goes after it.
 *
 * Tab in a box is a browser moving to the next control, which in a page of
 * Python is the one key an editor needs most. So the key is taken here and
 * turned into `SPACES` spaces, and a selection is replaced by them the way
 * typing over one is.
 *
 * @param box what is in the box
 * @param from where the selection starts
 * @param to where it ends, which is `from` where nothing is selected
 */
export function tabbed(
  box: string,
  from: number,
  to: number,
): { text: string; caret: number } {
  const spaces = " ".repeat(SPACES);
  return {
    text: box.slice(0, from) + spaces + box.slice(to),
    caret: from + SPACES,
  };
}

/**
 * What is said where the text is the railroad's script now.
 *
 * It names the railroad: a page with several railroads listed is a page where
 * which one was applied is the thing a reader has to know (ADR-0015 d.5).
 *
 * @param railroad the railroad it was applied for
 */
export function stored(railroad: string): string {
  return `applied: the store holds this text as ${railroad}'s script now`;
}
