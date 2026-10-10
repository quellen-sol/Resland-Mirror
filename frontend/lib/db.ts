import { redirect } from "next/navigation";
import type { SessionData } from "@auth0/nextjs-auth0/types";
import { auth0 } from "./auth0";
import { isRevokedByDeletion } from "./account";
import { db } from "../prisma/db";

/** True when the session belongs to an account that was deleted (an
 *  account_deletion row exists and the session predates the deletion). Such
 *  a session is signed out: no user row is read or re-created for it, or a
 *  device still signed in elsewhere could rebuild the deleted account. */
export async function isRevokedSession(session: SessionData): Promise<boolean> {
    const deletion = await db.orm.public.AccountDeletion
        .where((d) => d.auth0_id.eq(session.user.sub))
        .first();
    if (!deletion) return false;
    return isRevokedByDeletion(
        session.internal?.createdAt,
        deletion.auth0_deleted_at == null
            ? null
            : new Date(String(deletion.auth0_deleted_at)),
    );
}

/** Where to send someone getUser() returned nothing for: a deleted
 *  account's session is signed out (clearing its cookie) instead of being
 *  sent back through login. */
export async function signedOutTarget(): Promise<string> {
    const session = await auth0.getSession();
    return session && (await isRevokedSession(session))
        ? "/auth/logout"
        : "/auth/login";
}

export async function getUser() {
    const session = await auth0.getSession();
    if (!session || !session.user.email) {
        return null;
    }
    if (await isRevokedSession(session)) {
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

/** User row or a redirect — sends brand-new accounts to onboarding. */
export async function requireOnboardedUser() {
    const user = await getUser();
    if (!user) redirect(await signedOutTarget());
    if (!user.has_onboarded) redirect("/onboarding");
    return user;
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

/** Finished system design interviews, newest first — the practice history. */
export async function getUserSystemDesignHistory(userId: string) {
    return db.orm.public.UserSystemDesignSession.where((s) =>
        s.user_id.eq(userId),
    )
        .where((s) => s.status.eq("COMPLETED"))
        .orderBy((s) => s.completed_at.desc())
        .all();
}
