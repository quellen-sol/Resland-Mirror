import assert from "node:assert/strict";
import test from "node:test";
import {
  COMPONENT_PALETTE,
  arrowGeometry,
  PHASES,
  PHASE_LABELS,
  advanceLabel,
  dimensionAverages,
  fmtClock,
  gradeTone,
  layoutReferenceDesign,
  nextPhase,
  phaseElapsedSeconds,
  weakestDimension,
} from "./system-design.ts";

test("fmtClock runs like a stopwatch", () => {
  assert.equal(fmtClock(0), "0:00");
  assert.equal(fmtClock(45), "0:45");
  assert.equal(fmtClock(365), "6:05");
  assert.equal(fmtClock(3723), "1:02:03");
  assert.equal(fmtClock(-10), "0:00");
  assert.equal(fmtClock(59.9), "0:59");
});

test("phases advance in order and stop at feedback", () => {
  assert.equal(nextPhase("REQUIREMENTS"), "ESTIMATION");
  assert.equal(nextPhase("HIGH_LEVEL_DESIGN"), "DEEP_DIVE");
  assert.equal(nextPhase("DEEP_DIVE"), "FEEDBACK");
  assert.equal(nextPhase("FEEDBACK"), null);
  for (const phase of PHASES) assert.ok(PHASE_LABELS[phase]);
});

test("advance buttons say where they go", () => {
  assert.equal(advanceLabel("REQUIREMENTS"), "Move to Estimation");
  assert.equal(advanceLabel("ESTIMATION"), "Move to High-Level Design");
  assert.equal(advanceLabel("HIGH_LEVEL_DESIGN"), "Submit Design");
  assert.equal(advanceLabel("DEEP_DIVE"), null);
  assert.equal(advanceLabel("FEEDBACK"), null);
});

test("phase timer corrects for clock skew", () => {
  const started = "2026-10-01T12:00:00.000Z";
  const now = Date.parse("2026-10-01T12:05:00.000Z");
  assert.equal(phaseElapsedSeconds(started, 0, now), 300);
  // Client clock 30s behind the server.
  assert.equal(phaseElapsedSeconds(started, 30_000, now), 330);
  // Never negative, even with a client clock ahead of the server.
  assert.equal(phaseElapsedSeconds(started, -600_000, now), 0);
});

test("grade tones", () => {
  assert.equal(gradeTone("A+"), "great");
  assert.equal(gradeTone("A-"), "great");
  assert.equal(gradeTone("B+"), "good");
  assert.equal(gradeTone("B-"), "good");
  assert.equal(gradeTone("C"), "fair");
  assert.equal(gradeTone("D"), "poor");
  assert.equal(gradeTone("F"), "poor");
  assert.equal(gradeTone(null), "poor");
});

test("reference layout puts each component right of what points at it", () => {
  const boxes = layoutReferenceDesign(
    [{ id: "client" }, { id: "lb" }, { id: "api" }, { id: "db" }, { id: "cache" }],
    [
      { source: "client", target: "lb" },
      { source: "lb", target: "api" },
      { source: "api", target: "db" },
      { source: "api", target: "cache" },
    ],
  );
  const at = Object.fromEntries(boxes.map((b) => [b.id, b]));
  assert.equal(boxes.length, 5);
  assert.ok(at.client.x < at.lb.x);
  assert.ok(at.lb.x < at.api.x);
  assert.ok(at.api.x < at.db.x);
  assert.equal(at.db.x, at.cache.x);
  assert.notEqual(at.db.y, at.cache.y);
  for (const b of boxes) assert.ok(b.width > 0 && b.height > 0);
});

test("reference layout survives cycles and strays", () => {
  const boxes = layoutReferenceDesign(
    [{ id: "a" }, { id: "b" }, { id: "lonely" }],
    [
      { source: "a", target: "b" },
      { source: "b", target: "a" },
      { source: "a", target: "ghost" },
    ],
  );
  assert.deepEqual(boxes.map((b) => b.id).sort(), ["a", "b", "lonely"]);
  const ys = new Set(boxes.map((b) => `${b.x},${b.y}`));
  assert.equal(ys.size, 3, "no two boxes overlap");
});

test("arrows run edge to edge between laid-out boxes", () => {
  const box = (id, x, y) => ({ id, x, y, width: 100, height: 50 });
  // Target in the next column: right-middle to left-middle.
  assert.deepEqual(arrowGeometry(box("a", 0, 0), box("b", 250, 100)), {
    x: 100,
    y: 25,
    points: [
      [0, 0],
      [150, 100],
    ],
  });
  // Target to the left.
  assert.deepEqual(arrowGeometry(box("a", 250, 0), box("b", 0, 0)).points[1], [
    -150, 0,
  ]);
  // Skipping columns arcs over the boxes in between.
  const skip = arrowGeometry(box("a", 0, 0), box("b", 900, 0));
  assert.equal(skip.points.length, 3);
  assert.ok(skip.y + skip.points[1][1] < 0, "midpoint rises above the row");
  assert.deepEqual(skip.points[2], [800, 0]);
  // Same column: bottom-middle to top-middle, and back up.
  const down = arrowGeometry(box("a", 0, 0), box("b", 0, 200));
  assert.deepEqual([down.x, down.y, down.points[1]], [50, 50, [0, 150]]);
  const up = arrowGeometry(box("a", 0, 200), box("b", 0, 0));
  assert.deepEqual([up.x, up.y, up.points[1]], [50, 200, [0, -150]]);
});

const report = (scores) => ({
  dimensions: Object.entries(scores).map(([key, score]) => ({
    key,
    label: key.toUpperCase(),
    weight: 0.1,
    score,
    evidence: "",
    feedback: "",
  })),
});

test("dimension averages follow rubric order and skip ungraded interviews", () => {
  const avgs = dimensionAverages([
    report({ requirements: 4, deep_dive: 2 }),
    null,
    report({ requirements: 2, deep_dive: 3, estimation: 5 }),
  ]);
  assert.deepEqual(
    avgs.map((a) => [a.key, a.average, a.count]),
    [
      ["requirements", 3, 2],
      ["estimation", 5, 1],
      ["deep_dive", 2.5, 2],
    ],
  );
  assert.equal(weakestDimension(avgs).key, "deep_dive");
  assert.equal(weakestDimension([]), null);
});

test("palette kinds are unique", () => {
  const kinds = COMPONENT_PALETTE.map((p) => p.kind);
  assert.equal(new Set(kinds).size, kinds.length);
});
