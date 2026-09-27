import assert from "node:assert/strict";
import test from "node:test";
import { groupSkills, groupsToRows, rowsToGroups } from "./skills.ts";

test("groupSkills folds rows into first-appearance groups", () => {
  assert.deepEqual(
    groupSkills([
      { name: "Go", category: "Langs" },
      { name: "Git", category: null },
      { name: "Rust", category: "Langs" },
      { name: "AWS", category: "Cloud" },
    ]),
    [
      { category: "Langs", skills: ["Go", "Rust"] },
      { category: null, skills: ["Git"] },
      { category: "Cloud", skills: ["AWS"] },
    ],
  );
});

test("groupSkills trims blanks and normalizes empty categories to null", () => {
  assert.deepEqual(
    groupSkills([
      { name: "  ", category: "X" },
      { name: "TS", category: "  " },
    ]),
    [{ category: null, skills: ["TS"] }],
  );
});

test("rowsToGroups returns one ungrouped group when empty", () => {
  const groups = rowsToGroups([]);
  assert.equal(groups.length, 1);
  assert.equal(groups[0].category, null);
  assert.deepEqual(groups[0].skills, []);
  assert.ok(groups[0].id);
});

test("groupsToRows flattens in order and drops duplicate names", () => {
  const rows = groupsToRows([
    { id: "a", category: "Langs", skills: ["Go", "Rust"] },
    { id: "b", category: null, skills: ["Go", "Git"] },
    { id: "c", category: "  ", skills: ["TS"] },
  ]);
  assert.deepEqual(rows, [
    { name: "Go", category: "Langs" },
    { name: "Rust", category: "Langs" },
    { name: "Git", category: null },
    { name: "TS", category: null },
  ]);
});

test("rowsToGroups -> groupsToRows round-trips", () => {
  const rows = [
    { name: "Go", category: "Langs" },
    { name: "Git", category: null },
  ];
  assert.deepEqual(groupsToRows(rowsToGroups(rows)), rows);
});
