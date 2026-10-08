/**
 * The **script** edited on a mounted pane: a railroad picked, a text typed, and
 * the two warnings a person reads before anything is lost or stopped.
 *
 * What the rules come to — the text a railroad with no script opens with, and
 * whether the editor holds unapplied edits — is run through them below, the
 * way `view.test.ts` runs the hash's; what is asserted on the page is the
 * gesture: the pick, the editor, the question that opens when edits would be
 * discarded, the warning that says applying stops the railroad, and the
 * mirror's own sentence where the script does not compile (issue 185,
 * ADR-0015 d.5).
 *
 * **The editor is read off its own state** and not off a box's value
 * (ADR-0019). What the keys in it do is the editor's own suite's
 * (`editor.test.ts`); what is here is that the pane opens one, keeps it across
 * a draw, and opens a new document in it for a new railroad.
 *
 * The facts are the ones a page would hand it: the railroads the **face**
 * answered, and the two hands that ask the face for a script and apply one
 * (`dccex-app.ts`). Neither reaches anything here — what they are handed is
 * what a test records and answers.
 */

import { EditorSelection } from "@codemirror/state";
import { EditorView } from "@codemirror/view";
import { expect, test } from "vitest";

import {
  APPLIES,
  CONFIRMS,
  DISCARDS,
  KEEPS,
  NONE,
  NO_RAILROADS,
  PICK,
  SAMPLE,
  STOPS,
  UNAPPLIED,
  UNLISTED,
  UNREAD,
  type Applied,
  type Opened,
  commented,
  opened,
  stored,
  unapplied,
} from "../src/script.js";
import { DccexScript } from "../src/ui/dccex-script.js";
import { all, mounted, press, reads } from "./mounted.js";

/** The railroads the store holds, as the face lists them. */
const RAILROADS = ["crossover-yard", "bench"];

/** What the store holds for the first of them. */
const SCRIPT = '@on("power")\ndef power(t):\n    t.default()\n';

/** What was asked of the face, in the order it was asked. */
interface Asked {
  readonly opened: string[];
  readonly applied: [string, string][];
}

/** A pane mounted with the railroads listed, somewhere for its asks to go,
 *  and what each ask is answered with.
 *
 *  `held` is what the store holds per railroad, `null` for a railroad with no
 *  script and `undefined` for one the face could not be asked about — the
 *  three answers `face.ts` draws the line between. */
async function pane(
  held: Record<string, string | null | undefined> = { [RAILROADS[0]]: SCRIPT },
  applies: (railroad: string, text: string) => Applied = (
    railroad: string,
  ) => ({
    applied: true,
    says: stored(railroad),
  }),
  railroads: string[] | null = RAILROADS,
): Promise<[DccexScript, Asked]> {
  const asked: Asked = { opened: [], applied: [] };
  const drawn = new DccexScript();
  drawn.railroads = railroads;
  drawn.opens = (railroad: string): Promise<Opened> => {
    asked.opened.push(railroad);
    return Promise.resolve(opened(held[railroad]));
  };
  drawn.applies = (railroad: string, text: string): Promise<Applied> => {
    asked.applied.push([railroad, text]);
    return Promise.resolve(applies(railroad, text));
  };
  return [await mounted(drawn), asked];
}

/** The editor, once the pane has made one. */
function editor(drawn: DccexScript): EditorView {
  const made = drawn.editor;
  expect(made, "the pane made no editor").not.toBeNull();
  return made as EditorView;
}

/** What is in the editor. */
function edited(drawn: DccexScript): string {
  return editor(drawn).state.doc.toString();
}

/** Type `text` into the editor, over whatever was in it. */
async function typed(drawn: DccexScript, text: string): Promise<void> {
  const into = editor(drawn);
  into.dispatch({
    changes: { from: 0, to: into.state.doc.length, insert: text },
    selection: EditorSelection.cursor(text.length),
  });
  await drawn.updateComplete;
}

/** Press a key in the editor. */
function key(
  drawn: DccexScript,
  name: string,
  held: KeyboardEventInit = {},
): void {
  editor(drawn).contentDOM.dispatchEvent(
    new KeyboardEvent("keydown", {
      key: name,
      cancelable: true,
      bubbles: true,
      ...held,
    }),
  );
}

/** Press the railroad whose name is `railroad`, and let the ask it makes come
 *  back: the pane sets what it is showing, asks the face, and draws the answer
 *  when it arrives, which is two turns. */
async function picks(drawn: DccexScript, railroad: string): Promise<void> {
  const at = (drawn.railroads ?? []).indexOf(railroad);
  expect(at, `no control for ${railroad}`).toBeGreaterThan(-1);
  press(drawn, `.railroads li:nth-child(${at + 1}) .railroad`);
  await drawn.updateComplete;
  await drawn.updateComplete;
}

test("the railroads the store holds are listed and none is marked", async () => {
  const [drawn] = await pane();

  expect(all(drawn, ".railroad")).toStrictEqual(RAILROADS);
  expect(drawn.renderRoot.querySelector(".railroad[aria-current]")).toBeNull();
  expect(reads(drawn, ".says")).toBe(PICK);
  expect(drawn.renderRoot.querySelector(".script")).toBeNull();
});

test("a railroad picked opens its script in the editor", async () => {
  const [drawn, asked] = await pane();

  await picks(drawn, RAILROADS[0]);

  expect(asked.opened).toStrictEqual([RAILROADS[0]]);
  expect(edited(drawn)).toBe(SCRIPT);
  expect(reads(drawn, ".railroad[aria-current]")).toBe(RAILROADS[0]);
  expect(reads(drawn, ".says")).toBeNull();
});

test("a railroad with no script opens on the sample, commented out", async () => {
  const [drawn] = await pane({ [RAILROADS[1]]: null });

  await picks(drawn, RAILROADS[1]);

  expect(edited(drawn)).toBe(commented(SAMPLE));
  expect(reads(drawn, ".says")).toBe(NONE);
  for (const line of edited(drawn).split("\n")) {
    expect(line === "" || line.trimStart().startsWith("#")).toBe(true);
  }
});

test("a script that could not be read leaves nothing to edit", async () => {
  const [drawn] = await pane({ [RAILROADS[0]]: undefined });

  await picks(drawn, RAILROADS[0]);

  expect(reads(drawn, ".says")).toBe(UNREAD);
  expect(drawn.renderRoot.querySelector(".script")).toBeNull();
  expect(drawn.renderRoot.querySelector(".applies")).toBeNull();
});

test("railroads that could not be read are said to be, and not drawn as none", async () => {
  const [drawn] = await pane({}, undefined, null);

  expect(reads(drawn, ".unlisted")).toBe(UNLISTED);
  expect(all(drawn, ".railroad")).toStrictEqual([]);
});

test("a store with no railroads in it says that instead", async () => {
  const [drawn] = await pane({}, undefined, []);

  expect(reads(drawn, ".unlisted")).toBe(NO_RAILROADS);
});

test("an edit stays in the page and is said to be unapplied", async () => {
  const [drawn, asked] = await pane();
  await picks(drawn, RAILROADS[0]);

  await typed(drawn, `${SCRIPT}# and another line\n`);

  expect(asked.applied).toStrictEqual([]);
  expect(reads(drawn, ".unapplied")).toBe(UNAPPLIED);
});

test("leaving a railroad with unapplied edits asks first", async () => {
  const [drawn, asked] = await pane({
    [RAILROADS[0]]: SCRIPT,
    [RAILROADS[1]]: null,
  });
  await picks(drawn, RAILROADS[0]);
  await typed(drawn, "# typed and not applied\n");

  await picks(drawn, RAILROADS[1]);

  expect(reads(drawn, ".leaving .warns")).toBe(UNAPPLIED);
  expect(reads(drawn, ".discards")).toBe(DISCARDS);
  expect(reads(drawn, ".keeps")).toBe(KEEPS);
  expect(asked.opened).toStrictEqual([RAILROADS[0]]);
  expect(edited(drawn)).toBe("# typed and not applied\n");
  expect(reads(drawn, ".railroad[aria-current]")).toBe(RAILROADS[0]);
});

test("keeping the edits leaves the railroad where it was", async () => {
  const [drawn, asked] = await pane({
    [RAILROADS[0]]: SCRIPT,
    [RAILROADS[1]]: null,
  });
  await picks(drawn, RAILROADS[0]);
  await typed(drawn, "# typed and not applied\n");
  await picks(drawn, RAILROADS[1]);

  press(drawn, ".keeps");
  await drawn.updateComplete;

  expect(drawn.renderRoot.querySelector(".leaving")).toBeNull();
  expect(asked.opened).toStrictEqual([RAILROADS[0]]);
  expect(edited(drawn)).toBe("# typed and not applied\n");
});

test("discarding them opens the railroad that was picked", async () => {
  const [drawn, asked] = await pane({
    [RAILROADS[0]]: SCRIPT,
    [RAILROADS[1]]: null,
  });
  await picks(drawn, RAILROADS[0]);
  await typed(drawn, "# typed and not applied\n");
  await picks(drawn, RAILROADS[1]);

  press(drawn, ".discards");
  await drawn.updateComplete;
  await drawn.updateComplete;

  expect(asked.opened).toStrictEqual([RAILROADS[0], RAILROADS[1]]);
  expect(edited(drawn)).toBe(commented(SAMPLE));
  expect(reads(drawn, ".railroad[aria-current]")).toBe(RAILROADS[1]);
});

test("a railroad with no edits in the editor is left without a question", async () => {
  const [drawn, asked] = await pane({
    [RAILROADS[0]]: SCRIPT,
    [RAILROADS[1]]: null,
  });
  await picks(drawn, RAILROADS[0]);

  await picks(drawn, RAILROADS[1]);

  expect(drawn.renderRoot.querySelector(".leaving")).toBeNull();
  expect(asked.opened).toStrictEqual([RAILROADS[0], RAILROADS[1]]);
});

test("the page closing with unapplied edits is refused", async () => {
  const [drawn] = await pane();
  await picks(drawn, RAILROADS[0]);
  await typed(drawn, "# typed and not applied\n");

  const leaving = new Event("beforeunload", { cancelable: true });
  window.dispatchEvent(leaving);

  expect(leaving.defaultPrevented).toBe(true);
});

test("the page closing with nothing unapplied is not", async () => {
  const [drawn] = await pane();
  await picks(drawn, RAILROADS[0]);

  const leaving = new Event("beforeunload", { cancelable: true });
  window.dispatchEvent(leaving);

  expect(leaving.defaultPrevented).toBe(false);
});

test("apply says it stops the railroad before it sends anything", async () => {
  const [drawn, asked] = await pane();
  await picks(drawn, RAILROADS[0]);
  await typed(drawn, "# applied\n");

  press(drawn, ".applies");
  await drawn.updateComplete;

  expect(reads(drawn, ".warning .warns")).toBe(STOPS);
  expect(asked.applied).toStrictEqual([]);
  expect(reads(drawn, ".confirms")).toBe(CONFIRMS);
});

test("the second press is what sends the text", async () => {
  const [drawn, asked] = await pane();
  await picks(drawn, RAILROADS[0]);
  await typed(drawn, "# applied\n");
  press(drawn, ".applies");
  await drawn.updateComplete;

  press(drawn, ".confirms");
  await drawn.updateComplete;
  await drawn.updateComplete;

  expect(asked.applied).toStrictEqual([[RAILROADS[0], "# applied\n"]]);
  expect(reads(drawn, ".became.applied")).toBe(stored(RAILROADS[0]));
  expect(drawn.renderRoot.querySelector(".unapplied")).toBeNull();
  expect(drawn.renderRoot.querySelector(".warning")).toBeNull();
});

test("declining the warning leaves the edits and sends nothing", async () => {
  const [drawn, asked] = await pane();
  await picks(drawn, RAILROADS[0]);
  await typed(drawn, "# applied\n");
  press(drawn, ".applies");
  await drawn.updateComplete;

  press(drawn, ".cancels");
  await drawn.updateComplete;

  expect(asked.applied).toStrictEqual([]);
  expect(drawn.renderRoot.querySelector(".warning")).toBeNull();
  expect(edited(drawn)).toBe("# applied\n");
  expect(reads(drawn, ".unapplied")).toBe(UNAPPLIED);
});

test("an apply that lands after another railroad is picked stays with its own", async () => {
  const other = "# the bench\n";
  const [drawn] = await pane({ [RAILROADS[0]]: SCRIPT, [RAILROADS[1]]: other });
  let lands: (became: Applied) => void = () => undefined;
  drawn.applies = () =>
    new Promise<Applied>((resolve) => {
      lands = resolve;
    });
  await picks(drawn, RAILROADS[0]);
  await typed(drawn, "# applied\n");
  press(drawn, ".applies");
  await drawn.updateComplete;
  press(drawn, ".confirms");
  await drawn.updateComplete;

  await picks(drawn, RAILROADS[1]);
  lands({ applied: true, says: stored(RAILROADS[0]) });
  await drawn.updateComplete;
  await drawn.updateComplete;

  expect(edited(drawn)).toBe(other);
  expect(drawn.renderRoot.querySelector(".unapplied")).toBeNull();
  expect(drawn.renderRoot.querySelector(".became")).toBeNull();
});

test("a script the mirror refuses is shown in the mirror's own words", async () => {
  const refused = "the script does not compile: line 2: expected ':'";
  const [drawn, asked] = await pane({ [RAILROADS[0]]: SCRIPT }, () => ({
    applied: false,
    says: refused,
  }));
  await picks(drawn, RAILROADS[0]);
  await typed(drawn, "def power(t)\n    pass\n");
  press(drawn, ".applies");
  await drawn.updateComplete;

  press(drawn, ".confirms");
  await drawn.updateComplete;
  await drawn.updateComplete;

  expect(asked.applied).toHaveLength(1);
  expect(reads(drawn, ".became.failed")).toBe(refused);
  expect(edited(drawn)).toBe("def power(t)\n    pass\n");
  expect(reads(drawn, ".unapplied")).toBe(UNAPPLIED);
});

test("a key in the editor is an edit the page is holding", async () => {
  const [drawn] = await pane();
  await picks(drawn, RAILROADS[0]);
  editor(drawn).dispatch({ selection: { anchor: 0 } });

  key(drawn, "Tab");
  await drawn.updateComplete;

  expect(edited(drawn)).toBe(`    ${SCRIPT}`);
  expect(reads(drawn, ".unapplied")).toBe(UNAPPLIED);
});

test("the editor is the same one across a draw, with its history", async () => {
  const [drawn] = await pane();
  await picks(drawn, RAILROADS[0]);
  const made = editor(drawn);
  await typed(drawn, "# typed\n");

  press(drawn, ".applies");
  await drawn.updateComplete;
  press(drawn, ".cancels");
  await drawn.updateComplete;

  expect(editor(drawn)).toBe(made);
  key(drawn, "z", { ctrlKey: true });
  expect(edited(drawn)).toBe(SCRIPT);
});

test("an apply that landed leaves the editor and its history where they are", async () => {
  const [drawn] = await pane();
  await picks(drawn, RAILROADS[0]);
  const made = editor(drawn);
  await typed(drawn, "# applied\n");
  press(drawn, ".applies");
  await drawn.updateComplete;

  press(drawn, ".confirms");
  await drawn.updateComplete;
  await drawn.updateComplete;

  expect(editor(drawn)).toBe(made);
  key(drawn, "z", { ctrlKey: true });
  expect(edited(drawn)).toBe(SCRIPT);
});

test("another railroad opens a new document, and an undo stays in it", async () => {
  const other = "# the bench\n";
  const [drawn] = await pane({ [RAILROADS[0]]: SCRIPT, [RAILROADS[1]]: other });
  await picks(drawn, RAILROADS[0]);

  await picks(drawn, RAILROADS[1]);
  key(drawn, "z", { ctrlKey: true });

  expect(edited(drawn)).toBe(other);
});

test("the control that applies says what it does", async () => {
  const [drawn] = await pane();
  await picks(drawn, RAILROADS[0]);

  expect(reads(drawn, ".applies")).toBe(APPLIES);
  expect(drawn.renderRoot.querySelector(".warning")).toBeNull();
});

/* -- the rules, run ---------------------------------------------------------- */

test("the sample a railroad with no script opens on registers no handler", () => {
  for (const line of commented(SAMPLE).split("\n")) {
    expect(line === "" || line.trimStart().startsWith("#")).toBe(true);
  }
});

test("a line that is already a comment is not commented twice", () => {
  expect(commented("# already\n\nx = 1")).toBe("# already\n\n# x = 1");
});

test("the store's text is what is edited, and the sample is not stored", () => {
  expect(opened(SCRIPT)).toStrictEqual({
    text: SCRIPT,
    stored: true,
    says: "",
  });
  expect(opened(null).stored).toBe(false);
  expect(opened(undefined).text).toBeNull();
});

test("edits are unapplied where the editor is not the text that was applied", () => {
  expect(unapplied(SCRIPT, SCRIPT)).toBe(false);
  expect(unapplied(`${SCRIPT}\n`, SCRIPT)).toBe(true);
  expect(unapplied("anything", null)).toBe(false);
});
