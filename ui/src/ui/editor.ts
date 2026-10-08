/**
 * The **editor** the **script** view edits a railroad's Python in: CodeMirror
 * 6, built from its modules (ADR-0019 d.1).
 *
 * What is here is the editor's state — the language, the indent unit, the keys,
 * which tags carry which class, and the mark a refused Apply leaves on the line
 * it named — and nothing about the view it sits on. The pane makes one
 * `EditorView` over this and keeps it (`dccex-script.ts`).
 *
 * **The colours are not here.** Every tag gets a class and the classes are
 * coloured in the pane's stylesheet, which is the one place the view's colours
 * are written and the one place a check can read them
 * (`dccex-script.styles.ts`, ADR-0019 d.3). The editor draws in the pane's
 * shadow root, so those rules reach it.
 *
 * **`basicSetup` is not used** (ADR-0019 d.1). It brings bracket closing,
 * quote closing and a search panel, and what the view offers is decided here
 * rather than by what a bundle happened to carry (ADR-0019 d.2).
 */

import {
  defaultKeymap,
  history,
  historyKeymap,
  indentWithTab,
} from "@codemirror/commands";
import { python } from "@codemirror/lang-python";
import {
  HighlightStyle,
  bracketMatching,
  indentUnit,
  syntaxHighlighting,
} from "@codemirror/language";
import {
  EditorState,
  RangeSet,
  StateEffect,
  StateField,
  type Line,
} from "@codemirror/state";
import {
  Decoration,
  EditorView,
  GutterMarker,
  gutterLineClass,
  keymap,
  lineNumbers,
} from "@codemirror/view";
import { tags } from "@lezer/highlight";

import { type Refusal } from "../script.js";

/** How far one indent goes. Spaces and not a tab: a script is Python, where a
 *  mixed indentation is a document that does not compile, and four is what the
 *  sample and every module of the package are written with (PEP 8). */
export const INDENT = 4;

/** What a tag is drawn as: a class, and the colour on it is the pane's.
 *
 *  Six of them, which is what a reader of Python needs told apart: a keyword,
 *  a string, a comment, a number, a decorator and the name of a function. A
 *  tag no line names is drawn as the text around it rather than given a
 *  seventh colour nobody asked for.
 *
 *  The tags are the ones `@lezer/python` styles its tree with, and the parents
 *  are named where it uses several children of one: `tags.keyword` catches the
 *  control, operator, module and definition keywords, and `tags.comment`
 *  catches the line comments a script is half made of. The decorator is the
 *  `@`, which Python's grammar tags as meta. */
const COLOURED = HighlightStyle.define([
  { tag: tags.keyword, class: "tok-keyword" },
  { tag: tags.modifier, class: "tok-keyword" },
  { tag: tags.bool, class: "tok-keyword" },
  { tag: tags.null, class: "tok-keyword" },
  { tag: tags.self, class: "tok-keyword" },
  { tag: tags.string, class: "tok-string" },
  { tag: tags.special(tags.string), class: "tok-string" },
  { tag: tags.escape, class: "tok-string" },
  { tag: tags.comment, class: "tok-comment" },
  { tag: tags.number, class: "tok-number" },
  { tag: tags.meta, class: "tok-decorator" },
  { tag: tags.function(tags.variableName), class: "tok-function" },
  {
    tag: tags.function(tags.definition(tags.variableName)),
    class: "tok-function",
  },
  { tag: tags.function(tags.propertyName), class: "tok-function" },
  { tag: tags.definition(tags.className), class: "tok-function" },
]);

/** What the line a failed Apply named is drawn with: the text under a rule,
 *  and the line's number in the gutter told apart. The colours are the pane's
 *  like every other class here (`dccex-script.styles.ts`). */
const MARK = "refused";
const MARK_GUTTER = "refused-line";

/** What tells the field below which line to mark, or that there is none. */
const MARKS = StateEffect.define<Refusal | null>();

/** The line marked, or `null` where none is (ADR-0019 d.4).
 *
 *  Set by `mark()` below and cleared by any change to the document: the line
 *  the face named is a line of the text that was applied, so a mark left
 *  standing over typing would point at a line that has moved — and the person
 *  typing is answering the refusal. */
const MARKED = StateField.define<Refusal | null>({
  create: () => null,
  update(marked, change) {
    if (change.docChanged) {
      return null;
    }
    for (const effect of change.effects) {
      if (effect.is(MARKS)) {
        return effect.value;
      }
    }
    return marked;
  },
});

/** The line the mark is on, or `null` where there is no mark or where the
 *  number is not a line this document has.
 *
 *  A number past the end marks nothing rather than the last line: a mark is an
 *  answer about where the fault is, and the nearest line to one is a guess
 *  (ADR-0009 d.2). */
function at(state: EditorState): Line | null {
  const marked = state.field(MARKED);
  return marked === null || marked.line > state.doc.lines
    ? null
    : state.doc.line(marked.line);
}

/** The rule under the marked line's text, and the message on it: hovering says
 *  what the face said about that line.
 *
 *  A line with nothing on it is the gutter's mark alone — there is no text to
 *  draw a rule under, and a decoration over no characters is not a thing
 *  CodeMirror draws. */
const UNDERLINED = EditorView.decorations.compute([MARKED], (state) => {
  const line = at(state);
  const marked = state.field(MARKED);
  if (line === null || marked === null || line.from === line.to) {
    return Decoration.none;
  }
  return Decoration.set([
    Decoration.mark({
      class: MARK,
      attributes: { title: marked.message },
    }).range(line.from, line.to),
  ]);
});

/** The marked line's number, told apart in the gutter the lines are numbered
 *  in. The number is what a reader matches the face's sentence against, so the
 *  mark is on that rather than in a gutter of its own. */
const IN_GUTTER = new (class extends GutterMarker {
  override elementClass = MARK_GUTTER;
})();

const NUMBERED = gutterLineClass.compute([MARKED], (state) => {
  const line = at(state);
  return line === null
    ? RangeSet.empty
    : RangeSet.of(IN_GUTTER.range(line.from));
});

/**
 * Mark the line a failed Apply named in `view`, or take the mark away with
 * `null` (ADR-0019 d.4).
 *
 * What is marked is read off the face's own sentence and is the pane's to pass
 * on (`script.ts`'s `refusal()`, `dccex-script.ts`). Nothing here reads the
 * text: which line is wrong is Python's answer and not a page's.
 *
 * @param view the editor
 * @param marked the line and the message, or `null` for no mark
 */
export function mark(view: EditorView, marked: Refusal | null): void {
  view.dispatch({ effects: MARKS.of(marked) });
}

/**
 * What the editor is made of, less the document.
 *
 * The keys are the default keymap's — Enter indents, and Python's own grammar
 * is what indents one further after a `:`; Backspace in leading spaces takes
 * one indent; Ctrl-/ and Cmd-/ comment and uncomment — with Tab and Shift-Tab
 * indenting and dedenting the lines the selection covers, and the history's
 * keys over both. Every one of them is a transaction, so undo and redo cover
 * the indent keys as well as the typing (ADR-0019 d.2).
 *
 * Line numbers and the matching bracket, and nothing that closes a bracket or
 * a quote and no search: a script is a page of Python somebody reads before
 * they change it, and a page that put a `)` in uninvited is a page editing it.
 *
 * The mark goes with the numbers, because the number is what a reader matches
 * the face's sentence against (ADR-0019 d.4).
 */
const EDITS = [
  lineNumbers(),
  MARKED,
  UNDERLINED,
  NUMBERED,
  history(),
  bracketMatching(),
  indentUnit.of(" ".repeat(INDENT)),
  python(),
  syntaxHighlighting(COLOURED),
  keymap.of([...defaultKeymap, ...historyKeymap, indentWithTab]),
  EditorView.editorAttributes.of({ class: "script" }),
];

/**
 * The editor's state over `text`, telling `typed` what is in it after every
 * change.
 *
 * This is what a railroad opening gives the editor, and it is a state rather
 * than a document: a new railroad is a new document and a new history, and an
 * undo that reached back into the script before it would be an edit nobody
 * made (`dccex-script.ts`).
 *
 * @param text the document it opens with
 * @param labelled what a screen reader calls it
 * @param typed what is told the whole text after every change
 */
export function editing(
  text: string,
  labelled: string,
  typed: (text: string) => void,
): EditorState {
  return EditorState.create({
    doc: text,
    extensions: [
      ...EDITS,
      EditorView.contentAttributes.of({
        "aria-label": labelled,
        spellcheck: "false",
        autocapitalize: "off",
      }),
      EditorView.updateListener.of((update) => {
        if (update.docChanged) {
          typed(update.state.doc.toString());
        }
      }),
    ],
  });
}
