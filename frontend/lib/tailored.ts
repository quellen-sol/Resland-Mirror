// Editable snapshot stored on user_tailored_resume.content — the sections the
// tailor agent owns. Header/education/projects stay sourced from the base
// profile at export time. Mirrors api.tailored.model.TailoredContent.

export interface TailoredExperienceContent {
  company_name: string;
  title: string;
  start_date: string;
  end_date: string | null;
  bullets: string[];
}

export interface TailoredSkillGroupContent {
  category: string | null;
  skills: string[];
}

export interface TailoredContent {
  summary: string | null;
  experiences: TailoredExperienceContent[];
  skill_groups: TailoredSkillGroupContent[];
}

export function parseTailoredContent(raw: string): TailoredContent | null {
  try {
    const parsed = JSON.parse(raw) as TailoredContent;
    if (!parsed || !Array.isArray(parsed.experiences)) return null;
    return {
      summary: parsed.summary ?? null,
      experiences: parsed.experiences.map((e) => ({
        company_name: e.company_name ?? "",
        title: e.title ?? "",
        start_date: e.start_date ?? "",
        end_date: e.end_date ?? null,
        bullets: Array.isArray(e.bullets) ? e.bullets : [],
      })),
      skill_groups: Array.isArray(parsed.skill_groups)
        ? parsed.skill_groups.map((g) => ({
            category: g.category ?? null,
            skills: Array.isArray(g.skills) ? g.skills : [],
          }))
        : [],
    };
  } catch {
    return null;
  }
}

export interface ExportTailoredResponse {
  url: string;
  generated_at: string;
  regenerated: boolean;
}
