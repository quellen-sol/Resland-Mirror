// The memory bank: facts the tailor and suggestion agents learned from the
// user's interview answers, plus any the user added on /memory. Later runs
// read them back instead of asking again.

// Keep in sync with backend/shared/src/shared/memory.py.
export const MAX_MEMORY_FACTS = 200;
export const MAX_TOPIC_CHARS = 120;
export const MAX_FACT_CHARS = 500;

export type MemorySource = "TAILOR" | "SUGGESTION" | "USER";

export const SOURCE_LABELS: Record<MemorySource, string> = {
  TAILOR: "From tailoring",
  SUGGESTION: "From suggestions",
  USER: "Added by you",
};

export interface MemoryFact {
  id: number;
  topic: string;
  content: string;
  source: MemorySource;
}

export interface MemoryTopic {
  topic: string;
  facts: MemoryFact[];
}

/** Facts grouped by topic the way the agents read them: topics A-Z, and
 * oldest fact first within each. */
export function groupFactsByTopic(facts: MemoryFact[]): MemoryTopic[] {
  const groups = new Map<string, MemoryFact[]>();
  for (const fact of [...facts].sort((a, b) => a.id - b.id)) {
    const group = groups.get(fact.topic);
    if (group) group.push(fact);
    else groups.set(fact.topic, [fact]);
  }
  return [...groups.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([topic, facts]) => ({ topic, facts }));
}

export type FactInput =
  | { ok: true; topic: string; content: string }
  | { ok: false; error: string };

/** Trim a fact typed on /memory and hold it to the limits the agents use. */
export function parseFactInput(topic: unknown, content: unknown): FactInput {
  const t = typeof topic === "string" ? topic.trim() : "";
  const c = typeof content === "string" ? content.trim() : "";
  if (!t || !c) {
    return { ok: false, error: "Give the fact a topic and some content." };
  }
  if (t.length > MAX_TOPIC_CHARS) {
    return {
      ok: false,
      error: `Keep the topic under ${MAX_TOPIC_CHARS} characters.`,
    };
  }
  if (c.length > MAX_FACT_CHARS) {
    return {
      ok: false,
      error: `Keep each fact under ${MAX_FACT_CHARS} characters. Split a longer one in two.`,
    };
  }
  return { ok: true, topic: t, content: c };
}
