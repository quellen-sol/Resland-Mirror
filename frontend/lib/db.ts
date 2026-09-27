import { auth0 } from "./auth0";
import { db } from "../prisma/db";

export async function getUser() {
    const session = await auth0.getSession();
    if (!session || !session.user.email) {
        return null;
    }

    const existing = await db.orm.public.User
        .where((u) => u.auth0_id.eq(session.user.sub))
        .first();
    if (existing) {
        return existing;
    }

    try {
        return await db.orm.public.User.create({ auth0_id: session.user.sub });
    } catch {
        // Lost a create race — the row exists now, fetch it.
        return await db.orm.public.User
            .where((u) => u.auth0_id.eq(session.user.sub))
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
                .where((j) => j.user_id.eq(userId))
                .orderBy((j) => j.created_at.desc())
                .all(),
            db.orm.public.UserBaseSkill.where((s) => s.user_id.eq(userId))
                .orderBy((s) => s.sort_order.asc())
                .all(),
            db.orm.public.UserBaseExperience.where((e) => e.user_id.eq(userId))
                .all(),
            db.orm.public.UserBaseEducation.where((e) => e.user_id.eq(userId)).all(),
            db.orm.public.UserBaseProject.where((p) => p.user_id.eq(userId)).all(),
            db.orm.public.UserSocialLink.where((l) => l.user_id.eq(userId))
                .all(),
        ]);

    const experienceIds = experiences.map((e) => e.id);
    const bullets = experienceIds.length
        ? await db.orm.public.UserBaseExperienceBullet.where((b) =>
              b.user_experience_id.in(experienceIds),
          )
              .orderBy((b) => b.bullet_order.asc())
              .all()
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

export async function getUserTailoredResumes(userId: string) {
    return db.orm.public.UserTailoredResume.where((t) => t.user_id.eq(userId))
        .orderBy((t) => t.created_at.desc())
        .all();
}

export async function getUserTailoredResume(userId: string, id: string) {
    return db.orm.public.UserTailoredResume.where((t) => t.id.eq(id))
        .where((t) => t.user_id.eq(userId))
        .first();
}


