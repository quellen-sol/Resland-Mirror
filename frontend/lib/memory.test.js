import assert from "node:assert/strict";
import test from "node:test";
import {
  MAX_FACT_CHARS,
  MAX_TOPIC_CHARS,
  groupFactsByTopic,
  parseFactInput,
} from "./memory.ts";

const fact = (id, topic, content = `fact ${id}`) => ({
  id,
  topic,
  content,
  source: "TAILOR",
});

test("groupFactsByTopic sorts topics A-Z and facts oldest first", () => {
  assert.deepEqual(
    groupFactsByTopic([
      fact(3, "Engineer at Beta"),
      fact(5, "Engineer at Acme"),
      fact(1, "Engineer at Beta"),
    ]),
    [
      { topic: "Engineer at Acme", facts: [fact(5, "Engineer at Acme")] },
      {
        topic: "Engineer at Beta",
        facts: [fact(1, "Engineer at Beta"), fact(3, "Engineer at Beta")],
      },
    ],
  );
});

test("groupFactsByTopic leaves an empty bank empty", () => {
  assert.deepEqual(groupFactsByTopic([]), []);
});

test("parseFactInput trims a valid fact", () => {
  assert.deepEqual(parseFactInput("  General ", " Speaks Spanish. "), {
    ok: true,
    topic: "General",
    content: "Speaks Spanish.",
  });
});

test("parseFactInput accepts facts right at the limits", () => {
  const result = parseFactInput(
    "t".repeat(MAX_TOPIC_CHARS),
    "c".repeat(MAX_FACT_CHARS),
  );
  assert.equal(result.ok, true);
});

test("parseFactInput rejects blank, non-string, and oversized input", () => {
  for (const [topic, content] of [
    ["", "content"],
    ["General", "   "],
    [undefined, "content"],
    ["General", 42],
    ["t".repeat(MAX_TOPIC_CHARS + 1), "content"],
    ["General", "c".repeat(MAX_FACT_CHARS + 1)],
  ]) {
    const result = parseFactInput(topic, content);
    assert.equal(result.ok, false, `${topic} / ${content}`);
    assert.ok(result.error.length > 0);
  }
});
