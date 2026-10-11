import assert from "node:assert/strict";
import test from "node:test";
import { parseTailoredContent } from "./tailored.ts";

const experience = (extra = {}) => ({
  company_name: "Acme",
  title: "Engineer",
  start_date: "Jan 2020",
  end_date: null,
  bullets: ["Shipped it"],
  ...extra,
});

test("parseTailoredContent keeps an experience's location", () => {
  const parsed = parseTailoredContent(
    JSON.stringify({
      summary: null,
      experiences: [experience({ location: "Denver, CO" })],
      skill_groups: [],
    }),
  );
  assert.equal(parsed?.experiences[0].location, "Denver, CO");
});

test("parseTailoredContent reads older snapshots without a location as null", () => {
  const parsed = parseTailoredContent(
    JSON.stringify({
      summary: "Hi",
      experiences: [experience()],
      skill_groups: [],
    }),
  );
  assert.deepEqual(parsed?.experiences, [
    {
      company_name: "Acme",
      title: "Engineer",
      location: null,
      start_date: "Jan 2020",
      end_date: null,
      bullets: ["Shipped it"],
    },
  ]);
});

test("parseTailoredContent rejects unreadable content", () => {
  assert.equal(parseTailoredContent("not json"), null);
  assert.equal(parseTailoredContent(JSON.stringify({ summary: null })), null);
});
