import { redirect } from "next/navigation";
import { auth0 } from "@/lib/auth0";
import { getUser, getUserProfileData } from "@/lib/db";
import TailorForm from "./tailor-form";

export default async function TailorPage() {
  const user = await getUser();
  if (!user) redirect("/auth/login");
  const { token: accessToken } = await auth0.getAccessToken();

  const { experiences } = await getUserProfileData(user.auth0_id);

  return (
    <div className="relative flex flex-1 overflow-hidden bg-zinc-950 font-sans">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-96 bg-[radial-gradient(ellipse_at_top,var(--color-purple-900)_0%,transparent_70%)] opacity-40" />
      <main className="relative mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-10">
        <TailorForm
          accessToken={accessToken}
          experiences={experiences.map((e) => ({
            id: e.id,
            title: e.title,
            company_name: e.company_name,
            start_date: e.start_date,
            end_date: e.end_date,
          }))}
          hasProfile={experiences.length > 0}
        />
      </main>
    </div>
  );
}
