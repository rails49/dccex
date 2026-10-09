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
 *
 * **What is coloured has two halves and both are here.** That a run of Python
 * is given a class is read off the markup; that the class is readable is
 * computed from Shoelace's own palette, which arrives with the dependency and
 * is reachable only where `node_modules` is. The gate holds the step the sheet
 * asks for instead (`tests/ui/test_script.py`, ADR-0019 d.3).
 */

import { EditorView } from "@codemirror/view";
import dark from "@shoelace-style/shoelace/dist/themes/dark.styles.js";
import light from "@shoelace-style/shoelace/dist/themes/light.styles.js";
import type { CSSResult } from "lit";
import { afterEach, expect, test } from "vitest";

import { scriptStyles } from "../src/ui/dccex-script.styles.js";
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

/** A colour, as sRGB, each channel from 0 to 1. */
type Rgb = [number, number, number];

/** A step of a palette, as a theme declares it. */
const STEP = /(--sl-color-[a-z]+-\d+):\s*([^;]+);/g;

/** The least contrast WCAG 2 asks of text against what is behind it. */
const READABLE = 4.5;

/** Every ink the editor draws text in, with the rule whose background it is
 *  drawn on. The token classes and a marked line number sit on the editor's
 *  own background; the line numbers sit on the gutter's. */
const INKS: [string, string][] = [
  [".script.cm-editor", ".script.cm-editor"],
  [".script.cm-editor .cm-gutters", ".script.cm-editor .cm-gutters"],
  [".script.cm-editor .refused-line", ".script.cm-editor"],
  [".tok-keyword", ".script.cm-editor"],
  [".tok-string", ".script.cm-editor"],
  [".tok-comment", ".script.cm-editor"],
  [".tok-number", ".script.cm-editor"],
  [".tok-decorator", ".script.cm-editor"],
  [".tok-function", ".script.cm-editor"],
];

/** The colour `written` is, from `hsl(h s% l%)` or the same with commas. */
function rgb(written: string): Rgb {
  const inside = /^hsl\(([^)]+)\)$/.exec(written);
  if (inside === null) {
    throw new Error(`${written} is not an hsl colour`);
  }
  const said = inside[1].split(/[\s,]+/).map((part) => Number.parseFloat(part));
  const turn = (((said[0] % 360) + 360) % 360) / 60;
  const saturation = said[1] / 100;
  const lightness = said[2] / 100;
  const chroma = (1 - Math.abs(2 * lightness - 1)) * saturation;
  const beside = chroma * (1 - Math.abs((turn % 2) - 1));
  const sixths: Rgb[] = [
    [chroma, beside, 0],
    [beside, chroma, 0],
    [0, chroma, beside],
    [0, beside, chroma],
    [beside, 0, chroma],
    [chroma, 0, beside],
  ];
  const [red, green, blue] = sixths[Math.floor(turn)];
  const lift = lightness - chroma / 2;
  return [red + lift, green + lift, blue + lift];
}

/** The colours one of Shoelace's themes declares, by custom property.
 *
 * A step may stand for another — `--sl-color-neutral-700` is one of the gray
 * scale — so a value naming a property is read through to the colour behind
 * it. */
function palette(theme: CSSResult): Map<string, Rgb> {
  const written = new Map<string, string>();
  for (const [, step, value] of theme.cssText.matchAll(STEP)) {
    written.set(step, value.trim());
  }
  const read = (value: string): Rgb => {
    const named = /^var\((--[a-z0-9-]+)\)$/.exec(value);
    if (named === null) {
      return rgb(value);
    }
    const stood = written.get(named[1]);
    if (stood === undefined) {
      throw new Error(`${named[1]} is not in the theme`);
    }
    return read(stood);
  };
  return new Map([...written].map(([step, value]) => [step, read(value)]));
}

/** What a theme gives `step`. */
function colour(colours: Map<string, Rgb>, step: string): Rgb {
  const given = colours.get(step);
  if (given === undefined) {
    throw new Error(`${step} is not in the theme`);
  }
  return given;
}

/** The step one rule of the script view's sheet declares `property` as. */
function asked(selector: string, property: string): string {
  const rule = new RegExp(
    `\\n  ${selector.replaceAll(".", "\\.")} \\{([^}]*)\\}`,
  ).exec(scriptStyles.cssText);
  if (rule === null) {
    throw new Error(`no rule for ${selector}`);
  }
  const named = new RegExp(
    `${property}: var\\((--sl-color-[a-z]+-\\d+)\\)`,
  ).exec(rule[1]);
  if (named === null) {
    throw new Error(`${selector} draws its ${property} in no theme step`);
  }
  return named[1];
}

/** How light a colour is, as WCAG 2 measures it. */
function luminance([red, green, blue]: Rgb): number {
  const linear = (channel: number): number =>
    channel <= 0.03928 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
  return 0.2126 * linear(red) + 0.7152 * linear(green) + 0.0722 * linear(blue);
}

/** The contrast between two colours, from 1 to 21. */
function contrast(ink: Rgb, under: Rgb): number {
  const [high, low] = [luminance(ink), luminance(under)].sort((a, b) => b - a);
  return (high + 0.05) / (low + 0.05);
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

test("every ink the editor draws text in is readable in both themes", () => {
  for (const [named, theme] of [
    ["light", light],
    ["dark", dark],
  ] as const) {
    const colours = palette(theme);
    for (const [drawn, behind] of INKS) {
      const ink = colour(colours, asked(drawn, "color"));
      const under = colour(colours, asked(behind, "background"));

      expect(
        contrast(ink, under),
        `${drawn} on ${behind}'s background in the ${named} theme`,
      ).toBeGreaterThanOrEqual(READABLE);
    }
  }
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
