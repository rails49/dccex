/**
 * The journal view's controls, mounted: what each one offers and what pressing
 * it hands up.
 *
 * The words and the periods are the reading module's and are run through it
 * (`tests/ui/test_incidents.py`); what is asserted here is that a press hands
 * its answer up and keeps none of its own, that the download points at the
 * face's own address, and that the clear asks before anything is asked of the
 * face (ADR-0006 d.2, #126).
 */

import { expect, test } from "vitest";

import { JOURNAL_PATH } from "../src/face.js";
import { CLEARS, WARNS } from "../src/incidents.js";
import { DccexControls } from "../src/ui/dccex-controls.js";
import { all, mounted, part, press, reads } from "./mounted.js";

/** The periods one journal offers: the three spans, and the two builds in it. */
const CHOICES = [
  "all",
  "last day",
  "last 7 days",
  "v5.6.4-rails49.6",
  "v5.6.4-rails49.1",
];

/** The controls, and everything a press of them handed up. */
async function controls(
  given: Partial<DccexControls> = {},
): Promise<{
  drawn: DccexControls;
  picked: string[];
  toggled: boolean[];
  reloaded: number;
  emptied: number;
}> {
  const picked: string[] = [];
  const toggled: boolean[] = [];
  let reloaded = 0;
  let emptied = 0;
  const drawn = new DccexControls();
  drawn.choices = CHOICES;
  drawn.choice = "all";
  drawn.picks = (choice: string) => {
    picked.push(choice);
  };
  drawn.toggles = (routine: boolean) => {
    toggled.push(routine);
  };
  drawn.reloads = () => {
    reloaded += 1;
  };
  drawn.empties = () => {
    emptied += 1;
  };
  Object.assign(drawn, given);
  await mounted(drawn);
  return {
    drawn,
    picked,
    toggled,
    // The two counts are read after the presses below rather than before them,
    // so they are read off the helper rather than copied out of it.
    get reloaded(): number {
      return reloaded;
    },
    get emptied(): number {
      return emptied;
    },
  };
}

test("the periods are one chooser: the spans and the builds in the file", async () => {
  const { drawn } = await controls();
  expect(all(drawn, ".choices option")).toStrictEqual(CHOICES);
});

test("the period being read is the one the chooser shows", async () => {
  const { drawn } = await controls({ choice: "last day" });
  expect((part(drawn, ".choices") as HTMLSelectElement).value).toBe("last day");
});

test("choosing a period hands it up and keeps none of its own", async () => {
  const { drawn, picked } = await controls();
  const chooser = part(drawn, ".choices") as HTMLSelectElement;
  chooser.value = "v5.6.4-rails49.6";
  chooser.dispatchEvent(new Event("change"));
  expect(picked).toStrictEqual(["v5.6.4-rails49.6"]);
  expect(drawn.choice).toBe("all");
});

test("the toggle hands up whether the routine lines are wanted", async () => {
  const { drawn, toggled } = await controls();
  const toggle = part(drawn, ".toggle") as HTMLInputElement;
  expect(toggle.checked).toBe(false);
  toggle.click();
  expect(toggled).toStrictEqual([true]);
});

test("a toggle the view says is on is drawn on", async () => {
  const { drawn } = await controls({ routine: true });
  expect((part(drawn, ".toggle") as HTMLInputElement).checked).toBe(true);
});

test("the reload asks the view for the journal again", async () => {
  const asked = await controls();
  press(asked.drawn, ".reloads");
  press(asked.drawn, ".reloads");
  expect(asked.reloaded).toBe(2);
});

test("the size is the file's, and blank where none was served", async () => {
  expect(reads((await controls({ bytes: 1500 })).drawn, ".size")).toBe("1.5 kB");
  expect(reads((await controls()).drawn, ".size")).toBe("");
});

test("the download is a link to the face's own address", async () => {
  const link = part((await controls()).drawn, ".downloads");
  expect(link.getAttribute("href")).toBe(JOURNAL_PATH);
  expect(link.hasAttribute("download")).toBe(true);
});

test("the clear asks first and nothing is asked of the face until it is answered", async () => {
  const asked = await controls();
  expect(reads(asked.drawn, ".clears")).toBe(CLEARS);
  press(asked.drawn, ".clears");
  await asked.drawn.updateComplete;
  expect(reads(asked.drawn, ".warns")).toBe(WARNS);
  expect(asked.emptied).toBe(0);
  press(asked.drawn, ".confirms");
  await asked.drawn.updateComplete;
  expect(asked.emptied).toBe(1);
  expect(asked.drawn.renderRoot.querySelector(".warning")).toBeNull();
});

test("a clear declined asks nothing and leaves no sentence behind it", async () => {
  const asked = await controls();
  press(asked.drawn, ".clears");
  await asked.drawn.updateComplete;
  press(asked.drawn, ".cancels");
  await asked.drawn.updateComplete;
  expect(asked.emptied).toBe(0);
  expect(asked.drawn.renderRoot.querySelector(".warning")).toBeNull();
  expect(asked.drawn.renderRoot.querySelector(".says")).toBeNull();
});

test("what became of a clear is the sentence the view hands down", async () => {
  const said = "this mirror was given no journal";
  expect(reads((await controls({ says: said })).drawn, ".says")).toBe(said);
});

test("controls nobody handed anything to press nothing", async () => {
  // Which period is read and when the journal is asked for are the view's: a
  // control that answered for itself would draw one period while the table
  // counted another.
  const drawn = await mounted(new DccexControls());
  press(drawn, ".reloads");
  press(drawn, ".clears");
  await drawn.updateComplete;
  press(drawn, ".confirms");
  expect(all(drawn, ".choices option")).toStrictEqual([]);
});
