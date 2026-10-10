"use server";

import { redirect } from "next/navigation";
import { getUser, signedOutTarget } from "@/lib/db";
import { db } from "@/prisma/db";
import type { SaveProfileInput } from "../onboarding/actions";

function orNull(value: string): string | null {
  const trimmed = value.trim();
  return trimmed === "" ? null : trimmed;
}

export async function saveProfileEdit(input: SaveProfileInput) {
  const user = await getUser();
  if (!user) redirect(await signedOutTarget());

  await db.transaction(async (tx) => {
    await tx.orm.public.User.where({ auth0_id: user.auth0_id }).update({
      full_name: orNull(input.fullName),
      email: orNull(input.email),
      phone: orNull(input.phone),
      location: orNull(input.location),
    });

    // Experiences/bullets: diff by id so row ids stay stable — downstream
    // consumers (e.g. the suggestions API) reference them.
    const existingExps = await tx.orm.public.UserBaseExperience.where((e) =>
      e.user_id.eq(user.auth0_id),
    ).all();
    const ownedExpIds = new Set(existingExps.map((e) => e.id));
    const submittedExpIds = new Set(
      input.experiences.flatMap((e) => (e.id != null ? [e.id] : [])),
    );
    const staleExpIds = existingExps
      .filter((e) => !submittedExpIds.has(e.id))
      .map((e) => e.id);

    if (staleExpIds.length > 0) {
      await tx.orm.public.UserBaseExperienceBullet.where((b) =>
        b.user_experience_id.in(staleExpIds),
      ).deleteAll();
      await tx.orm.public.UserBaseExperience.where((e) =>
        e.id.in(staleExpIds),
      ).deleteAll();
    }

    for (const exp of input.experiences) {
      const fields = {
        company_name: exp.companyName,
        title: exp.title,
        start_date: exp.startDate,
        end_date: exp.endDate,
        description: exp.description,
      };
      // Unrecognized ids can't update another user's row — treat as new.
      const expId =
        exp.id != null && ownedExpIds.has(exp.id)
          ? (await tx.orm.public.UserBaseExperience.where({
              id: exp.id,
            }).update(fields),
            exp.id)
          : (await tx.orm.public.UserBaseExperience.create({
              user_id: user.auth0_id,
              ...fields,
            })).id;

      const existingBullets =
        await tx.orm.public.UserBaseExperienceBullet.where((b) =>
          b.user_experience_id.eq(expId),
        ).all();
      const ownedBulletIds = new Set(existingBullets.map((b) => b.id));
      const submittedBulletIds = new Set(
        exp.bullets.flatMap((b) => (b.id != null ? [b.id] : [])),
      );
      const staleBulletIds = existingBullets
        .filter((b) => !submittedBulletIds.has(b.id))
        .map((b) => b.id);

      if (staleBulletIds.length > 0) {
        await tx.orm.public.UserBaseExperienceBullet.where((b) =>
          b.id.in(staleBulletIds),
        ).deleteAll();
      }
      for (const [i, b] of exp.bullets.entries()) {
        if (b.id != null && ownedBulletIds.has(b.id)) {
          await tx.orm.public.UserBaseExperienceBullet.where({
            id: b.id,
          }).update({ bullet: b.text, bullet_order: i });
        } else {
          await tx.orm.public.UserBaseExperienceBullet.create({
            user_experience_id: expId,
            bullet: b.text,
            bullet_order: i,
          });
        }
      }
    }

    await tx.orm.public.UserBaseSkill.where((s) => s.user_id.eq(user.auth0_id)).deleteAll();
    await tx.orm.public.UserBaseEducation.where((e) => e.user_id.eq(user.auth0_id))
      .deleteAll();
    await tx.orm.public.UserBaseProject.where((p) => p.user_id.eq(user.auth0_id)).deleteAll();
    await tx.orm.public.UserSocialLink.where((l) => l.user_id.eq(user.auth0_id))
      .deleteAll();

    for (const link of input.socialLinks) {
      await tx.orm.public.UserSocialLink.create({
        user_id: user.auth0_id,
        type: link.type,
        link: link.link,
      });
    }

    for (const [i, skill] of input.skills.entries()) {
      await tx.orm.public.UserBaseSkill.create({
        user_id: user.auth0_id,
        name: skill.name,
        category: skill.category,
        sort_order: i,
      });
    }

    for (const edu of input.education) {
      await tx.orm.public.UserBaseEducation.create({
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
      await tx.orm.public.UserBaseProject.create({
        user_id: user.auth0_id,
        name: proj.name,
        link: proj.link,
        description: proj.description,
        start_date: proj.startDate,
        end_date: proj.endDate,
      });
    }
  });

  redirect("/dashboard");
}
