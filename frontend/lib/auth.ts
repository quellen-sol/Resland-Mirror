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
