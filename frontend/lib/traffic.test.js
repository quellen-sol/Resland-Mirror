import assert from "node:assert/strict";
import test from "node:test";
import {
  classifySource,
  coerceTrafficRange,
  isLikelyBot,
  isTrackedPath,
  normalizePath,
  parsePageView,
  summarizeTraffic,
  trafficRangeStart,
} from "./traffic.ts";

const HOST = "resland.org";
const VISIT = "0b6c2f0e-3f43-4d0a-9a51-6c1f0d0e9a11";

// ---------------------------------------------------------------------------
// Paths

test("normalizePath masks ids in dynamic routes", () => {
  assert.equal(normalizePath("/tailored/3f2a9c"), "/tailored/[id]");
  assert.equal(normalizePath("/system-design/abc-123"), "/system-design/[id]");
  assert.equal(normalizePath("/tailored"), "/tailored");
  assert.equal(normalizePath("/system-design"), "/system-design");
});

test("normalizePath keeps public paths and drops a trailing slash", () => {
  assert.equal(normalizePath("/"), "/");
  assert.equal(normalizePath("/dsa/binary-search"), "/dsa/binary-search");
  assert.equal(normalizePath("/help/"), "/help");
});

test("normalizePath rejects anything that isn't a plain path", () => {
  for (const bad of ["", "help", "https://evil.example/", "/a b", "/<script>", "/x?y=1", `/${"a".repeat(200)}`, 42, null]) {
    assert.equal(normalizePath(bad), null, String(bad));
  }
});

test("isTrackedPath skips admin, auth, API and maintenance routes", () => {
  for (const path of ["/", "/help", "/dsa", "/dsa/tries", "/dashboard", "/onboarding", "/tailored/[id]"]) {
    assert.equal(isTrackedPath(path), true, path);
  }
  for (const path of ["/admin", "/auth/login", "/api/dsa/progress", "/maintenance"]) {
    assert.equal(isTrackedPath(path), false, path);
  }
});

// ---------------------------------------------------------------------------
// Sources

test("classifySource recognizes search engines, including Google's app", () => {
  for (const [referrer, name] of [
    ["https://www.google.com/", "google"],
    ["https://www.google.co.uk/", "google"],
    ["https://www.bing.com/search?q=x", "bing"],
    ["https://duckduckgo.com/", "duckduckgo"],
    ["https://search.brave.com/search?q=x", "brave"],
    ["android-app://com.google.android.googlequicksearchbox/", "google"],
  ]) {
    assert.deepEqual(classifySource({ referrer, siteHost: HOST }), { source: "SEARCH", name }, referrer);
  }
});

test("classifySource tells AI assistants apart from their parent's search", () => {
  for (const [referrer, name] of [
    ["https://chatgpt.com/", "chatgpt"],
    ["https://www.perplexity.ai/", "perplexity"],
    ["https://claude.ai/", "claude"],
    ["https://gemini.google.com/app", "gemini"],
    ["https://copilot.microsoft.com/", "copilot"],
  ]) {
    assert.deepEqual(classifySource({ referrer, siteHost: HOST }), { source: "AI", name }, referrer);
  }
});

test("classifySource recognizes social sites and keeps other hosts as referrals", () => {
  assert.deepEqual(classifySource({ referrer: "https://news.ycombinator.com/item?id=1", siteHost: HOST }), { source: "SOCIAL", name: "hacker news" });
  assert.deepEqual(classifySource({ referrer: "https://old.reddit.com/r/leetcode", siteHost: HOST }), { source: "SOCIAL", name: "reddit" });
  assert.deepEqual(classifySource({ referrer: "https://t.co/abc", siteHost: HOST }), { source: "SOCIAL", name: "x" });
  assert.deepEqual(classifySource({ referrer: "https://www.example.dev/post", siteHost: HOST }), { source: "REFERRAL", name: "example.dev" });
});

test("classifySource: no referrer is direct, our own host is internal", () => {
  assert.deepEqual(classifySource({ siteHost: HOST }), { source: "DIRECT", name: null });
  assert.deepEqual(classifySource({ referrer: "", siteHost: HOST }), { source: "DIRECT", name: null });
  assert.deepEqual(classifySource({ referrer: "not a url", siteHost: HOST }), { source: "DIRECT", name: null });
  assert.deepEqual(classifySource({ referrer: "https://resland.org/help", siteHost: HOST }), { source: "INTERNAL", name: null });
  assert.deepEqual(classifySource({ referrer: "https://www.resland.org/", siteHost: HOST }), { source: "INTERNAL", name: null });
  assert.deepEqual(classifySource({ referrer: "https://resland.us.auth0.com/u/login", siteHost: HOST }), { source: "INTERNAL", name: null });
});

test("classifySource lets utm_source name the source", () => {
  assert.deepEqual(classifySource({ utmSource: "Reddit", siteHost: HOST }), { source: "SOCIAL", name: "reddit" });
  assert.deepEqual(classifySource({ utmSource: "newsletter", referrer: "https://www.google.com/", siteHost: HOST }), { source: "REFERRAL", name: "newsletter" });
});

// ---------------------------------------------------------------------------
// Beacons

test("parsePageView builds a first-page row from the referrer", () => {
  assert.deepEqual(
    parsePageView({ visit: VISIT, path: "/dsa/tries/", referrer: "https://www.google.com/", utm_campaign: "launch" }, HOST),
    { visit_id: VISIT, path: "/dsa/tries", prev_path: null, source: "SEARCH", source_name: "google", utm_campaign: "launch" },
  );
});

test("parsePageView marks later pages in a visit internal", () => {
  assert.deepEqual(
    parsePageView({ visit: VISIT, path: "/tailored/9f8e", prev: "/dashboard", referrer: "https://www.google.com/" }, HOST),
    { visit_id: VISIT, path: "/tailored/[id]", prev_path: "/dashboard", source: "INTERNAL", source_name: null, utm_campaign: null },
  );
});

test("parsePageView rejects malformed bodies and untracked pages", () => {
  for (const body of [
    null,
    "x",
    {},
    { visit: VISIT },
    { visit: "short", path: "/" },
    { visit: "has spaces in it ok", path: "/" },
    { visit: VISIT, path: "nope" },
    { visit: VISIT, path: "/admin" },
    { visit: VISIT, path: "/", prev: 7 },
  ]) {
    assert.equal(parsePageView(body, HOST), null, JSON.stringify(body));
  }
});

test("parsePageView trims long free-text fields", () => {
  const row = parsePageView({ visit: VISIT, path: "/", utm_campaign: "c".repeat(500), utm_source: "s".repeat(500) }, HOST);
  assert.equal(row.utm_campaign.length, 100);
  assert.equal(row.source_name.length, 100);
});

test("isLikelyBot catches crawlers and headless browsers, not people", () => {
  for (const ua of [
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; bingbot/2.0)",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 HeadlessChrome/120.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11) Chrome-Lighthouse",
    "",
    null,
  ]) {
    assert.equal(isLikelyBot(ua), true, String(ua));
  }
  assert.equal(
    isLikelyBot("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"),
    false,
  );
});

test("coerceTrafficRange allows 1, 7 or 30 days", () => {
  assert.equal(coerceTrafficRange("1"), 1);
  assert.equal(coerceTrafficRange("30"), 30);
  assert.equal(coerceTrafficRange("14"), 7);
  assert.equal(coerceTrafficRange(null), 7);
});

// ---------------------------------------------------------------------------
// Summary

const NOW = new Date("2026-10-05T12:00:00Z");

test("trafficRangeStart is midnight UTC, counting today as day one", () => {
  assert.equal(trafficRangeStart(1, NOW).toISOString(), "2026-10-05T00:00:00.000Z");
  assert.equal(trafficRangeStart(7, NOW).toISOString(), "2026-09-29T00:00:00.000Z");
});

function view(visit, path, prev, at, source = prev ? "INTERNAL" : "DIRECT", name = null) {
  return { visit_id: visit, path, prev_path: prev, source, source_name: name, created_at: at };
}

const ROWS = [
  // Visit a: Google -> /dsa/tries -> /dsa -> / -> /onboarding (signed up)
  view("a", "/dsa/tries", null, "2026-10-04T09:00:00Z", "SEARCH", "google"),
  view("a", "/dsa", "/dsa/tries", "2026-10-04T09:01:00Z"),
  view("a", "/", "/dsa", "2026-10-04T09:02:00Z"),
  view("a", "/onboarding", "/", "2026-10-04T09:05:00Z"),
  // Visit b: Google -> /dsa/tries, reloads it
  view("b", "/dsa/tries", null, "2026-10-05T08:00:00Z", "SEARCH", "google"),
  view("b", "/dsa/tries", "/dsa/tries", "2026-10-05T08:00:30Z"),
  // Visit c: ChatGPT -> /
  view("c", "/", null, "2026-10-05T10:00:00Z", "AI", "chatgpt"),
  // Visit d started before the range; only its later page is in the rows.
  view("d", "/help", "/", "2026-10-05T11:00:00Z"),
];

test("summarizeTraffic counts visits by their first page and views by row", () => {
  const s = summarizeTraffic(ROWS, { days: 7, now: NOW });
  assert.equal(s.visits, 3);
  assert.equal(s.views, 8);
  assert.equal(s.searchVisits, 2);
  assert.equal(s.aiVisits, 1);
  assert.equal(s.onboardingVisits, 1);
});

test("summarizeTraffic ranks sources and landing pages", () => {
  const s = summarizeTraffic(ROWS, { days: 7, now: NOW });
  assert.deepEqual(s.sources, [
    { source: "SEARCH", name: "google", visits: 2 },
    { source: "AI", name: "chatgpt", visits: 1 },
  ]);
  assert.deepEqual(s.landingPages, [
    { path: "/dsa/tries", visits: 2, search: 2, onboarding: 1 },
    { path: "/", visits: 1, search: 0, onboarding: 0 },
  ]);
});

test("summarizeTraffic ranks pages by views, with distinct visits", () => {
  const s = summarizeTraffic(ROWS, { days: 7, now: NOW });
  assert.deepEqual(s.pages.slice(0, 2), [
    { path: "/dsa/tries", views: 3, visits: 2 },
    { path: "/", views: 2, visits: 2 },
  ]);
});

test("summarizeTraffic lists page-to-page moves without reloads", () => {
  const s = summarizeTraffic(ROWS, { days: 7, now: NOW });
  assert.equal(s.navigation.some((n) => n.from === n.to), false);
  assert.deepEqual(
    s.navigation.map((n) => `${n.from} -> ${n.to}: ${n.count}`).sort(),
    ["/ -> /help: 1", "/ -> /onboarding: 1", "/dsa -> /: 1", "/dsa/tries -> /dsa: 1"],
  );
});

test("summarizeTraffic fills every day in the range, oldest first", () => {
  const s = summarizeTraffic(ROWS, { days: 7, now: NOW });
  assert.equal(s.daily.length, 7);
  assert.equal(s.daily[0].day, "2026-09-29");
  assert.deepEqual(s.daily.at(-2), { day: "2026-10-04", visits: 1, views: 4, searchVisits: 1 });
  assert.deepEqual(s.daily.at(-1), { day: "2026-10-05", visits: 2, views: 4, searchVisits: 1 });
  assert.deepEqual(s.daily[0], { day: "2026-09-29", visits: 0, views: 0, searchVisits: 0 });
});

test("summarizeTraffic handles no rows", () => {
  const s = summarizeTraffic([], { days: 1, now: NOW });
  assert.equal(s.visits, 0);
  assert.equal(s.views, 0);
  assert.deepEqual(s.sources, []);
  assert.deepEqual(s.daily, [{ day: "2026-10-05", visits: 0, views: 0, searchVisits: 0 }]);
});
