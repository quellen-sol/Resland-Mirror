import type { Metadata } from "next";
import { getAccessTokenOrLogin } from "@/lib/auth";
import {
  getUserSystemDesignHistory,
  getUserTailoredResumes,
  requireOnboardedUser,
} from "@/lib/db";
import type { GradeReport, HireSignal, Level } from "@/lib/system-design";
import SystemDesignHome from "./system-design-home";

export const metadata: Metadata = { title: "System Design Mock" };

function parseReport(raw: string | null): GradeReport | null {
  if (!raw) return null;
  try {
    return JSON.parse(raw) as GradeReport;
  } catch {
    return null;
  }
}

export default async function SystemDesignPage({
  searchParams,
}: {
  searchParams: Promise<{ tailored?: string }>;
}) {
  const user = await requireOnboardedUser();
  const accessToken = await getAccessTokenOrLogin("/system-design");
  const { tailored } = await searchParams;

  const [resumes, history] = await Promise.all([
    getUserTailoredResumes(user.auth0_id),
    getUserSystemDesignHistory(user.auth0_id),
  ]);

  return (
    <div className="relative flex flex-1 overflow-hidden bg-zinc-950 font-sans">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-96 bg-[radial-gradient(ellipse_at_top,var(--color-purple-900)_0%,transparent_70%)] opacity-40" />
      <main className="relative mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-10">
        <SystemDesignHome
          accessToken={accessToken}
          tailoredResumes={resumes.map((r) => ({
            id: r.id,
            company_name: r.company_name,
            role: r.role,
          }))}
          history={history.map((s) => ({
            id: s.id,
            title: s.title,
            level: s.level as Level,
            source: s.source as "BANK" | "JOB",
            company_name: s.company_name,
            letter_grade: s.letter_grade,
            hire_signal: s.hire_signal as HireSignal | null,
            completed_at: s.completed_at
              ? new Date(String(s.completed_at)).toISOString()
              : null,
            dimensions: parseReport(s.result)?.dimensions ?? null,
          }))}
          preselectTailored={tailored ?? null}
        />
      </main>
    </div>
  );
}
