import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, Sparkles } from "lucide-react";
import { getAccessTokenOrLogin } from "@/lib/auth";
import { getUserTailoredResumes, requireOnboardedUser } from "@/lib/db";
import HelpTip from "@/components/help-tip";
import TailoredBoard from "./tailored-board";
import Backdrop from "@/components/backdrop";

export const metadata: Metadata = { title: "Tailored Resumes" };

export default async function TailoredPage() {
  const user = await requireOnboardedUser();
  const accessToken = await getAccessTokenOrLogin("/tailored");

  const tailored = await getUserTailoredResumes(user.auth0_id);

  return (
    <div className="relative flex flex-1 overflow-hidden bg-zinc-950 font-sans">
      <Backdrop />
      <main className="relative mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-10">
        <header className="flex items-center justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h1 className="text-3xl font-semibold tracking-[-0.03em]">
                Tailored Resumes
              </h1>
              <HelpTip title="Tailored Resumes">
                <p>
                  Each entry is a version of your resume tailored to a specific
                  job posting. Open one to edit the content or export it as a
                  document.
                </p>
              </HelpTip>
            </div>
            <p className="mt-1 text-sm text-zinc-400">
              Saved versions of your resume tailored to a specific job — edit
              one or generate its document.
            </p>
          </div>
          <div className="flex shrink-0 items-center gap-3">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-1.5 text-sm text-zinc-500 underline-offset-4 hover:text-zinc-300 hover:underline"
            >
              <ArrowLeft className="size-3.5" /> Dashboard
            </Link>
            <Link
              href="/tailor"
              className="inline-flex items-center gap-1.5 rounded-lg bg-white px-2.5 py-1.5 text-sm font-medium text-zinc-950 hover:bg-zinc-200 [&_svg]:size-4"
            >
              <Sparkles /> Tailor Resume
            </Link>
          </div>
        </header>

        <TailoredBoard
          accessToken={accessToken}
          items={tailored.map((t) => ({
            id: t.id,
            company_name: t.company_name,
            role: t.role,
            created_at: new Date(String(t.created_at)).toISOString(),
            generated_at: t.generated_at
              ? new Date(String(t.generated_at)).toISOString()
              : null,
          }))}
        />
      </main>
    </div>
  );
}
