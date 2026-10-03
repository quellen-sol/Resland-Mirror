import type { Metadata } from "next";
import { getAccessTokenOrLogin } from "@/lib/auth";
import { getUserProfileData, requireOnboardedUser } from "@/lib/db";
import TailorForm from "./tailor-form";
import Backdrop from "@/components/backdrop";

export const metadata: Metadata = { title: "Tailor Resume" };

export default async function TailorPage() {
  const user = await requireOnboardedUser();
  const accessToken = await getAccessTokenOrLogin("/tailor");

  const { experiences, skills } = await getUserProfileData(user.auth0_id);

  return (
    <div className="relative flex flex-1 overflow-hidden bg-zinc-950 font-sans">
      <Backdrop />
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
          skills={skills.map((s) => ({ name: s.name, category: s.category }))}
          hasProfile={experiences.length > 0}
        />
      </main>
    </div>
  );
}
