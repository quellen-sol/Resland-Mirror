"use server";

import { Temporal } from "temporal-polyfill";
import { redirect } from "next/navigation";
import { getUser } from "@/lib/db";
import { db } from "@/prisma/db";
import type { SaveProfileInput } from "../onboarding/actions";

function toInstant(date: string | null): Temporal.Instant | null {
  return date ? Temporal.Instant.from(`${date}T00:00:00Z`) : null;
}

function orNull(value: string): string | null {
  const trimmed = value.trim();
  return trimmed === "" ? null : trimmed;
}

export async function saveProfileEdit(input: SaveProfileInput) {
  const user = await getUser();
  if (!user) redirect("/auth/login");

  await db.transaction(async (tx) => {
    await tx.orm.public.User.where({ id: user.id }).update({
      fullName: orNull(input.fullName),
      email: orNull(input.email),
      phone: orNull(input.phone),
      location: orNull(input.location),
    });

    // Delete existing profile rows (bullets first — they FK to experiences).
    const expIds = (
      await tx.orm.public.UserJobExperience.where((e) =>
        e.userId.eq(user.id),
      ).all()
    ).map((e) => e.id);

    if (expIds.length > 0) {
      await tx.orm.public.UserJobExperienceBullet.where((b) =>
        b.userJobExperienceId.in(expIds),
      ).delete();
    }
    await tx.orm.public.UserJobExperience.where((e) =>
      e.userId.eq(user.id),
    ).delete();
    await tx.orm.public.UserSkill.where((s) => s.userId.eq(user.id)).delete();
    await tx.orm.public.UserEducation.where((e) => e.userId.eq(user.id))
      .delete();
    await tx.orm.public.UserProject.where((p) => p.userId.eq(user.id)).delete();
    await tx.orm.public.UserSocialLink.where((l) => l.userId.eq(user.id))
      .delete();

    for (const link of input.socialLinks) {
      await tx.orm.public.UserSocialLink.create({
        userId: user.id,
        type: link.type,
        link: link.link,
      });
    }

    for (const name of input.skills) {
      await tx.orm.public.UserSkill.create({ userId: user.id, name });
    }

    for (const exp of input.experiences) {
      const experience = await tx.orm.public.UserJobExperience.create({
        userId: user.id,
        companyName: exp.companyName,
        title: exp.title,
        startDate: toInstant(exp.startDate)!,
        endDate: toInstant(exp.endDate),
        description: exp.description,
      });
      for (const bullet of exp.bullets) {
        await tx.orm.public.UserJobExperienceBullet.create({
          userJobExperienceId: experience.id,
          bullet,
        });
      }
    }

    for (const edu of input.education) {
      await tx.orm.public.UserEducation.create({
        userId: user.id,
        institution: edu.institution,
        degree: edu.degree,
        fieldOfStudy: edu.fieldOfStudy,
        startDate: toInstant(edu.startDate)!,
        endDate: toInstant(edu.endDate),
        description: edu.description,
      });
    }

    for (const proj of input.projects) {
      await tx.orm.public.UserProject.create({
        userId: user.id,
        name: proj.name,
        link: proj.link,
        description: proj.description,
        startDate: toInstant(proj.startDate)!,
        endDate: toInstant(proj.endDate),
      });
    }
  });

  redirect("/dashboard");
}
