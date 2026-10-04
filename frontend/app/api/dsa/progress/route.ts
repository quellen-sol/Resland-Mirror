import { NextResponse } from "next/server";
import { DSA_TOPICS } from "@/content/dsa/index.ts";
import { getUser } from "@/lib/db";
import { parseProgressUpdate, type DsaProgressResponse } from "@/lib/dsa";
import { db } from "@/prisma/db";

// Study progress for the public /dsa pages. They're prerendered, so they ask
// here after load whether anyone is signed in and what they've studied.

const KNOWN_TOPICS = new Set(DSA_TOPICS.map((t) => t.slug));

async function studiedTopics(userId: string) {
  const rows = await db.orm.public.UserDsaProgress.where((p) =>
    p.user_id.eq(userId),
  ).all();
  // A topic removed from content/dsa leaves its rows behind; hide them.
  return rows.map((r) => r.topic).filter((t) => KNOWN_TOPICS.has(t));
}

// Signed-out visitors are the normal case on a public page, so they get a 200
// that says so rather than a 401.
export async function GET() {
  const user = await getUser();
  const body: DsaProgressResponse = user
    ? { signedIn: true, studied: await studiedTopics(user.auth0_id) }
    : { signedIn: false };
  return NextResponse.json(body);
}

export async function PUT(request: Request) {
  const user = await getUser();
  if (!user) {
    return NextResponse.json(
      { detail: "Sign in to track your progress" },
      { status: 401 },
    );
  }

  const update = parseProgressUpdate(
    await request.json().catch(() => null),
    KNOWN_TOPICS,
  );
  if (!update) {
    return NextResponse.json({ detail: "Unknown topic" }, { status: 400 });
  }

  const row = { user_id: user.auth0_id, topic: update.topic };
  if (update.studied) {
    // Marking twice is a no-op, not a unique-constraint error.
    await db.orm.public.UserDsaProgress.upsert({
      create: row,
      update: {},
      conflictOn: row,
    });
  } else {
    await db.orm.public.UserDsaProgress.where(row).deleteAll();
  }

  const body: DsaProgressResponse = {
    signedIn: true,
    studied: await studiedTopics(user.auth0_id),
  };
  return NextResponse.json(body);
}
