import { auth0 } from "@/lib/auth0";
import { isLikelyBot, parsePageView } from "@/lib/traffic";
import { db } from "@/prisma/db";

// The page-view beacon from components/page-view-tracker.tsx. Public and
// fire-and-forget: it always answers 204, so a rejected view looks the same
// as a recorded one.
const done = () => new Response(null, { status: 204 });

/** Site admins browsing their own site would swamp the numbers. */
async function isSiteAdmin() {
  try {
    const session = await auth0.getSession();
    if (!session) return false;
    const user = await db.orm.public.User.where((u) =>
      u.auth0_id.eq(session.user.sub),
    ).first();
    return Boolean(user?.site_admin);
  } catch {
    return false;
  }
}

export async function POST(request: Request) {
  if (isLikelyBot(request.headers.get("user-agent"))) return done();

  // sendBeacon posts the body as text, so parse it by hand.
  const text = await request.text().catch(() => "");
  if (text.length > 2000) return done();
  let body: unknown = null;
  try {
    body = JSON.parse(text);
  } catch {
    return done();
  }
  const host =
    request.headers.get("x-forwarded-host") ?? request.headers.get("host") ?? "resland.org";
  const row = parsePageView(body, host);
  if (!row || (await isSiteAdmin())) return done();

  try {
    await db.orm.public.PageView.create(row);
  } catch (e) {
    console.error("page_view insert failed", e);
  }
  return done();
}
