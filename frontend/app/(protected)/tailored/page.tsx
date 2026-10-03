import { redirect } from "next/navigation";
import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, Sparkles } from "lucide-react";
import { getAccessTokenOrLogin } from "@/lib/auth";
import { getUser, getUserTailoredResumes } from "@/lib/db";
import TailoredBoard from "./tailored-board";

export const metadata: Metadata = { title: "Tailored resumes" };

export default async function TailoredPage() {
  const user = await getUser();
  if (!user) redirect("/auth/login");
  const accessToken = await getAccessTokenOrLogin("/tailored");

  const tailored = await getUserTailoredResumes(user.auth0_id);

  return (
    <div className="relative flex flex-1 overflow-hidden bg-zinc-950 font-sans">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-96 bg-[radial-gradient(ellipse_at_top,var(--color-purple-900)_0%,transparent_70%)] opacity-40" />
      <main className="relative mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-10">
        <header className="flex items-center justify-between gap-4">
          <div className="min-w-0">
            <h1 className="bg-gradient-to-r from-purple-300 to-violet-500 bg-clip-text text-3xl font-semibold text-transparent">
              Tailored resumes
            </h1>
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
              className="inline-flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-violet-600 to-purple-600 px-2.5 py-1.5 text-sm font-medium text-white hover:from-violet-500 hover:to-purple-500 [&_svg]:size-4"
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
