"use server";

import { redirect } from "next/navigation";
import { getUser } from "@/lib/db";
import { db } from "@/prisma/db";
import type { SaveProfileInput } from "../onboarding/actions";

function orNull(value: string): string | null {
  const trimmed = value.trim();
  return trimmed === "" ? null : trimmed;
}

export async function saveProfileEdit(input: SaveProfileInput) {
  const user = await getUser();
  if (!user) redirect("/auth/login");

  await db.transaction(async (tx) => {
    await tx.orm.public.User.where({ auth0Id: user.auth0Id }).update({
      fullName: orNull(input.fullName),
      email: orNull(input.email),
      phone: orNull(input.phone),
      location: orNull(input.location),
    });

    // Experiences/bullets: diff by id so row ids stay stable — downstream
    // consumers (e.g. the suggestions API) reference them.
    const existingExps = await tx.orm.public.UserBaseJobExperience.where((e) =>
      e.userId.eq(user.auth0Id),
    ).all();
    const ownedExpIds = new Set(existingExps.map((e) => e.id));
    const submittedExpIds = new Set(
      input.experiences.flatMap((e) => (e.id != null ? [e.id] : [])),
    );
    const staleExpIds = existingExps
      .filter((e) => !submittedExpIds.has(e.id))
      .map((e) => e.id);

    if (staleExpIds.length > 0) {
      await tx.orm.public.UserBaseJobExperienceBullet.where((b) =>
        b.userJobExperienceId.in(staleExpIds),
      ).deleteAll();
      await tx.orm.public.UserBaseJobExperience.where((e) =>
        e.id.in(staleExpIds),
      ).deleteAll();
    }

    for (const exp of input.experiences) {
      const fields = {
        companyName: exp.companyName,
        title: exp.title,
        startDate: exp.startDate,
        endDate: exp.endDate,
        description: exp.description,
      };
      // Unrecognized ids can't update another user's row — treat as new.
      const expId =
        exp.id != null && ownedExpIds.has(exp.id)
          ? (await tx.orm.public.UserBaseJobExperience.where({
              id: exp.id,
            }).update(fields),
            exp.id)
          : (await tx.orm.public.UserBaseJobExperience.create({
              userId: user.auth0Id,
              ...fields,
            })).id;

      const existingBullets =
        await tx.orm.public.UserBaseJobExperienceBullet.where((b) =>
          b.userJobExperienceId.eq(expId),
        ).all();
      const ownedBulletIds = new Set(existingBullets.map((b) => b.id));
      const submittedBulletIds = new Set(
        exp.bullets.flatMap((b) => (b.id != null ? [b.id] : [])),
      );
      const staleBulletIds = existingBullets
        .filter((b) => !submittedBulletIds.has(b.id))
        .map((b) => b.id);

      if (staleBulletIds.length > 0) {
        await tx.orm.public.UserBaseJobExperienceBullet.where((b) =>
          b.id.in(staleBulletIds),
        ).deleteAll();
      }
      for (const b of exp.bullets) {
        if (b.id != null && ownedBulletIds.has(b.id)) {
          await tx.orm.public.UserBaseJobExperienceBullet.where({
            id: b.id,
          }).update({ bullet: b.text });
        } else {
          await tx.orm.public.UserBaseJobExperienceBullet.create({
            userJobExperienceId: expId,
            bullet: b.text,
          });
        }
      }
    }

    await tx.orm.public.UserBaseSkill.where((s) => s.userId.eq(user.auth0Id)).deleteAll();
    await tx.orm.public.UserBaseEducation.where((e) => e.userId.eq(user.auth0Id))
      .deleteAll();
    await tx.orm.public.UserBaseProject.where((p) => p.userId.eq(user.auth0Id)).deleteAll();
    await tx.orm.public.UserSocialLink.where((l) => l.userId.eq(user.auth0Id))
      .deleteAll();

    for (const link of input.socialLinks) {
      await tx.orm.public.UserSocialLink.create({
        userId: user.auth0Id,
        type: link.type,
        link: link.link,
      });
    }

    for (const name of input.skills) {
      await tx.orm.public.UserBaseSkill.create({ userId: user.auth0Id, name });
    }

    for (const edu of input.education) {
      await tx.orm.public.UserBaseEducation.create({
        userId: user.auth0Id,
        institution: edu.institution,
        degree: edu.degree,
        fieldOfStudy: edu.fieldOfStudy,
        startDate: edu.startDate,
        endDate: edu.endDate,
        description: edu.description,
      });
    }

    for (const proj of input.projects) {
      await tx.orm.public.UserBaseProject.create({
        userId: user.auth0Id,
        name: proj.name,
        link: proj.link,
        description: proj.description,
        startDate: proj.startDate,
        endDate: proj.endDate,
      });
    }
  });

  redirect("/dashboard");
}
