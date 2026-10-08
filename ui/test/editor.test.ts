/**
 * The **editor**, over a document: what the keys do, what is coloured, and
 * what it refuses to do (ADR-0019 d.2).
 *
 * CodeMirror is made here directly rather than through a mounted pane, because
 * what is asserted is the editor and not the view around it — the pick, Apply
 * and the two warnings are `script.test.ts`'s.
 *
 * **What is read is the state and the markup, never a rectangle.** happy-dom
 * lays CodeMirror out nowhere (`mounted.ts`), so a width, a caret position on
 * screen and a scroll are not things this can see. The keys reach the editor
 * as a `keydown` on the text, which is where its keymap listens.
 *
 * `Mod-/` is the comment key, which is Cmd-/ on a Mac and Ctrl-/ everywhere
 * else. CodeMirror reads the platform, and the platform here is not a Mac, so
 * what is pressed below is the Ctrl one.
 */

import { EditorView } from "@codemirror/view";
import { afterEach, expect, test } from "vitest";

import { INDENT, editing, mark } from "../src/ui/editor.js";

/** One indent. */
const DEEP = " ".repeat(INDENT);

/** The editors made, so that each is let go of after its check. */
const made: EditorView[] = [];

/** An editor over `text`, in the document. */
function editor(text: string): EditorView {
  const into = document.createElement("div");
  document.body.append(into);
  const view = new EditorView({
    parent: into,
    state: editing(text, "script", () => undefined),
  });
  made.push(view);
  return view;
}

/** Put the caret at `at`. */
function caret(view: EditorView, at: number): void {
  view.dispatch({ selection: { anchor: at } });
}

/** Press a key on the text. */
function press(view: EditorView, key: string, held: KeyboardEventInit = {}): void {
  view.contentDOM.dispatchEvent(
    new KeyboardEvent("keydown", { key, cancelable: true, bubbles: true, ...held }),
  );
}

/** What is in the editor. */
function reads(view: EditorView): string {
  return view.state.doc.toString();
}

/** The line numbers drawn with a mark on them. */
function numbered(view: EditorView): (string | null)[] {
  return [...view.dom.querySelectorAll(".cm-lineNumbers .refused-line")].map(
    (drawn) => drawn.textContent,
  );
}

/** The classes every coloured run of `view` was drawn with. */
function coloured(view: EditorView): string[] {
  return [...view.contentDOM.querySelectorAll("span")].map(
    (drawn) => drawn.className,
  );
}

afterEach(() => {
  for (const view of made.splice(0)) {
    view.destroy();
  }
});

test("the indent unit is four spaces", () => {
  expect(INDENT).toBe(4);
  const view = editor("x = 1\n");
  caret(view, 0);
  press(view, "Tab");

  expect(reads(view)).toBe(`${DEEP}x = 1\n`);
});

test("enter indents, and one further after a colon", () => {
  const view = editor("def power(t):");
  caret(view, "def power(t):".length);

  press(view, "Enter");

  expect(reads(view)).toBe(`def power(t):\n${DEEP}`);
});

test("enter keeps the indent of the line it was pressed on", () => {
  const view = editor(`def power(t):\n${DEEP}t.default()`);
  caret(view, reads(view).length);

  press(view, "Enter");

  expect(reads(view)).toBe(`def power(t):\n${DEEP}t.default()\n${DEEP}`);
});

test("tab and shift-tab indent and dedent the lines the selection covers", () => {
  const view = editor("a = 1\nb = 2\nc = 3\n");
  view.dispatch({ selection: { anchor: 2, head: 8 } });

  press(view, "Tab");
  const indented = reads(view);
  press(view, "Tab", { shiftKey: true });

  expect(indented).toBe(`${DEEP}a = 1\n${DEEP}b = 2\nc = 3\n`);
  expect(reads(view)).toBe("a = 1\nb = 2\nc = 3\n");
});

test("backspace in leading spaces takes one indent", () => {
  const view = editor(`def power(t):\n${DEEP}${DEEP}t.default()\n`);
  caret(view, `def power(t):\n${DEEP}${DEEP}`.length);

  press(view, "Backspace");

  expect(reads(view)).toBe(`def power(t):\n${DEEP}t.default()\n`);
});

test("ctrl-slash comments the line, and again uncomments it", () => {
  const view = editor("t.default()\n");
  caret(view, 0);

  press(view, "/", { ctrlKey: true });
  const commented = reads(view);
  press(view, "/", { ctrlKey: true });

  expect(commented).toBe("# t.default()\n");
  expect(reads(view)).toBe("t.default()\n");
});

test("undo and redo cover an indent as well as a keystroke", () => {
  const view = editor("x = 1\n");
  caret(view, 0);
  press(view, "Tab");

  press(view, "z", { ctrlKey: true });
  const undone = reads(view);
  press(view, "y", { ctrlKey: true });

  expect(undone).toBe("x = 1\n");
  expect(reads(view)).toBe(`${DEEP}x = 1\n`);
});

test("python is coloured: a keyword, a string, a comment, a number, a decorator and a name", () => {
  const view = editor(
    '@on("start")\ndef configure(t):\n    # the districts\n    limit = 2000\n',
  );

  expect(coloured(view)).toEqual(
    expect.arrayContaining([
      "tok-keyword",
      "tok-string",
      "tok-comment",
      "tok-number",
      "tok-decorator",
      "tok-function",
    ]),
  );
});

test("the lines are numbered", () => {
  const view = editor("a = 1\nb = 2\n");

  const numbers = [
    ...view.dom.querySelectorAll(".cm-lineNumbers .cm-gutterElement"),
  ].map((drawn) => drawn.textContent);

  expect(numbers.slice(1)).toStrictEqual(["1", "2", "3"]);
});

test("nothing closes a bracket or a quote", () => {
  const view = editor("");

  view.dispatch({ changes: { from: 0, insert: "(" }, selection: { anchor: 1 } });
  view.dispatch({ changes: { from: 1, insert: '"' }, selection: { anchor: 2 } });

  expect(reads(view)).toBe('("');
});

test("the editor works in a shadow root", () => {
  const host = document.createElement("div");
  document.body.append(host);
  const root = host.attachShadow({ mode: "open" });
  const into = document.createElement("div");
  root.append(into);
  const view = new EditorView({
    parent: into,
    state: editing("x = 1\n", "script", () => undefined),
  });
  made.push(view);

  expect(view.root).toBe(root);
  expect(root.querySelector(".cm-content")).toBe(view.contentDOM);
});

test("every change says the whole text", () => {
  const said: string[] = [];
  const into = document.createElement("div");
  document.body.append(into);
  const view = new EditorView({
    parent: into,
    state: editing("x = 1\n", "script", (text: string) => {
      said.push(text);
    }),
  });
  made.push(view);
  caret(view, 0);

  press(view, "Tab");
  press(view, "z", { ctrlKey: true });

  expect(said).toStrictEqual([`${DEEP}x = 1\n`, "x = 1\n"]);
});

test("a failed apply marks the line it names, and hovering says why", () => {
  const view = editor("a = 1\nb = 2\nc = (\n");

  mark(view, { line: 3, message: "invalid syntax" });

  const underlined = view.contentDOM.querySelector(".refused");
  expect(underlined?.textContent).toBe("c = (");
  expect(underlined?.getAttribute("title")).toBe("invalid syntax");
  expect(numbered(view)).toStrictEqual(["3"]);
});

test("any edit clears the mark", () => {
  const view = editor("a = 1\nb = 2\nc = (\n");
  mark(view, { line: 3, message: "invalid syntax" });
  caret(view, 0);

  press(view, "Tab");

  expect(view.contentDOM.querySelector(".refused")).toBeNull();
  expect(numbered(view)).toStrictEqual([]);
});

test("a refusal naming a line the document has not marks nothing", () => {
  const view = editor("a = 1\nb = 2\n");

  mark(view, { line: 9, message: "unexpected EOF while parsing" });

  expect(view.contentDOM.querySelector(".refused")).toBeNull();
  expect(numbered(view)).toStrictEqual([]);
});

test("a mark on a line with nothing on it is the gutter's alone", () => {
  const view = editor("a = 1\n\nc = 3\n");

  mark(view, { line: 2, message: "invalid syntax" });

  expect(view.contentDOM.querySelector(".refused")).toBeNull();
  expect(numbered(view)).toStrictEqual(["2"]);
});

test("nothing marked takes the mark away", () => {
  const view = editor("a = 1\nb = 2\n");
  mark(view, { line: 1, message: "invalid syntax" });

  mark(view, null);

  expect(view.contentDOM.querySelector(".refused")).toBeNull();
  expect(numbered(view)).toStrictEqual([]);
});

test("a screen reader is told what it is", () => {
  const view = editor("x = 1\n");

  expect(view.contentDOM.getAttribute("aria-label")).toBe("script");
  expect(view.contentDOM.getAttribute("spellcheck")).toBe("false");
});
