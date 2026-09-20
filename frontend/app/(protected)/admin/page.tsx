import { notFound, redirect } from "next/navigation";
import { auth0 } from "@/lib/auth0";
import { getUser } from "@/lib/db";
import AdminClient from "./admin-client";

export default async function AdminPage() {
  const user = await getUser();
  if (!user) redirect("/auth/login");
  // Hidden route — pretend it doesn't exist for non-admins.
  if (!user.site_admin) notFound();
  const { token: accessToken } = await auth0.getAccessToken();

  return (
    <div className="relative flex flex-1 overflow-hidden bg-zinc-950 font-sans">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-96 bg-[radial-gradient(ellipse_at_top,var(--color-purple-900)_0%,transparent_70%)] opacity-40" />
      <main className="relative mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-10">
        <AdminClient accessToken={accessToken} />
      </main>
    </div>
  );
}
