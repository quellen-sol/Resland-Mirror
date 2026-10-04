import assert from "node:assert/strict";
import test from "node:test";
import {
  DEMO_LOOP_MS,
  DEMO_SCRIPT,
  DEMO_STATIC_FRAME,
  demoFrameAt,
} from "./live-demo.ts";

const STEP_MS = 25;
function* framesOverOneLoop() {
  for (let ms = 0; ms < DEMO_LOOP_MS; ms += STEP_MS) yield [ms, demoFrameAt(ms)];
}

test("the loop has a positive length", () => {
  assert.ok(DEMO_LOOP_MS > 0);
});

test("the loop opens on an empty window", () => {
  const f = demoFrameAt(0);
  assert.equal(f.questionVisible, false);
  assert.equal(f.answerVisible, false);
  assert.equal(f.optionsShown, 0);
  assert.equal(f.picked, null);
  assert.equal(f.actionsVisible, false);
  assert.equal(f.toastVisible, false);
  assert.equal(f.struck, false);
  assert.equal(f.typing, null);
});

test("Resland thinks before the question types out", () => {
  const firstVisible = [...framesOverOneLoop()].find(([, f]) => f.questionVisible);
  assert.ok(firstVisible, "the question never appears");
  const [, f] = firstVisible;
  assert.equal(f.thinking, true);
  assert.equal(f.question, "");
});

test("typed text is always a prefix of the script and never shrinks", () => {
  const prev = { question: "", answer: "" };
  for (const [ms, f] of framesOverOneLoop()) {
    for (const key of ["question", "answer"]) {
      assert.ok(DEMO_SCRIPT[key].startsWith(f[key]), `${key} at ${ms}ms`);
      assert.ok(f[key].length >= prev[key].length, `${key} shrank at ${ms}ms`);
      prev[key] = f[key];
    }
  }
});

test("every line finishes typing within the loop", () => {
  const last = demoFrameAt(DEMO_LOOP_MS - 1);
  assert.equal(last.question, DEMO_SCRIPT.question);
  assert.equal(last.answer, DEMO_SCRIPT.answer);
  assert.equal(last.optionsShown, DEMO_SCRIPT.options.length);
});

test("there are three options and the scripted pick is one of them", () => {
  assert.equal(DEMO_SCRIPT.options.length, 3);
  assert.equal(new Set(DEMO_SCRIPT.options).size, 3);
  assert.ok(DEMO_SCRIPT.picked >= 0 && DEMO_SCRIPT.picked < 3);
});

test("the options only use numbers from the bullet and the answer", () => {
  // The demo sells "nothing made up", so it can't invent a metric either.
  const numbers = (text) => new Set(text.match(/\d+/g) ?? []);
  const known = numbers(`${DEMO_SCRIPT.bullet} ${DEMO_SCRIPT.answer}`);
  for (const option of DEMO_SCRIPT.options) {
    for (const n of numbers(option)) assert.ok(known.has(n), `${n} in: ${option}`);
  }
});

test("options appear one at a time and the pick waits for all three", () => {
  let prev = 0;
  for (const [ms, f] of framesOverOneLoop()) {
    assert.ok(f.optionsShown >= prev && f.optionsShown <= prev + 1, `jumped at ${ms}ms`);
    prev = f.optionsShown;
    if (f.optionsShown > 0) assert.equal(f.struck, true, `options before strike at ${ms}ms`);
    if (f.picked !== null) {
      assert.equal(f.optionsShown, 3, `picked early at ${ms}ms`);
      assert.equal(f.picked, DEMO_SCRIPT.picked);
    }
  }
});

test("the caret only sits on the line that's typing", () => {
  for (const [ms, f] of framesOverOneLoop()) {
    if (f.typing === null) continue;
    const typed = f[f.typing];
    assert.ok(typed.length < DEMO_SCRIPT[f.typing].length, `caret on finished ${f.typing} at ${ms}ms`);
  }
  assert.ok([...framesOverOneLoop()].some(([, f]) => f.typing === "answer"));
});

test("things happen in order: question, answer, options, pick, accept, toast", () => {
  const firstMs = (pred) => [...framesOverOneLoop()].find(([, f]) => pred(f))?.[0];
  const order = [
    firstMs((f) => f.question === DEMO_SCRIPT.question),
    firstMs((f) => f.answerVisible),
    firstMs((f) => f.answer === DEMO_SCRIPT.answer),
    firstMs((f) => f.struck && f.optionsShown === 1),
    firstMs((f) => f.optionsShown === 3),
    firstMs((f) => f.actionsVisible),
    firstMs((f) => f.picked !== null),
    firstMs((f) => f.acceptPressed),
    firstMs((f) => f.toastVisible),
  ];
  assert.ok(order.every((ms) => ms !== undefined), `missing beat: ${order}`);
  for (let i = 1; i < order.length; i++) assert.ok(order[i] >= order[i - 1], `beat ${i} out of order: ${order}`);
});

test("once shown, a step stays up for the rest of the loop", () => {
  const keys = ["questionVisible", "answerVisible", "actionsVisible", "toastVisible", "struck"];
  const seen = new Set();
  for (const [ms, f] of framesOverOneLoop()) {
    for (const k of keys) {
      if (f[k]) seen.add(k);
      else assert.ok(!seen.has(k), `${k} disappeared at ${ms}ms`);
    }
  }
});

test("the loop repeats", () => {
  for (const ms of [0, 1234, DEMO_LOOP_MS - 1]) {
    assert.deepEqual(demoFrameAt(ms + DEMO_LOOP_MS), demoFrameAt(ms));
    assert.deepEqual(demoFrameAt(ms + 3 * DEMO_LOOP_MS), demoFrameAt(ms));
  }
});

test("the static frame shows the whole exchange, an option picked, waiting on Accept", () => {
  assert.equal(DEMO_STATIC_FRAME.questionVisible, true);
  assert.equal(DEMO_STATIC_FRAME.thinking, false);
  assert.equal(DEMO_STATIC_FRAME.question, DEMO_SCRIPT.question);
  assert.equal(DEMO_STATIC_FRAME.answer, DEMO_SCRIPT.answer);
  assert.equal(DEMO_STATIC_FRAME.optionsShown, 3);
  assert.equal(DEMO_STATIC_FRAME.picked, DEMO_SCRIPT.picked);
  assert.equal(DEMO_STATIC_FRAME.struck, true);
  assert.equal(DEMO_STATIC_FRAME.actionsVisible, true);
  assert.equal(DEMO_STATIC_FRAME.acceptPressed, false);
  assert.equal(DEMO_STATIC_FRAME.toastVisible, false);
  assert.equal(DEMO_STATIC_FRAME.typing, null);
});
