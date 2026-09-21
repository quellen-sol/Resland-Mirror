import { redirect } from "next/navigation";
import { auth0 } from "./auth0";
import { upsertUser } from "./db";

export async function requireUser() {
  const session = await auth0.getSession();
  if (!session) {
    redirect("/auth/login");
  }
  await upsertUser();
  return session.user;
}

export async function getAccessTokenOrLogin(returnTo: string): Promise<string> {
  try {
    return (await auth0.getAccessToken()).token;
  } catch {
    redirect(
      `/auth/logout?returnTo=${encodeURIComponent(`/auth/login?returnTo=${returnTo}`)}`,
    );
  }
}
