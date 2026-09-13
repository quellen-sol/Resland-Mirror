"use server";

import { redirect } from "next/navigation";
import { getUser } from "@/lib/db";
import { db } from "@/prisma/db";

export interface BulletInput {
  id?: number;
  text: string;
}

export interface ExperienceInput {
  id?: number;
  companyName: string;
  title: string;
  startDate: string;
  endDate: string | null;
  description: string | null;
  bullets: BulletInput[];
}

export interface EducationInput {
  institution: string;
  degree: string;
  fieldOfStudy: string;
  startDate: string;
  endDate: string | null;
  description: string | null;
}

export interface ProjectInput {
  name: string;
  link: string | null;
  description: string | null;
  startDate: string;
  endDate: string | null;
}

export interface SaveProfileInput {
  fullName: string;
  email: string;
  phone: string;
  location: string;
  socialLinks: { type: "LINKEDIN" | "GITHUB" | "WEBSITE"; link: string }[];
  skills: string[];
  experiences: ExperienceInput[];
  education: EducationInput[];
  projects: ProjectInput[];
}

function orNull(value: string): string | null {
  const trimmed = value.trim();
  return trimmed === "" ? null : trimmed;
}

export async function completeOnboarding() {
  const user = await getUser();
  if (!user) redirect("/auth/login");
  if (!user.has_onboarded) {
    await db.orm.public.User.where({ auth0_id: user.auth0_id }).update({
      has_onboarded: true,
    });
  }
}

export async function saveManualProfile(input: SaveProfileInput) {
  const user = await getUser();
  if (!user) redirect("/auth/login");

  await db.orm.public.User.where({ auth0_id: user.auth0_id }).update({
    full_name: orNull(input.fullName),
    email: orNull(input.email),
    phone: orNull(input.phone),
    location: orNull(input.location),
  });

  for (const link of input.socialLinks) {
    await db.orm.public.UserSocialLink.create({
      user_id: user.auth0_id,
      type: link.type,
      link: link.link,
    });
  }

  for (const name of input.skills) {
    await db.orm.public.UserBaseSkill.create({ user_id: user.auth0_id, name });
  }

  for (const exp of input.experiences) {
    const experience = await db.orm.public.UserBaseExperience.create({
      user_id: user.auth0_id,
      company_name: exp.companyName,
      title: exp.title,
      start_date: exp.startDate,
      end_date: exp.endDate,
      description: exp.description,
    });
    for (const bullet of exp.bullets) {
      await db.orm.public.UserBaseExperienceBullet.create({
        user_experience_id: experience.id,
        bullet: bullet.text,
      });
    }
  }

  for (const edu of input.education) {
    await db.orm.public.UserBaseEducation.create({
      user_id: user.auth0_id,
      institution: edu.institution,
      degree: edu.degree,
      field_of_study: edu.fieldOfStudy,
      start_date: edu.startDate,
      end_date: edu.endDate,
      description: edu.description,
    });
  }

  for (const proj of input.projects) {
    await db.orm.public.UserBaseProject.create({
      user_id: user.auth0_id,
      name: proj.name,
      link: proj.link,
      description: proj.description,
      start_date: proj.startDate,
      end_date: proj.endDate,
    });
  }

  if (!user.has_onboarded) {
    await db.orm.public.User.where({ auth0_id: user.auth0_id }).update({
      has_onboarded: true,
    });
  }

  redirect("/dashboard");
}
