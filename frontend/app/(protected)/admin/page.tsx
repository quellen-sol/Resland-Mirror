import { notFound, redirect } from "next/navigation";
import type { Metadata } from "next";
import { getAccessTokenOrLogin } from "@/lib/auth";
import { getUser } from "@/lib/db";
import AdminClient from "./admin-client";
import Backdrop from "@/components/backdrop";

export const metadata: Metadata = { title: "Admin" };

export default async function AdminPage() {
  // Plain getUser(), not requireOnboardedUser(): the site_admin check must run
  // first so non-admins get the 404 and admins aren't gated on onboarding.
  const user = await getUser();
  if (!user) redirect("/auth/login");
  // Hidden route — pretend it doesn't exist for non-admins.
  if (!user.site_admin) notFound();
  const accessToken = await getAccessTokenOrLogin("/admin");

  return (
    <div className="relative flex flex-1 overflow-hidden bg-zinc-950 font-sans">
      <Backdrop />
      <main className="relative mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-10">
        <AdminClient accessToken={accessToken} />
      </main>
    </div>
  );
}
