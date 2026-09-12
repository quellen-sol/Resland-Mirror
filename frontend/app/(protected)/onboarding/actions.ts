"use server";

import { Temporal } from "temporal-polyfill";
import { redirect } from "next/navigation";
import { getUser } from "@/lib/db";
import { db } from "@/prisma/db";

export interface ExperienceInput {
  companyName: string;
  title: string;
  startDate: string;
  endDate: string | null;
  description: string | null;
  bullets: string[];
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

function toInstant(date: string | null): Temporal.Instant | null {
  return date ? Temporal.Instant.from(`${date}T00:00:00Z`) : null;
}

function orNull(value: string): string | null {
  const trimmed = value.trim();
  return trimmed === "" ? null : trimmed;
}

export async function completeOnboarding() {
  const user = await getUser();
  if (!user) redirect("/auth/login");
  if (!user.hasOnboarded) {
    await db.orm.public.User.where({ auth0Id: user.auth0Id }).update({
      hasOnboarded: true,
    });
  }
}

export async function saveManualProfile(input: SaveProfileInput) {
  const user = await getUser();
  if (!user) redirect("/auth/login");

  await db.orm.public.User.where({ auth0Id: user.auth0Id }).update({
    fullName: orNull(input.fullName),
    email: orNull(input.email),
    phone: orNull(input.phone),
    location: orNull(input.location),
  });

  for (const link of input.socialLinks) {
    await db.orm.public.UserSocialLink.create({
      userId: user.auth0Id,
      type: link.type,
      link: link.link,
    });
  }

  for (const name of input.skills) {
    await db.orm.public.UserBaseSkill.create({ userId: user.auth0Id, name });
  }

  for (const exp of input.experiences) {
    const experience = await db.orm.public.UserBaseJobExperience.create({
      userId: user.auth0Id,
      companyName: exp.companyName,
      title: exp.title,
      startDate: toInstant(exp.startDate)!,
      endDate: toInstant(exp.endDate),
      description: exp.description,
    });
    for (const bullet of exp.bullets) {
      await db.orm.public.UserBaseJobExperienceBullet.create({
        userJobExperienceId: experience.id,
        bullet,
      });
    }
  }

  for (const edu of input.education) {
    await db.orm.public.UserBaseEducation.create({
      userId: user.auth0Id,
      institution: edu.institution,
      degree: edu.degree,
      fieldOfStudy: edu.fieldOfStudy,
      startDate: toInstant(edu.startDate)!,
      endDate: toInstant(edu.endDate),
      description: edu.description,
    });
  }

  for (const proj of input.projects) {
    await db.orm.public.UserBaseProject.create({
      userId: user.auth0Id,
      name: proj.name,
      link: proj.link,
      description: proj.description,
      startDate: toInstant(proj.startDate)!,
      endDate: toInstant(proj.endDate),
    });
  }

  if (!user.hasOnboarded) {
    await db.orm.public.User.where({ auth0Id: user.auth0Id }).update({
      hasOnboarded: true,
    });
  }

  redirect("/dashboard");
}
