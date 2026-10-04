// First-party traffic metrics: what the page-view tracker sends, how the
// beacon route turns it into a page_view row, and how /admin's Traffic panel
// summarizes those rows. Pure functions so node --test can cover them.

/** Mirrors the TrafficSource enum in prisma/contract.prisma. */
export type TrafficSource =
  | "SEARCH"
  | "AI"
  | "SOCIAL"
  | "REFERRAL"
  | "DIRECT"
  | "INTERNAL";

/** What components/page-view-tracker.tsx posts to /api/metrics/pageview. */
export interface PageViewBeacon {
  /** Random per-tab id, kept in sessionStorage. */
  visit: string;
  path: string;
  /** The page this tab was on before. Absent on a visit's first page. */
  prev?: string;
  /** document.referrer, sent on a visit's first page only. */
  referrer?: string;
  utm_source?: string;
  utm_campaign?: string;
}

/** The columns the beacon route writes to page_view. */
export interface PageViewInsert {
  visit_id: string;
  path: string;
  prev_path: string | null;
  source: TrafficSource;
  source_name: string | null;
  utm_campaign: string | null;
}

/** A stored page_view row, as the summary reads it. */
export interface PageViewRecord {
  visit_id: string;
  path: string;
  prev_path: string | null;
  source: TrafficSource;
  source_name: string | null;
  created_at: string | Date;
}

const MAX_PATH = 120;
const PLAIN_PATH = /^\/[A-Za-z0-9._~\-/]*$/;

// Routes whose last segment is a per-user id. Add new ones here so the ids
// stay out of page_view (and the admin tables stay readable).
const ID_ROUTES = [/^\/tailored\/[^/]+$/, /^\/system-design\/[^/]+$/];

/** Masks ids in dynamic routes (/tailored/abc -> /tailored/[id]) and drops
 *  the trailing slash. Null for anything that isn't a plausible path. */
export function normalizePath(pathname: unknown): string | null {
  if (typeof pathname !== "string" || pathname.length > MAX_PATH) return null;
  if (!PLAIN_PATH.test(pathname)) return null;
  const path = pathname.length > 1 ? pathname.replace(/\/+$/, "") : pathname;
  if (ID_ROUTES.some((route) => route.test(path))) {
    return path.replace(/\/[^/]+$/, "/[id]");
  }
  return path;
}

const UNTRACKED = ["/admin", "/auth", "/api", "/maintenance"];

/** False for pages that shouldn't count: /admin, auth and API routes, and
 *  the maintenance page. Takes a normalized path. */
export function isTrackedPath(path: string): boolean {
  return !UNTRACKED.some((p) => path === p || path.startsWith(`${p}/`));
}

// Known referrers, checked in order: the first rule whose pattern matches the
// referrer's host wins, so a subdomain (gemini.google.com) must come before
// its parent's catch-all (google.*).
const KNOWN_SOURCES: [RegExp, TrafficSource, string][] = [
  [/^gemini\.google\./, "AI", "gemini"],
  [/(^|\.)chatgpt\.com$|^chat\.openai\.com$/, "AI", "chatgpt"],
  [/(^|\.)perplexity\.ai$/, "AI", "perplexity"],
  [/(^|\.)claude\.ai$/, "AI", "claude"],
  [/^copilot\.microsoft\.com$/, "AI", "copilot"],
  [/(^|\.)phind\.com$/, "AI", "phind"],
  [/(^|\.)you\.com$/, "AI", "you.com"],
  [/(^|\.)google\.[a-z.]+$|^com\.google\.android\.googlequicksearchbox$/, "SEARCH", "google"],
  [/(^|\.)bing\.com$/, "SEARCH", "bing"],
  [/(^|\.)duckduckgo\.com$/, "SEARCH", "duckduckgo"],
  [/^search\.brave\.com$/, "SEARCH", "brave"],
  [/(^|\.)yahoo\.com$/, "SEARCH", "yahoo"],
  [/(^|\.)ecosia\.org$/, "SEARCH", "ecosia"],
  [/(^|\.)kagi\.com$/, "SEARCH", "kagi"],
  [/(^|\.)startpage\.com$/, "SEARCH", "startpage"],
  [/(^|\.)yandex\.[a-z.]+$/, "SEARCH", "yandex"],
  [/(^|\.)baidu\.com$/, "SEARCH", "baidu"],
  [/(^|\.)qwant\.com$/, "SEARCH", "qwant"],
  [/^news\.ycombinator\.com$/, "SOCIAL", "hacker news"],
  [/(^|\.)reddit\.com$/, "SOCIAL", "reddit"],
  [/^(x|twitter)\.com$|^t\.co$/, "SOCIAL", "x"],
  [/(^|\.)linkedin\.com$|^lnkd\.in$/, "SOCIAL", "linkedin"],
  [/(^|\.)facebook\.com$/, "SOCIAL", "facebook"],
  [/(^|\.)youtube\.com$/, "SOCIAL", "youtube"],
  [/(^|\.)producthunt\.com$/, "SOCIAL", "product hunt"],
  [/^dev\.to$/, "SOCIAL", "dev.to"],
  [/(^|\.)discord\.com$/, "SOCIAL", "discord"],
  [/(^|\.)bsky\.app$/, "SOCIAL", "bluesky"],
];

// What a utm_source value means when it names a known source.
const UTM_NAMES = new Map<string, [TrafficSource, string]>(
  KNOWN_SOURCES.map(([, source, name]) => [name, [source, name]]),
);
UTM_NAMES.set("hn", ["SOCIAL", "hacker news"]);
UTM_NAMES.set("twitter", ["SOCIAL", "x"]);

const MAX_TEXT = 100;

function bareHost(host: string): string {
  return host.toLowerCase().replace(/^www\./, "");
}

/** The host a referrer names. Android apps send android-app://<package>/. */
function referrerHost(referrer: string): string | null {
  try {
    return new URL(referrer).hostname || null;
  } catch {
    return null;
  }
}

/** Where a visit came from, from its first page's referrer and utm_source.
 *  `siteHost` is this site's own host, which counts as INTERNAL. */
export function classifySource(input: {
  referrer?: string | null;
  utmSource?: string | null;
  siteHost: string;
}): { source: TrafficSource; name: string | null } {
  const utm = input.utmSource?.trim().toLowerCase().slice(0, MAX_TEXT);
  if (utm) {
    const known = UTM_NAMES.get(utm);
    return known ? { source: known[0], name: known[1] } : { source: "REFERRAL", name: utm };
  }

  const host = input.referrer ? referrerHost(input.referrer) : null;
  if (!host) return { source: "DIRECT", name: null };
  const bare = bareHost(host);
  // Our own pages, and the Auth0 login screens that send people back.
  if (bare === bareHost(input.siteHost) || bare.endsWith(".auth0.com")) {
    return { source: "INTERNAL", name: null };
  }
  for (const [pattern, source, name] of KNOWN_SOURCES) {
    if (pattern.test(bare)) return { source, name };
  }
  return { source: "REFERRAL", name: bare.slice(0, MAX_TEXT) };
}

/** Validates a beacon body into a row to insert; null for anything
 *  malformed or untracked. */
export function parsePageView(body: unknown, siteHost: string): PageViewInsert | null {
  if (typeof body !== "object" || body === null) return null;
  const b = body as Record<string, unknown>;
  if (typeof b.visit !== "string" || !VISIT_ID.test(b.visit)) return null;

  const path = normalizePath(b.path);
  if (!path || !isTrackedPath(path)) return null;
  let prev: string | null = null;
  if (b.prev !== undefined) {
    prev = normalizePath(b.prev);
    if (!prev) return null;
  }

  const { source, name } = prev
    ? { source: "INTERNAL" as const, name: null }
    : classifySource({
        referrer: optionalText(b.referrer, 500),
        utmSource: optionalText(b.utm_source),
        siteHost,
      });
  return {
    visit_id: b.visit,
    path,
    prev_path: prev,
    source,
    source_name: name,
    utm_campaign: optionalText(b.utm_campaign),
  };
}

const VISIT_ID = /^[A-Za-z0-9-]{8,64}$/;

function optionalText(value: unknown, max = MAX_TEXT): string | null {
  return typeof value === "string" && value.trim() ? value.trim().slice(0, max) : null;
}

const BOT_UA =
  /bot|crawl|spider|slurp|headless|lighthouse|pagespeed|preview|fetch|monitor|python|curl|wget|httpclient|java\/|go-http|node-fetch|axios|vercel|facebookexternalhit|embedly|whatsapp|telegram/i;

/** Crawlers and headless browsers that run JavaScript. A missing user agent
 *  counts as a bot: every real browser sends one. */
export function isLikelyBot(userAgent: string | null | undefined): boolean {
  return !userAgent || BOT_UA.test(userAgent);
}

export const TRAFFIC_RANGES = [1, 7, 30] as const;
export type TrafficRange = (typeof TRAFFIC_RANGES)[number];

/** `?days=` for the admin traffic route, falling back to 7. */
export function coerceTrafficRange(value: unknown): TrafficRange {
  const days = Number(value);
  return TRAFFIC_RANGES.find((r) => r === days) ?? 7;
}

const DAY_MS = 24 * 60 * 60 * 1000;

/** Midnight UTC at the start of a `days`-long range that ends today. */
export function trafficRangeStart(days: number, now: Date): Date {
  const today = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
  return new Date(today - (days - 1) * DAY_MS);
}

export interface TrafficSummary {
  /** Visits whose first page falls in the range. */
  visits: number;
  views: number;
  searchVisits: number;
  aiVisits: number;
  /** Visits that reached /onboarding, which is where new accounts land. */
  onboardingVisits: number;
  sources: { source: TrafficSource; name: string | null; visits: number }[];
  landingPages: { path: string; visits: number; search: number; onboarding: number }[];
  pages: { path: string; views: number; visits: number }[];
  /** Page-to-page moves inside a visit; reloads are left out. */
  navigation: { from: string; to: string; count: number }[];
  /** One entry per UTC day in the range, oldest first, zeros included. */
  daily: { day: string; visits: number; views: number; searchVisits: number }[];
}

const ONBOARDING = "/onboarding";

/** Sorted biggest first, ties broken by key so the tables don't jitter. */
function ranked<T>(items: Iterable<T>, count: (t: T) => number, key: (t: T) => string): T[] {
  return [...items].sort((a, b) => count(b) - count(a) || key(a).localeCompare(key(b)));
}

function bump<K>(map: Map<K, number>, key: K) {
  map.set(key, (map.get(key) ?? 0) + 1);
}

export function summarizeTraffic(
  rows: readonly PageViewRecord[],
  opts: { days: number; now: Date },
): TrafficSummary {
  const start = trafficRangeStart(opts.days, opts.now);
  const daily = Array.from({ length: opts.days }, (_, i) => ({
    day: new Date(start.getTime() + i * DAY_MS).toISOString().slice(0, 10),
    visits: 0,
    views: 0,
    searchVisits: 0,
  }));
  const dayOf = (at: string | Date) =>
    daily.find((d) => d.day === new Date(at).toISOString().slice(0, 10));

  // A visit counts once, by its first page; one that began before the range
  // still contributes views but isn't a visit here.
  const landings = new Map<string, PageViewRecord>();
  const reachedOnboarding = new Set<string>();
  const pageViews = new Map<string, number>();
  const pageVisits = new Map<string, Set<string>>();
  const moves = new Map<string, number>();

  for (const row of rows) {
    if (row.prev_path === null && !landings.has(row.visit_id)) landings.set(row.visit_id, row);
    if (row.path === ONBOARDING) reachedOnboarding.add(row.visit_id);
    bump(pageViews, row.path);
    const visitors = pageVisits.get(row.path) ?? new Set<string>();
    visitors.add(row.visit_id);
    pageVisits.set(row.path, visitors);
    if (row.prev_path !== null && row.prev_path !== row.path) {
      bump(moves, `${row.prev_path}\u0000${row.path}`);
    }
    const day = dayOf(row.created_at);
    if (day) day.views += 1;
  }

  const sources = new Map<string, { source: TrafficSource; name: string | null; visits: number }>();
  const landingPages = new Map<string, { path: string; visits: number; search: number; onboarding: number }>();
  let searchVisits = 0;
  let aiVisits = 0;
  for (const [visit, row] of landings) {
    const isSearch = row.source === "SEARCH";
    if (isSearch) searchVisits += 1;
    if (row.source === "AI") aiVisits += 1;

    const sourceKey = `${row.source}:${row.source_name ?? ""}`;
    const s = sources.get(sourceKey) ?? { source: row.source, name: row.source_name, visits: 0 };
    s.visits += 1;
    sources.set(sourceKey, s);

    const l = landingPages.get(row.path) ?? { path: row.path, visits: 0, search: 0, onboarding: 0 };
    l.visits += 1;
    if (isSearch) l.search += 1;
    if (reachedOnboarding.has(visit)) l.onboarding += 1;
    landingPages.set(row.path, l);

    const day = dayOf(row.created_at);
    if (day) {
      day.visits += 1;
      if (isSearch) day.searchVisits += 1;
    }
  }

  return {
    visits: landings.size,
    views: rows.length,
    searchVisits,
    aiVisits,
    onboardingVisits: [...landings.keys()].filter((v) => reachedOnboarding.has(v)).length,
    sources: ranked(sources.values(), (s) => s.visits, (s) => `${s.source}:${s.name ?? ""}`),
    landingPages: ranked(landingPages.values(), (l) => l.visits, (l) => l.path),
    pages: ranked(
      [...pageViews].map(([path, views]) => ({ path, views, visits: pageVisits.get(path)!.size })),
      (p) => p.views,
      (p) => p.path,
    ),
    navigation: ranked(
      [...moves].map(([key, count]) => {
        const [from, to] = key.split("\u0000");
        return { from, to, count };
      }),
      (n) => n.count,
      (n) => `${n.from} ${n.to}`,
    ),
    daily,
  };
}
