import { redirect } from "next/navigation";
import { auth0 } from "./auth0";
import { isRevokedSession, upsertUser } from "./db";

export async function requireUser() {
  const session = await auth0.getSession();
  if (!session) {
    redirect("/auth/login");
  }
  // A session from before its account was deleted (another device, an old
  // tab) is signed out, never given a fresh user row.
  if (await isRevokedSession(session)) {
    redirect("/auth/logout");
  }
  await upsertUser();
  return session.user;
}

export async function getAccessTokenOrLogin(returnTo: string): Promise<string> {
  try {
    return (await auth0.getAccessToken()).token;
  } catch {
    redirect(`/auth/login?returnTo=${encodeURIComponent(returnTo)}`);
  }
}
