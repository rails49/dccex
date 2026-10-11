/**
 * The **script** edited on a mounted pane: the loaded railroad's text in the
 * editor, a text typed, and the two warnings a person reads before anything is
 * lost or stopped.
 *
 * What the rules come to — the text a railroad with no script opens with, and
 * whether the editor holds unapplied edits — is run through them below, the
 * way `view.test.ts` runs the hash's; what is asserted on the page is what the
 * loaded railroad does to it: the script that opens, the editor, the warning
 * that says applying stops the railroad, the edits left stranded by an unload,
 * and the mirror's own sentence where the script does not compile (issue 185,
 * issue 238, ADR-0015 d.5).
 *
 * **The editor is read off its own state** and not off a box's value
 * (ADR-0019). What the keys in it do is the editor's own suite's
 * (`editor.test.ts`); what is here is that the pane opens one, keeps it across
 * a draw, and opens a new document in it for another railroad.
 *
 * The facts are the ones a page would hand it: which railroad `control` has
 * loaded, off the bus, and the two hands that ask the **face** for a script
 * and apply one (`dccex-app.ts`). Neither hand reaches anything here — what
 * they are handed is what a test records and answers.
 */

import { EditorSelection } from "@codemirror/state";
import { EditorView } from "@codemirror/view";
import { expect, test } from "vitest";

import {
  APPLIES,
  CONFIRMS,
  DISCARDS,
  GONE,
  NONE,
  SAMPLE,
  STOPS,
  UNANSWERED,
  UNAPPLIED,
  UNLOADED,
  UNREAD,
  type Applied,
  type Opened,
  commented,
  opened,
  refusal,
  stored,
  unapplied,
} from "../src/script.js";
import { DccexScript } from "../src/ui/dccex-script.js";
import { mounted, part, press, reads } from "./mounted.js";

/** The railroad `control` has loaded, and the one it is given instead. */
const RAILROADS = ["crossover-yard", "bench"];

/** What the store holds for the first of them. */
const SCRIPT = '@on("power")\ndef power(t):\n    t.default()\n';

/** What was asked of the face, in the order it was asked. */
interface Asked {
  readonly opened: string[];
  readonly applied: [string, string][];
}

/** A pane mounted on the railroad `control` has loaded, somewhere for its asks
 *  to go, and what each ask is answered with.
 *
 *  `held` is what the store holds per railroad, `null` for a railroad with no
 *  script and `undefined` for one the face could not be asked about — the
 *  three answers `face.ts` draws the line between.
 *
 *  It is drawn twice over: the pane asks the face while the first draw is
 *  being made, so the answer is in the editor on the next one. */
async function pane(
  held: Record<string, string | null | undefined> = { [RAILROADS[0]]: SCRIPT },
  applies: (railroad: string, text: string) => Applied = (
    railroad: string,
  ) => ({
    applied: true,
    says: stored(railroad),
  }),
  loaded: string | null = RAILROADS[0],
): Promise<[DccexScript, Asked]> {
  const asked: Asked = { opened: [], applied: [] };
  const drawn = new DccexScript();
  drawn.loaded = loaded;
  drawn.opens = (railroad: string): Promise<Opened> => {
    asked.opened.push(railroad);
    return Promise.resolve(opened(held[railroad]));
  };
  drawn.applies = (railroad: string, text: string): Promise<Applied> => {
    asked.applied.push([railroad, text]);
    return Promise.resolve(applies(railroad, text));
  };
  await mounted(drawn);
  await drawn.updateComplete;
  return [drawn, asked];
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

/** `control` loads `railroad`, as the page hands the name down, and the ask
 *  the pane makes of it comes back: the pane names it, asks the face, and
 *  draws the answer when it arrives, which is two turns. */
async function loads(
  drawn: DccexScript,
  railroad: string | null,
): Promise<void> {
  drawn.loaded = railroad;
  await drawn.updateComplete;
  await drawn.updateComplete;
}

/** Whether the control at `selector` is dead. */
function dead(drawn: DccexScript, selector: string): boolean {
  return part(drawn, selector).hasAttribute("disabled");
}

test("the loaded railroad is named and its script is in the editor", async () => {
  const [drawn, asked] = await pane();

  expect(asked.opened).toStrictEqual([RAILROADS[0]]);
  expect(reads(drawn, ".loaded")).toBe(RAILROADS[0]);
  expect(edited(drawn)).toBe(SCRIPT);
  expect(reads(drawn, ".says")).toBeNull();
});

test("there is nothing to pick a railroad with", async () => {
  const [drawn] = await pane();

  expect(drawn.renderRoot.querySelector(".railroad")).toBeNull();
  expect(drawn.renderRoot.querySelector(".railroads")).toBeNull();
});

test("the same railroad loaded again opens nothing and keeps the typing", async () => {
  const [drawn, asked] = await pane();
  await typed(drawn, "# typed and not applied\n");

  await loads(drawn, RAILROADS[0]);

  expect(asked.opened).toStrictEqual([RAILROADS[0]]);
  expect(edited(drawn)).toBe("# typed and not applied\n");
});

test("another railroad loaded opens its script", async () => {
  const other = "# the bench\n";
  const [drawn, asked] = await pane({
    [RAILROADS[0]]: SCRIPT,
    [RAILROADS[1]]: other,
  });

  await loads(drawn, RAILROADS[1]);

  expect(asked.opened).toStrictEqual([RAILROADS[0], RAILROADS[1]]);
  expect(reads(drawn, ".loaded")).toBe(RAILROADS[1]);
  expect(edited(drawn)).toBe(other);
});

test("no railroad loaded leaves no editor and nothing to apply", async () => {
  const [drawn, asked] = await pane({}, undefined, null);

  expect(reads(drawn, ".loaded")).toBe(UNLOADED);
  expect(asked.opened).toStrictEqual([]);
  expect(drawn.renderRoot.querySelector(".editing")).toBeNull();
  expect(drawn.renderRoot.querySelector(".script")).toBeNull();
  expect(drawn.renderRoot.querySelector(".applies")).toBeNull();
});

test("a railroad with no script opens on the sample, commented out", async () => {
  const [drawn] = await pane({ [RAILROADS[0]]: null });

  expect(edited(drawn)).toBe(commented(SAMPLE));
  expect(reads(drawn, ".says")).toBe(NONE);
  for (const line of edited(drawn).split("\n")) {
    expect(line === "" || line.trimStart().startsWith("#")).toBe(true);
  }
});

test("a script that could not be read leaves nothing to edit", async () => {
  const [drawn] = await pane({ [RAILROADS[0]]: undefined });

  expect(reads(drawn, ".says")).toBe(UNREAD);
  expect(drawn.renderRoot.querySelector(".script")).toBeNull();
  expect(drawn.renderRoot.querySelector(".applies")).toBeNull();
});

test("an edit stays in the page and is said to be unapplied", async () => {
  const [drawn, asked] = await pane();

  await typed(drawn, `${SCRIPT}# and another line\n`);

  expect(asked.applied).toStrictEqual([]);
  expect(reads(drawn, ".unapplied")).toBe(UNAPPLIED);
});

test("a railroad unloaded with unapplied edits keeps them and says so", async () => {
  const [drawn, asked] = await pane({
    [RAILROADS[0]]: SCRIPT,
    [RAILROADS[1]]: null,
  });
  await typed(drawn, "# typed and not applied\n");

  await loads(drawn, RAILROADS[1]);

  expect(reads(drawn, ".unloaded .warns")).toBe(GONE);
  expect(reads(drawn, ".discards")).toBe(DISCARDS);
  expect(asked.opened).toStrictEqual([RAILROADS[0]]);
  expect(asked.applied).toStrictEqual([]);
  expect(edited(drawn)).toBe("# typed and not applied\n");
  expect(reads(drawn, ".loaded")).toBe(RAILROADS[0]);
  expect(dead(drawn, ".applies")).toBe(true);
});

test("discarding them opens the railroad that is loaded now", async () => {
  const [drawn, asked] = await pane({
    [RAILROADS[0]]: SCRIPT,
    [RAILROADS[1]]: null,
  });
  await typed(drawn, "# typed and not applied\n");
  await loads(drawn, RAILROADS[1]);

  press(drawn, ".discards");
  await drawn.updateComplete;
  await drawn.updateComplete;

  expect(asked.opened).toStrictEqual([RAILROADS[0], RAILROADS[1]]);
  expect(asked.applied).toStrictEqual([]);
  expect(edited(drawn)).toBe(commented(SAMPLE));
  expect(reads(drawn, ".loaded")).toBe(RAILROADS[1]);
  expect(drawn.renderRoot.querySelector(".unloaded")).toBeNull();
});

test("discarding them with nothing loaded now leaves nothing to edit", async () => {
  const [drawn] = await pane();
  await typed(drawn, "# typed and not applied\n");
  await loads(drawn, null);

  press(drawn, ".discards");
  await drawn.updateComplete;
  await drawn.updateComplete;

  expect(reads(drawn, ".loaded")).toBe(UNLOADED);
  expect(drawn.renderRoot.querySelector(".editing")).toBeNull();
  expect(drawn.renderRoot.querySelector(".applies")).toBeNull();
});

test("the railroad loaded again while its edits stand lets them be applied", async () => {
  const [drawn, asked] = await pane();
  await typed(drawn, "# typed and not applied\n");
  await loads(drawn, RAILROADS[1]);

  await loads(drawn, RAILROADS[0]);

  expect(asked.opened).toStrictEqual([RAILROADS[0]]);
  expect(edited(drawn)).toBe("# typed and not applied\n");
  expect(drawn.renderRoot.querySelector(".unloaded")).toBeNull();
  expect(dead(drawn, ".applies")).toBe(false);
});

test("a railroad unloaded with no edits in it is replaced without a question", async () => {
  const [drawn, asked] = await pane({
    [RAILROADS[0]]: SCRIPT,
    [RAILROADS[1]]: null,
  });

  await loads(drawn, RAILROADS[1]);

  expect(drawn.renderRoot.querySelector(".unloaded")).toBeNull();
  expect(asked.opened).toStrictEqual([RAILROADS[0], RAILROADS[1]]);
});

test("the page closing with unapplied edits is refused", async () => {
  const [drawn] = await pane();
  await typed(drawn, "# typed and not applied\n");

  const leaving = new Event("beforeunload", { cancelable: true });
  window.dispatchEvent(leaving);

  expect(leaving.defaultPrevented).toBe(true);
});

test("the page closing with nothing unapplied is not", async () => {
  await pane();

  const leaving = new Event("beforeunload", { cancelable: true });
  window.dispatchEvent(leaving);

  expect(leaving.defaultPrevented).toBe(false);
});

test("apply says it stops the railroad before it sends anything", async () => {
  const [drawn, asked] = await pane();
  await typed(drawn, "# applied\n");

  press(drawn, ".applies");
  await drawn.updateComplete;

  expect(reads(drawn, ".warning .warns")).toBe(STOPS);
  expect(asked.applied).toStrictEqual([]);
  expect(reads(drawn, ".confirms")).toBe(CONFIRMS);
});

test("the second press is what sends the text", async () => {
  const [drawn, asked] = await pane();
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

test("an apply that lands after another railroad is loaded stays with its own", async () => {
  const other = "# the bench\n";
  const [drawn] = await pane({ [RAILROADS[0]]: SCRIPT, [RAILROADS[1]]: other });
  let lands: (became: Applied) => void = () => undefined;
  drawn.applies = () =>
    new Promise<Applied>((resolve) => {
      lands = resolve;
    });
  await typed(drawn, "# applied\n");
  press(drawn, ".applies");
  await drawn.updateComplete;
  press(drawn, ".confirms");
  await drawn.updateComplete;

  await loads(drawn, RAILROADS[1]);
  lands({ applied: true, says: stored(RAILROADS[0]) });
  await drawn.updateComplete;
  await drawn.updateComplete;

  expect(edited(drawn)).toBe(other);
  expect(drawn.renderRoot.querySelector(".unapplied")).toBeNull();
  expect(drawn.renderRoot.querySelector(".became")).toBeNull();
});

test("a script the mirror refuses is shown in the mirror's own words", async () => {
  const says = "the script does not compile: line 2: expected ':'";
  const [drawn, asked] = await pane({ [RAILROADS[0]]: SCRIPT }, () => ({
    applied: false,
    says,
  }));
  await typed(drawn, "def power(t)\n    pass\n");
  press(drawn, ".applies");
  await drawn.updateComplete;

  press(drawn, ".confirms");
  await drawn.updateComplete;
  await drawn.updateComplete;

  expect(asked.applied).toHaveLength(1);
  expect(reads(drawn, ".became.failed")).toBe(says);
  expect(edited(drawn)).toBe("def power(t)\n    pass\n");
  expect(reads(drawn, ".unapplied")).toBe(UNAPPLIED);
});

/** A pane whose Apply is refused with `says`, open on the loaded railroad
 *  with `text` typed into it. */
async function refused(says: string, text: string): Promise<DccexScript> {
  const [drawn] = await pane({ [RAILROADS[0]]: SCRIPT }, () => ({
    applied: false,
    says,
  }));
  await typed(drawn, text);
  press(drawn, ".applies");
  await drawn.updateComplete;
  press(drawn, ".confirms");
  await drawn.updateComplete;
  await drawn.updateComplete;
  return drawn;
}

/** The marked text in the editor, or `null` where nothing is marked. */
function marked(drawn: DccexScript): Element | null {
  return editor(drawn).contentDOM.querySelector(".refused");
}

test("an apply the mirror refused marks the line it named", async () => {
  const says = "the script does not compile: line 3: invalid syntax";

  const drawn = await refused(says, "a = 1\nb = 2\nc = (\n");

  expect(marked(drawn)?.textContent).toBe("c = (");
  expect(marked(drawn)?.getAttribute("title")).toBe("invalid syntax");
  expect(reads(drawn, ".became.failed")).toBe(says);
  expect(reads(drawn, ".says")).toBeNull();
});

test("an edit after a refused apply clears the mark", async () => {
  const drawn = await refused(
    "the script does not compile: line 3: invalid syntax",
    "a = 1\nb = 2\nc = (\n",
  );

  await typed(drawn, "a = 1\nb = 2\nc = 3\n");

  expect(marked(drawn)).toBeNull();
  expect(reads(drawn, ".became.failed")).toBe(
    "the script does not compile: line 3: invalid syntax",
  );
});

test("a refusal that names no line marks nothing in the editor", async () => {
  const drawn = await refused(
    "the script does not compile: source code string cannot contain null bytes",
    "a = 1\nb = 2\n",
  );

  expect(marked(drawn)).toBeNull();
});

test("an apply that lands leaves no mark", async () => {
  const [drawn] = await pane();
  await typed(drawn, "# applied\n");
  press(drawn, ".applies");
  await drawn.updateComplete;

  press(drawn, ".confirms");
  await drawn.updateComplete;
  await drawn.updateComplete;

  expect(marked(drawn)).toBeNull();
});

test("a key in the editor is an edit the page is holding", async () => {
  const [drawn] = await pane();
  editor(drawn).dispatch({ selection: { anchor: 0 } });

  key(drawn, "Tab");
  await drawn.updateComplete;

  expect(edited(drawn)).toBe(`    ${SCRIPT}`);
  expect(reads(drawn, ".unapplied")).toBe(UNAPPLIED);
});

test("the editor is the same one across a draw, with its history", async () => {
  const [drawn] = await pane();
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

test("another railroad loaded opens a new document, and an undo stays in it", async () => {
  const other = "# the bench\n";
  const [drawn] = await pane({ [RAILROADS[0]]: SCRIPT, [RAILROADS[1]]: other });

  await loads(drawn, RAILROADS[1]);
  key(drawn, "z", { ctrlKey: true });

  expect(edited(drawn)).toBe(other);
});

test("the control that applies says what it does", async () => {
  const [drawn] = await pane();

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

test("the line the mirror's refusal names is read off its sentence", () => {
  expect(
    refusal("the script does not compile: line 3: invalid syntax"),
  ).toStrictEqual({ line: 3, message: "invalid syntax" });
  expect(
    refusal("the script does not compile: line 12: expected ':'"),
  ).toStrictEqual({ line: 12, message: "expected ':'" });
});

test("a refusal that names no line marks nothing", () => {
  expect(
    refusal(
      "the script does not compile: source code string cannot contain null" +
        " bytes",
    ),
  ).toBeNull();
  expect(refusal(UNANSWERED)).toBeNull();
  expect(refusal(stored(RAILROADS[0]))).toBeNull();
});

test("edits are unapplied where the editor is not the text that was applied", () => {
  expect(unapplied(SCRIPT, SCRIPT)).toBe(false);
  expect(unapplied(`${SCRIPT}\n`, SCRIPT)).toBe(true);
  expect(unapplied("anything", null)).toBe(false);
});
