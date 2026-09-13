import type { ProfileFormValues } from "@/components/profile-form";
import type { SaveProfileInput } from "@/app/(protected)/onboarding/actions";

export function toProfileInput(values: ProfileFormValues): SaveProfileInput {
  return {
    fullName: values.fullName,
    email: values.email,
    phone: values.phone,
    location: values.location,
    socialLinks: values.socialLinks.filter((l) => l.link.trim() !== ""),
    skills: values.skills.map((s) => s.trim()).filter(Boolean),
    experiences: values.experiences
      .filter((e) => e.companyName && e.title && e.startDate)
      .map((e) => ({
        id: e.id,
        companyName: e.companyName,
        title: e.title,
        startDate: e.startDate,
        endDate: e.endDate || null,
        description: e.description || null,
        bullets: e.bullets
          .map((b) => ({ id: b.id, text: b.text.trim() }))
          .filter((b) => b.text !== ""),
      })),
    education: values.education
      .filter((e) => e.institution && e.degree && e.fieldOfStudy && e.startDate)
      .map((e) => ({
        institution: e.institution,
        degree: e.degree,
        fieldOfStudy: e.fieldOfStudy,
        startDate: e.startDate,
        endDate: e.endDate || null,
        description: e.description || null,
      })),
    projects: values.projects
      .filter((p) => p.name && p.startDate)
      .map((p) => ({
        name: p.name,
        link: p.link || null,
        description: p.description || null,
        startDate: p.startDate,
        endDate: p.endDate || null,
      })),
  };
}
