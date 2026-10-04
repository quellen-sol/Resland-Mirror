// Checks every LeetCode link in the DSA study center against LeetCode's
// public GraphQL API: the problem exists, isn't premium-only, the "LeetCode N"
// label has the right number, and practice difficulties match. Needs the
// network, so it's opt-in: `pnpm test:dsa-links` (DSA_ONLY=slug,... works).
import assert from "node:assert/strict";
import { describe, test } from "node:test";
import { DSA_TOPICS } from "../content/dsa/index.ts";

const LEETCODE = /^https:\/\/leetcode\.com\/problems\/([a-z0-9-]+)\/$/;

const only = process.env.DSA_ONLY?.split(",").filter(Boolean);
const topics = DSA_TOPICS.filter((t) => !only || only.includes(t.slug));

/** Every link with what the page claims about it. */
const links = topics.flatMap((topic) => [
  ...topic.problems
    .filter((p) => p.link)
    .map((p) => ({
      where: `${topic.slug}/${p.id}`,
      url: p.link.url,
      label: p.link.label,
      difficulty: p.difficulty,
    })),
  ...topic.practice.map((p) => ({
    where: `${topic.slug} practice "${p.title}"`,
    url: p.url,
    difficulty: p.difficulty,
  })),
]);

const lookups = new Map();
function lookup(slug) {
  if (!lookups.has(slug)) {
    lookups.set(
      slug,
      fetch("https://leetcode.com/graphql", {
        method: "POST",
        headers: { "Content-Type": "application/json", Referer: "https://leetcode.com" },
        body: JSON.stringify({
          query:
            "query q($s: String!) { question(titleSlug: $s) { questionFrontendId title difficulty isPaidOnly } }",
          variables: { s: slug },
        }),
      })
        .then((r) => r.json())
        .then((r) => r.data.question),
    );
  }
  return lookups.get(slug);
}

describe("dsa links", { concurrency: 4 }, () => {
  for (const link of links) {
    const slug = link.url.match(LEETCODE)?.[1];
    test(`${link.where} -> ${link.url}`, async () => {
      if (!link.url.includes("leetcode.com")) return; // Other sites aren't checked.
      assert.ok(slug, "LeetCode links look like https://leetcode.com/problems/<slug>/");
      const q = await lookup(slug);
      assert.ok(q, "no such LeetCode problem");
      assert.equal(q.isPaidOnly, false, `${q.title} is premium-only`);
      assert.equal(q.difficulty.toUpperCase(), link.difficulty, `${q.title} difficulty`);
      if (link.label) assert.equal(link.label, `LeetCode ${q.questionFrontendId}`);
    });
  }
});
