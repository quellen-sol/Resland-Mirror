import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { getAccessTokenOrLogin } from "@/lib/auth";
import { getUserTailoredResume, requireOnboardedUser } from "@/lib/db";
import { parseTailoredContent } from "@/lib/tailored";
import TailoredEditor from "./tailored-editor";
import Backdrop from "@/components/backdrop";

export const metadata: Metadata = { title: "Tailored Resume" };

export default async function TailoredDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const user = await requireOnboardedUser();
  const accessToken = await getAccessTokenOrLogin(`/tailored/${id}`);

  const row = await getUserTailoredResume(user.auth0_id, id);
  if (!row) notFound();

  const content = parseTailoredContent(row.content);

  return (
    <div className="relative flex flex-1 overflow-hidden bg-zinc-950 font-sans">
      <Backdrop />
      <main className="relative mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-10">
        <TailoredEditor
          accessToken={accessToken}
          id={row.id}
          initialCompany={row.company_name ?? ""}
          initialRole={row.role ?? ""}
          jobDescription={row.job_description}
          initialContent={
            content ?? { summary: null, experiences: [], skill_groups: [] }
          }
          contentReadable={content !== null}
        />
      </main>
    </div>
  );
}
