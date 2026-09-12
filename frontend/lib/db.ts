import { auth0 } from "./auth0";
import { db } from "../prisma/db";

export async function getUser() {
    const session = await auth0.getSession();
    if (!session || !session.user.email) {
        return null;
    }

    const existing = await db.orm.public.User
        .where((u) => u.auth0Id.eq(session.user.sub))
        .first();
    if (existing) {
        return existing;
    }

    try {
        return await db.orm.public.User.create({ auth0Id: session.user.sub });
    } catch {
        // Lost a create race — the row exists now, fetch it.
        return await db.orm.public.User
            .where((u) => u.auth0Id.eq(session.user.sub))
            .first();
    }
}

export async function upsertUser() {
    await getUser();
}

export async function getUserProfileData(userId: string) {
    const [uploadJobs, skills, experiences, education, projects, socialLinks] =
        await Promise.all([
            db.orm.public.UserUploadJob
                .where((j) => j.userId.eq(userId))
                .orderBy((j) => j.createdAt.desc())
                .all(),
            db.orm.public.UserBaseSkill.where((s) => s.userId.eq(userId)).all(),
            db.orm.public.UserBaseJobExperience.where((e) => e.userId.eq(userId))
                .all(),
            db.orm.public.UserBaseEducation.where((e) => e.userId.eq(userId)).all(),
            db.orm.public.UserBaseProject.where((p) => p.userId.eq(userId)).all(),
            db.orm.public.UserSocialLink.where((l) => l.userId.eq(userId))
                .all(),
        ]);

    const experienceIds = experiences.map((e) => e.id);
    const bullets = experienceIds.length
        ? await db.orm.public.UserBaseJobExperienceBullet.where((b) =>
              b.userJobExperienceId.in(experienceIds),
          ).all()
        : [];

    return {
        uploadJobs,
        skills,
        experiences,
        bullets,
        education,
        projects,
        socialLinks,
    };
}


