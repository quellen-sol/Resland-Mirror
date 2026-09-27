// Ordered, optionally-categorized skills.
//
// Storage is a flat, ordered row set (`user_base_skill` rows carry a
// `category` string and a `sort_order`); the editor works on ordered groups —
// one per category plus an `Ungrouped` bucket (category null). Flattening
// groups back to rows keeps categories contiguous, which is what the resume
// export assumes when it groups them again.

export interface SkillRow {
  name: string;
  category: string | null;
}

export interface SkillGroupForm {
  // React key for the group — client-generated, never persisted.
  id: string;
  // null = the "Ungrouped" bucket.
  category: string | null;
  skills: string[];
}

export function newGroupId(): string {
  return crypto.randomUUID();
}

// Fold ordered skill rows into ordered {category, skills} groups — one per
// distinct category in first-appearance order (rows arrive in display order).
export function groupSkills(
  rows: SkillRow[],
): { category: string | null; skills: string[] }[] {
  const groups: { category: string | null; skills: string[] }[] = [];
  const byCategory = new Map<string | null, string[]>();
  for (const row of rows) {
    const name = row.name.trim();
    if (!name) continue;
    const category = row.category?.trim() || null;
    let skills = byCategory.get(category);
    if (!skills) {
      skills = [];
      byCategory.set(category, skills);
      groups.push({ category, skills });
    }
    skills.push(name);
  }
  return groups;
}

// Same folding as groupSkills, plus stable React keys for the form. Returns
// one Ungrouped group when there is nothing to show.
export function rowsToGroups(rows: SkillRow[]): SkillGroupForm[] {
  const groups = groupSkills(rows).map((g) => ({ ...g, id: newGroupId() }));
  return groups.length > 0 ? groups : [ungroupedGroup()];
}

export function ungroupedGroup(): SkillGroupForm {
  return { id: newGroupId(), category: null, skills: [] };
}

// Flatten groups into the ordered row set to persist. Blank-named groups
// collapse into Ungrouped rather than dropping their skills; duplicate skill
// names are dropped after the first occurrence (the table is unique on
// (user_id, name)).
export function groupsToRows(groups: SkillGroupForm[]): SkillRow[] {
  const rows: SkillRow[] = [];
  const seen = new Set<string>();
  for (const group of groups) {
    const category = group.category?.trim() || null;
    for (const skill of group.skills) {
      const name = skill.trim();
      if (!name || seen.has(name)) continue;
      seen.add(name);
      rows.push({ name, category });
    }
  }
  return rows;
}
