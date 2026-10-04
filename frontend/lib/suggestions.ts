/** One bullet's alternative rewrites from a suggestion session. */
export interface BulletOptions {
  bullet_id: number;
  options: string[];
}

/** Read a session's stored result: a JSON array of {bullet_id, options}.
 *  Sessions from before options existed stored {bullet_id, suggestion} —
 *  that reads as a single option. Anything malformed is dropped. */
export function parseSuggestionResult(
  result: string | null | undefined,
): BulletOptions[] {
  if (!result) return [];
  let parsed: unknown;
  try {
    parsed = JSON.parse(result);
  } catch {
    return [];
  }
  if (!Array.isArray(parsed)) return [];

  const bullets: BulletOptions[] = [];
  for (const entry of parsed) {
    if (!entry || typeof entry !== "object") continue;
    const { bullet_id, options, suggestion } = entry as Record<string, unknown>;
    if (typeof bullet_id !== "number") continue;
    const raw = Array.isArray(options) ? options : [suggestion];
    const texts = raw.filter(
      (o): o is string => typeof o === "string" && o.trim() !== "",
    );
    if (texts.length > 0) bullets.push({ bullet_id, options: texts });
  }
  return bullets;
}

/** The reply that asks the agent for a fresh set of options. */
export function moreOptionsMessage(guidance: string): string {
  return (
    guidance.trim() ||
    "Write three different options, not repeats of the ones above."
  );
}
