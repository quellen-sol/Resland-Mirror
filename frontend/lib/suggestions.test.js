import assert from "node:assert/strict";
import test from "node:test";
import { moreOptionsMessage, parseSuggestionResult } from "./suggestions.ts";

test("parseSuggestionResult reads each bullet's options", () => {
  assert.deepEqual(
    parseSuggestionResult(
      JSON.stringify([
        { bullet_id: 1, options: ["a", "b", "c"] },
        { bullet_id: 2, options: ["d", "e", "f"] },
      ]),
    ),
    [
      { bullet_id: 1, options: ["a", "b", "c"] },
      { bullet_id: 2, options: ["d", "e", "f"] },
    ],
  );
});

test("parseSuggestionResult lifts a legacy single suggestion into one option", () => {
  assert.deepEqual(
    parseSuggestionResult(
      JSON.stringify([{ bullet_id: 4, suggestion: "old style" }]),
    ),
    [{ bullet_id: 4, options: ["old style"] }],
  );
});

test("parseSuggestionResult drops blank options and malformed entries", () => {
  assert.deepEqual(
    parseSuggestionResult(
      JSON.stringify([
        { bullet_id: 1, options: ["a", "  ", 7, "c"] },
        { bullet_id: "2", options: ["x"] },
        { options: ["no id"] },
        { bullet_id: 3, options: [] },
        null,
      ]),
    ),
    [{ bullet_id: 1, options: ["a", "c"] }],
  );
});

test("parseSuggestionResult is empty for missing or unparseable results", () => {
  assert.deepEqual(parseSuggestionResult(null), []);
  assert.deepEqual(parseSuggestionResult(undefined), []);
  assert.deepEqual(parseSuggestionResult(""), []);
  assert.deepEqual(parseSuggestionResult("{not json"), []);
  assert.deepEqual(parseSuggestionResult(JSON.stringify({ bullet_id: 1 })), []);
});

test("moreOptionsMessage sends the user's guidance when given", () => {
  assert.equal(moreOptionsMessage("  lead with the cost savings "), "lead with the cost savings");
});

test("moreOptionsMessage falls back to a plain request for new options", () => {
  const msg = moreOptionsMessage("   ");
  assert.match(msg, /three/i);
  assert.match(msg, /different/i);
});
