// DSA study center: the content model, plus the pure helpers the pages and
// the progress route share. Topics live in content/dsa — one topic.ts of
// prose per topic, and one folder per example holding a runnable solution in
// every language (see lib/dsa-examples.test.js).

export type DsaLanguage = "typescript" | "python" | "go" | "csharp" | "java";

export interface DsaLanguageInfo {
  id: DsaLanguage;
  label: string;
  /** Solution file name inside an example folder. */
  file: string;
}

// Tab order on every code block. Python leads: it's the language most
// candidates interview in.
export const DSA_LANGUAGES: readonly DsaLanguageInfo[] = [
  { id: "python", label: "Python", file: "solution.py" },
  { id: "typescript", label: "TypeScript", file: "solution.ts" },
  { id: "go", label: "Go", file: "solution.go" },
  { id: "csharp", label: "C#", file: "Solution.cs" },
  { id: "java", label: "Java", file: "Solution.java" },
];

export const DEFAULT_DSA_LANGUAGE: DsaLanguage = "python";

/** "A, B and C". */
function joinWithAnd(items: readonly string[]): string {
  return items.length < 2
    ? (items[0] ?? "")
    : `${items.slice(0, -1).join(", ")} and ${items[items.length - 1]}`;
}

/** "Python, TypeScript, Go, C# and Java", for copy. */
export const DSA_LANGUAGE_NAMES = joinWithAnd(DSA_LANGUAGES.map((l) => l.label));

/** localStorage key and <html> data attribute for the chosen language. */
export const DSA_LANGUAGE_STORAGE_KEY = "resland.dsa.language";

export type DsaCategoryId =
  | "foundations"
  | "techniques"
  | "linear"
  | "trees"
  | "graphs"
  | "dp";

export interface DsaCategory {
  id: DsaCategoryId;
  title: string;
  blurb: string;
}

// Also the suggested study order: topics sort by category, then by their
// position in content/dsa/index.ts.
export const DSA_CATEGORIES: readonly DsaCategory[] = [
  {
    id: "foundations",
    title: "Foundations",
    blurb: "How to measure an algorithm, and the structures everything else builds on.",
  },
  {
    id: "techniques",
    title: "Core Techniques",
    blurb: "Patterns that turn a brute-force scan into a linear or logarithmic one.",
  },
  {
    id: "linear",
    title: "Lists, Stacks & Queues",
    blurb: "Sequential structures and the problems they make easy.",
  },
  {
    id: "trees",
    title: "Trees & Heaps",
    blurb: "Hierarchical structures for ordered data, prefixes and priorities.",
  },
  {
    id: "graphs",
    title: "Graphs",
    blurb: "Traversal, ordering, connectivity and shortest paths.",
  },
  {
    id: "dp",
    title: "Backtracking & Dynamic Programming",
    blurb: "Exploring choices exhaustively, then reusing the answers to subproblems.",
  },
];

export type DsaLevel = "BEGINNER" | "INTERMEDIATE" | "ADVANCED";
export type DsaDifficulty = "EASY" | "MEDIUM" | "HARD";

export const DSA_LEVEL_LABELS: Record<DsaLevel, string> = {
  BEGINNER: "Beginner",
  INTERMEDIATE: "Intermediate",
  ADVANCED: "Advanced",
};

/** A block of prose. `text` and list items accept inline markup: `code`,
 *  **bold**, and [label](href) links — see parseInline. */
export type DsaBlock =
  | { type: "p"; text: string }
  | { type: "list"; items: string[]; ordered?: boolean }
  /** Monospace ASCII art: an array, a tree, pointer positions. */
  | { type: "diagram"; text: string; caption?: string }
  | { type: "tip"; text: string };

export interface DsaComplexityRow {
  operation: string;
  time: string;
  space: string;
}

export interface DsaExample {
  /** Folder under content/dsa/<slug>/ with one solution per language and
   *  expected.txt, the output every one of them must print. */
  id: string;
  title: string;
  /** How the code works — rendered above the code tabs. */
  explanation: DsaBlock[];
  time: string;
  space: string;
}

export interface DsaProblem extends DsaExample {
  difficulty: DsaDifficulty;
  /** The problem as an interviewer would pose it. */
  statement: DsaBlock[];
  /** Where to submit the same problem. */
  link?: { label: string; url: string };
}

export interface DsaPracticeLink {
  title: string;
  url: string;
  difficulty: DsaDifficulty;
}

export interface DsaTopic {
  slug: string;
  title: string;
  /** The page's <title>, worded the way people search for the topic, e.g.
   *  "Sliding Window Technique: Template and Interview Problems". At most 55
   *  characters so " · Resland" still fits. */
  seoTitle: string;
  category: DsaCategoryId;
  level: DsaLevel;
  /** One sentence — topic cards and the meta description. */
  summary: string;
  /** Slugs worth reading first. */
  prerequisites: string[];
  /** What it is and how it works. */
  overview: DsaBlock[];
  /** Clues in a problem statement that point at this topic. */
  signals: string[];
  complexity: DsaComplexityRow[];
  /** The reusable core implementation. */
  template: DsaExample;
  /** Classic problems worked end to end. */
  problems: DsaProblem[];
  pitfalls: string[];
  /** More problems to try alone. */
  practice: DsaPracticeLink[];
}

// ---------------------------------------------------------------------------
// Navigation

/** The few fields navigation and progress read, cheap to hand to client
 *  components instead of whole topics. */
export type DsaTopicRef = Pick<DsaTopic, "slug" | "title" | "category" | "level">;

export function toTopicRef({ slug, title, category, level }: DsaTopic): DsaTopicRef {
  return { slug, title, category, level };
}

type Placed = Pick<DsaTopic, "slug" | "category">;

const CATEGORY_RANK = new Map(DSA_CATEGORIES.map((c, i) => [c.id, i]));

/** Topics in study order: category order first, then their listed order. */
export function orderTopics<T extends Placed>(topics: readonly T[]): T[] {
  // Array.prototype.sort is stable, so listed order survives within a category.
  return [...topics].sort(
    (a, b) =>
      (CATEGORY_RANK.get(a.category) ?? Infinity) -
      (CATEGORY_RANK.get(b.category) ?? Infinity),
  );
}

export interface DsaCategoryGroup<T extends Placed = DsaTopic> {
  category: DsaCategory;
  topics: T[];
}

/** Categories in order with their topics; empty categories are dropped. */
export function groupTopicsByCategory<T extends Placed>(
  topics: readonly T[],
): DsaCategoryGroup<T>[] {
  return DSA_CATEGORIES.map((category) => ({
    category,
    topics: topics.filter((t) => t.category === category.id),
  })).filter((g) => g.topics.length > 0);
}

/** The topics before and after `slug` in study order. */
export function topicNeighbors<T extends Placed>(
  topics: readonly T[],
  slug: string,
): { prev: T | null; next: T | null } {
  const ordered = orderTopics(topics);
  const i = ordered.findIndex((t) => t.slug === slug);
  if (i === -1) return { prev: null, next: null };
  return { prev: ordered[i - 1] ?? null, next: ordered[i + 1] ?? null };
}

/** Topics that list `slug` as a prerequisite, in study order. */
export function topicDependents<T extends Placed & Pick<DsaTopic, "prerequisites">>(
  topics: readonly T[],
  slug: string,
): T[] {
  return orderTopics(topics.filter((t) => t.prerequisites.includes(slug)));
}

// ---------------------------------------------------------------------------
// Search metadata

export const META_DESCRIPTION_MAX = 160;

/** The topic summary, plus as many of its worked problems as fit in
 *  META_DESCRIPTION_MAX: "… Worked problems: Two Sum and Group Anagrams." */
export function topicMetaDescription(
  topic: Pick<DsaTopic, "summary" | "problems">,
): string {
  const titles = topic.problems.map((p) => p.title);
  for (let n = titles.length; n > 0; n--) {
    const list = joinWithAnd(titles.slice(0, n));
    const text = `${topic.summary} Worked ${n === 1 ? "problem" : "problems"}: ${list}.`;
    if (text.length <= META_DESCRIPTION_MAX) return text;
  }
  return topic.summary;
}

// ---------------------------------------------------------------------------
// Inline markup

export type InlineToken =
  | { type: "text"; text: string }
  | { type: "code"; text: string }
  | { type: "strong"; text: string }
  | { type: "link"; text: string; href: string };

// Code spans first so markup characters inside them stay literal.
const INLINE = /`([^`]+)`|\*\*(.+?)\*\*|\[([^\]]+)\]\(([^)\s]+)\)/g;

/** Splits prose into text, `code`, **bold** and [label](href) tokens.
 *  Unclosed markers are kept as literal text. */
export function parseInline(text: string): InlineToken[] {
  const tokens: InlineToken[] = [];
  let last = 0;
  for (const m of text.matchAll(INLINE)) {
    if (m.index > last) tokens.push({ type: "text", text: text.slice(last, m.index) });
    if (m[1] !== undefined) tokens.push({ type: "code", text: m[1] });
    else if (m[2] !== undefined) tokens.push({ type: "strong", text: m[2] });
    else tokens.push({ type: "link", text: m[3], href: m[4] });
    last = m.index + m[0].length;
  }
  if (last < text.length) tokens.push({ type: "text", text: text.slice(last) });
  return tokens;
}

/** Prose with its markup removed, for meta tags and structured data. */
export function toPlainText(text: string): string {
  return parseInline(text)
    .map((token) => token.text)
    .join("");
}

// ---------------------------------------------------------------------------
// Progress (GET/PUT /api/dsa/progress)

export type DsaProgressResponse =
  | { signedIn: false }
  | { signedIn: true; studied: string[] };

export interface DsaProgressUpdate {
  topic: string;
  studied: boolean;
}

/** Validates a PUT body; null for anything malformed or an unknown topic. */
export function parseProgressUpdate(
  body: unknown,
  knownSlugs: ReadonlySet<string>,
): DsaProgressUpdate | null {
  if (typeof body !== "object" || body === null) return null;
  const { topic, studied } = body as Record<string, unknown>;
  if (typeof topic !== "string" || !knownSlugs.has(topic)) return null;
  if (typeof studied !== "boolean") return null;
  return { topic, studied };
}

export interface DsaProgressSummary {
  done: number;
  total: number;
  byCategory: Partial<Record<DsaCategoryId, { done: number; total: number }>>;
}

/** Counts studied topics overall and per category. Slugs that no longer
 *  match a topic are ignored. */
export function summarizeProgress(
  topics: readonly Placed[],
  studied: Iterable<string>,
): DsaProgressSummary {
  const done = new Set(studied);
  const summary: DsaProgressSummary = { done: 0, total: 0, byCategory: {} };
  for (const topic of topics) {
    const bucket = (summary.byCategory[topic.category] ??= { done: 0, total: 0 });
    bucket.total += 1;
    summary.total += 1;
    if (done.has(topic.slug)) {
      bucket.done += 1;
      summary.done += 1;
    }
  }
  return summary;
}

const LANGUAGE_IDS = new Set<string>(DSA_LANGUAGES.map((l) => l.id));

/** Narrows a stored value to a language, falling back to the default. */
export function coerceDsaLanguage(value: unknown): DsaLanguage {
  return typeof value === "string" && LANGUAGE_IDS.has(value)
    ? (value as DsaLanguage)
    : DEFAULT_DSA_LANGUAGE;
}
