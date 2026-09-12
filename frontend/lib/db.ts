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
