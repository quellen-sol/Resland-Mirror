import type { Metadata } from "next";
import { getAccessTokenOrLogin } from "@/lib/auth";
import { requireOnboardedUser } from "@/lib/db";
import InterviewRoom from "./interview-room";

export const metadata: Metadata = { title: "System Design Interview" };

export default async function InterviewPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  await requireOnboardedUser();
  const accessToken = await getAccessTokenOrLogin(`/system-design/${id}`);

  return (
    <div className="relative flex flex-1 bg-zinc-950 font-sans">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-96 bg-[radial-gradient(ellipse_at_top,var(--color-purple-900)_0%,transparent_70%)] opacity-40" />
      <main className="relative mx-auto flex w-full max-w-[1600px] flex-col gap-6 px-6 py-8">
        <InterviewRoom accessToken={accessToken} sessionId={id} />
      </main>
    </div>
  );
}
