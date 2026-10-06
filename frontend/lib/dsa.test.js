import assert from "node:assert/strict";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";
import {
  DEFAULT_DSA_LANGUAGE,
  DSA_CATEGORIES,
  DSA_LANGUAGE_NAMES,
  DSA_LANGUAGES,
  META_DESCRIPTION_MAX,
  coerceDsaLanguage,
  groupTopicsByCategory,
  orderTopics,
  parseInline,
  parseProgressUpdate,
  summarizeProgress,
  toPlainText,
  topicDependents,
  topicMetaDescription,
  topicNeighbors,
} from "./dsa.ts";
import { DSA_TOPICS } from "../content/dsa/index.ts";

const CONTENT_DIR = new URL("../content/dsa/", import.meta.url).pathname;

/** Minimal topic for the helper tests — only the fields they read. */
function fixture(slug, category) {
  return { slug, category, title: slug };
}

// ---------------------------------------------------------------------------
// Navigation

test("orderTopics sorts by category order and keeps listed order within one", () => {
  const topics = [
    fixture("dp-1d", "dp"),
    fixture("big-o", "foundations"),
    fixture("tries", "trees"),
    fixture("arrays-hashing", "foundations"),
  ];
  assert.deepEqual(
    orderTopics(topics).map((t) => t.slug),
    ["big-o", "arrays-hashing", "tries", "dp-1d"],
  );
});

test("groupTopicsByCategory follows DSA_CATEGORIES and drops empty ones", () => {
  const groups = groupTopicsByCategory([
    fixture("tries", "trees"),
    fixture("big-o", "foundations"),
    fixture("heaps", "trees"),
  ]);
  assert.deepEqual(
    groups.map((g) => [g.category.id, g.topics.map((t) => t.slug)]),
    [
      ["foundations", ["big-o"]],
      ["trees", ["tries", "heaps"]],
    ],
  );
});

test("topicNeighbors walks study order across category boundaries", () => {
  const topics = [
    fixture("tries", "trees"),
    fixture("big-o", "foundations"),
    fixture("two-pointers", "techniques"),
  ];
  const first = topicNeighbors(topics, "big-o");
  assert.equal(first.prev, null);
  assert.equal(first.next?.slug, "two-pointers");

  const middle = topicNeighbors(topics, "two-pointers");
  assert.equal(middle.prev?.slug, "big-o");
  assert.equal(middle.next?.slug, "tries");

  const last = topicNeighbors(topics, "tries");
  assert.equal(last.prev?.slug, "two-pointers");
  assert.equal(last.next, null);

  assert.deepEqual(topicNeighbors(topics, "nope"), { prev: null, next: null });
});

test("topicDependents lists topics that build on one, in study order", () => {
  const topics = [
    { ...fixture("tries", "trees"), prerequisites: ["binary-trees"] },
    { ...fixture("binary-trees", "trees"), prerequisites: ["recursion"] },
    { ...fixture("graph-traversal", "graphs"), prerequisites: ["recursion", "stacks-queues"] },
    { ...fixture("recursion", "foundations"), prerequisites: [] },
    { ...fixture("dp-1d", "dp"), prerequisites: ["recursion"] },
  ];
  assert.deepEqual(
    topicDependents(topics, "recursion").map((t) => t.slug),
    ["binary-trees", "graph-traversal", "dp-1d"],
  );
  assert.deepEqual(topicDependents(topics, "dp-1d"), []);
});

// ---------------------------------------------------------------------------
// Search metadata

function problem(title) {
  return { title };
}

test("topicMetaDescription adds the worked problems that fit", () => {
  assert.equal(
    topicMetaDescription({
      summary: "Halve a sorted range every step.",
      problems: [problem("Lower Bound"), problem("Koko Eating Bananas")],
    }),
    "Halve a sorted range every step. Worked problems: Lower Bound and Koko Eating Bananas.",
  );
  assert.equal(
    topicMetaDescription({
      summary: "Short.",
      problems: [problem("A"), problem("B"), problem("C")],
    }),
    "Short. Worked problems: A, B and C.",
  );
  assert.equal(
    topicMetaDescription({ summary: "One.", problems: [problem("Two Sum")] }),
    "One. Worked problem: Two Sum.",
  );
});

test("topicMetaDescription drops problems from the end to stay in bounds", () => {
  const summary = "x".repeat(110) + ".";
  const d = topicMetaDescription({
    summary,
    problems: [problem("Group Anagrams"), problem("Longest Consecutive Sequence")],
  });
  assert.equal(d, `${summary} Worked problem: Group Anagrams.`);
  assert.ok(d.length <= META_DESCRIPTION_MAX);

  const full = "y".repeat(150) + ".";
  assert.equal(topicMetaDescription({ summary: full, problems: [problem("Two Sum")] }), full);
});

test("toPlainText strips code, bold and link markup", () => {
  assert.equal(
    toPlainText("Move `left` **inward**, see [Binary Search](/dsa/binary-search)."),
    "Move left inward, see Binary Search.",
  );
  assert.equal(toPlainText("O(n) time"), "O(n) time");
});

// ---------------------------------------------------------------------------
// Inline markup

test("parseInline splits code, bold and links out of plain text", () => {
  assert.deepEqual(
    parseInline("Move `left` **inward**, see [Binary Search](/dsa/binary-search)."),
    [
      { type: "text", text: "Move " },
      { type: "code", text: "left" },
      { type: "text", text: " " },
      { type: "strong", text: "inward" },
      { type: "text", text: ", see " },
      { type: "link", text: "Binary Search", href: "/dsa/binary-search" },
      { type: "text", text: "." },
    ],
  );
});

test("parseInline leaves plain text as a single token", () => {
  assert.deepEqual(parseInline("O(n) time"), [{ type: "text", text: "O(n) time" }]);
  assert.deepEqual(parseInline(""), []);
});

test("parseInline keeps markup characters inside code spans literal", () => {
  assert.deepEqual(parseInline("`a**b[0]`"), [{ type: "code", text: "a**b[0]" }]);
});

test("parseInline treats unclosed markers as literal text", () => {
  assert.deepEqual(parseInline("2 * 3 and `x"), [
    { type: "text", text: "2 * 3 and `x" },
  ]);
  assert.deepEqual(parseInline("**open"), [{ type: "text", text: "**open" }]);
  assert.deepEqual(parseInline("arr[i] (not a link)"), [
    { type: "text", text: "arr[i] (not a link)" },
  ]);
});

// ---------------------------------------------------------------------------
// Progress

const KNOWN = new Set(["two-pointers", "tries"]);

test("parseProgressUpdate accepts a known topic and a boolean", () => {
  assert.deepEqual(
    parseProgressUpdate({ topic: "tries", studied: true }, KNOWN),
    { topic: "tries", studied: true },
  );
  assert.deepEqual(
    parseProgressUpdate({ topic: "two-pointers", studied: false, extra: 1 }, KNOWN),
    { topic: "two-pointers", studied: false },
  );
});

test("parseProgressUpdate rejects malformed bodies and unknown topics", () => {
  for (const body of [
    null,
    undefined,
    "tries",
    [],
    {},
    { topic: "tries" },
    { topic: "tries", studied: "yes" },
    { topic: 4, studied: true },
    { topic: "graphs-101", studied: true },
  ]) {
    assert.equal(parseProgressUpdate(body, KNOWN), null, JSON.stringify(body));
  }
});

test("summarizeProgress counts per category and ignores stale slugs", () => {
  const topics = [
    fixture("big-o", "foundations"),
    fixture("arrays-hashing", "foundations"),
    fixture("tries", "trees"),
  ];
  assert.deepEqual(
    summarizeProgress(topics, ["big-o", "tries", "tries", "removed-topic"]),
    {
      done: 2,
      total: 3,
      byCategory: {
        foundations: { done: 1, total: 2 },
        trees: { done: 1, total: 1 },
      },
    },
  );
  assert.deepEqual(summarizeProgress([], new Set()), {
    done: 0,
    total: 0,
    byCategory: {},
  });
});

test("DSA_LANGUAGE_NAMES lists every language for copy", () => {
  for (const l of DSA_LANGUAGES) assert.ok(DSA_LANGUAGE_NAMES.includes(l.label), l.label);
  assert.match(DSA_LANGUAGE_NAMES, /, [^,]+ and [^,]+$/);
});

test("the default language leads the tabs", () => {
  assert.equal(DSA_LANGUAGES[0].id, DEFAULT_DSA_LANGUAGE);
});

test("coerceDsaLanguage falls back to the default", () => {
  assert.equal(coerceDsaLanguage("go"), "go");
  assert.equal(coerceDsaLanguage("csharp"), "csharp");
  assert.equal(coerceDsaLanguage("rust"), DEFAULT_DSA_LANGUAGE);
  assert.equal(coerceDsaLanguage(null), DEFAULT_DSA_LANGUAGE);
});

// ---------------------------------------------------------------------------
// Content integrity — every topic in content/dsa/index.ts

const SLUG = /^[a-z0-9]+(-[a-z0-9]+)*$/;
const slugs = new Set(DSA_TOPICS.map((t) => t.slug));
const categoryIds = new Set(DSA_CATEGORIES.map((c) => c.id));

/** Every prose string in a topic, for the markup checks. */
function proseOf(topic) {
  const blocks = [
    ...topic.overview,
    ...topic.template.explanation,
    ...topic.problems.flatMap((p) => [...p.statement, ...p.explanation]),
  ];
  return [
    topic.summary,
    ...topic.signals,
    ...topic.pitfalls,
    ...blocks.flatMap((b) =>
      b.type === "list"
        ? b.items
        : b.type === "diagram"
          ? (b.caption ? [b.caption] : [])
          : [b.text],
    ),
  ];
}

/** Diagram bodies: shown verbatim, so no inline markup, but still copy. */
function diagramsOf(topic) {
  return [
    ...topic.overview,
    ...topic.template.explanation,
    ...topic.problems.flatMap((p) => [...p.statement, ...p.explanation]),
  ].flatMap((b) => (b.type === "diagram" ? [b.text] : []));
}

test("the registry is non-empty with unique, well-formed slugs", () => {
  assert.ok(DSA_TOPICS.length > 0, "content/dsa/index.ts lists no topics");
  assert.equal(slugs.size, DSA_TOPICS.length, "duplicate topic slugs");
  for (const t of DSA_TOPICS) assert.match(t.slug, SLUG);
});

test("every category has at least one topic", () => {
  const used = new Set(DSA_TOPICS.map((t) => t.category));
  for (const c of DSA_CATEGORIES) assert.ok(used.has(c.id), `${c.id} is empty`);
});

test("every topic directory is registered", () => {
  const dirs = readdirSync(CONTENT_DIR, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name);
  for (const dir of dirs) assert.ok(slugs.has(dir), `${dir}/ isn't in index.ts`);
});

for (const topic of DSA_TOPICS) {
  test(`topic ${topic.slug} is complete and consistent`, () => {
    assert.ok(categoryIds.has(topic.category), `unknown category ${topic.category}`);
    for (const field of ["title", "summary"]) {
      assert.ok(topic[field].trim(), `${field} is empty`);
    }
    assert.ok(topic.summary.length <= 160, "summary is too long for a meta description");
    assert.ok(topic.seoTitle.trim(), "seoTitle is empty");
    assert.ok(topic.seoTitle.length <= 55, `seoTitle is ${topic.seoTitle.length} characters, over 55`);
    assert.notEqual(topic.seoTitle, topic.title, "seoTitle should say more than the title");
    assert.ok(topicMetaDescription(topic).length <= META_DESCRIPTION_MAX);
    assert.ok(topic.overview.length > 0, "no overview");
    assert.ok(topic.signals.length > 0, "no signals");
    assert.ok(topic.complexity.length > 0, "no complexity rows");
    assert.ok(topic.pitfalls.length > 0, "no pitfalls");
    assert.ok(
      topic.problems.length >= 1 && topic.problems.length <= 3,
      "expected 1-3 worked problems",
    );

    for (const slug of topic.prerequisites) {
      assert.ok(slugs.has(slug), `unknown prerequisite ${slug}`);
      assert.notEqual(slug, topic.slug, "lists itself as a prerequisite");
    }

    const examples = [topic.template, ...topic.problems];
    const ids = examples.map((e) => e.id);
    assert.equal(new Set(ids).size, ids.length, "duplicate example ids");
    for (const example of examples) {
      assert.match(example.id, SLUG);
      assert.ok(example.title.trim() && example.time && example.space);
      assert.ok(example.explanation.length > 0, `${example.id} has no explanation`);
      const dir = join(CONTENT_DIR, topic.slug, example.id);
      for (const file of [...DSA_LANGUAGES.map((l) => l.file), "expected.txt"]) {
        assert.ok(existsSync(join(dir, file)), `missing ${topic.slug}/${example.id}/${file}`);
      }
      assert.ok(
        readFileSync(join(dir, "expected.txt"), "utf8").trim(),
        `${example.id}/expected.txt is empty`,
      );
    }
    const folders = readdirSync(join(CONTENT_DIR, topic.slug), { withFileTypes: true })
      .filter((d) => d.isDirectory())
      .map((d) => d.name);
    for (const folder of folders) {
      assert.ok(ids.includes(folder), `${topic.slug}/${folder}/ isn't a registered example`);
    }
    for (const problem of topic.problems) {
      assert.ok(problem.statement.length > 0, `${problem.id} has no statement`);
      if (problem.link) assert.match(problem.link.url, /^https:\/\//);
    }
    for (const link of topic.practice) assert.match(link.url, /^https:\/\//);

    // House style for user-facing copy: plain sentences, no "X — Y".
    const shown = [
      topic.title,
      topic.seoTitle,
      ...proseOf(topic),
      ...diagramsOf(topic),
      ...examples.map((e) => e.title),
      ...examples.flatMap((e) =>
        DSA_LANGUAGES.map((l) => readFileSync(join(CONTENT_DIR, topic.slug, e.id, l.file), "utf8")),
      ),
    ];
    for (const text of shown) assert.ok(!text.includes("—"), `em dash in: ${text.slice(0, 80)}`);

    for (const text of proseOf(topic)) {
      for (const token of parseInline(text)) {
        if (token.type === "link" && token.href.startsWith("/")) {
          const [, target] = token.href.match(/^\/dsa\/([^#?]+)/) ?? [];
          assert.ok(slugs.has(target), `broken internal link ${token.href}`);
        }
        if (token.type === "text") {
          assert.doesNotMatch(token.text, /`|\*\*/, `unbalanced markup in: ${text}`);
        }
      }
    }
  });
}
