"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Briefcase,
  Dices,
  Library,
  Loader2,
  Network,
  Play,
  Target,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import HelpTip from "@/components/help-tip";
import ModelSelect from "@/components/model-select";
import {
  apiFetch,
  describeApiError,
  isInsufficientBalance,
} from "@/lib/api";
import {
  GRADE_TONE_CLASSES,
  HIRE_SIGNAL_LABELS,
  LEVEL_LABELS,
  dimensionAverages,
  gradeTone,
  weakestDimension,
  type DimensionResult,
  type HireSignal,
  type Level,
  type ProblemSummary,
  type SessionStatus,
} from "@/lib/system-design";
import { cn } from "cn";

interface TailoredOption {
  id: string;
  company_name: string | null;
  role: string | null;
}

interface HistoryItem {
  id: string;
  title: string | null;
  level: Level;
  source: "BANK" | "JOB";
  company_name: string | null;
  letter_grade: string | null;
  hire_signal: HireSignal | null;
  completed_at: string | null;
  dimensions: DimensionResult[] | null;
}

const LEVELS: Level[] = ["MID", "SENIOR", "STAFF"];

const DIFFICULTY_STYLES: Record<ProblemSummary["difficulty"], string> = {
  EASY: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
  MEDIUM: "border-amber-500/30 bg-amber-500/10 text-amber-300",
  HARD: "border-red-500/30 bg-red-500/10 text-red-300",
};

function fmtDate(iso: string | null) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function tailoredLabel(t: TailoredOption) {
  const role = t.role || "Tailored Resume";
  return t.company_name ? `${role} · ${t.company_name}` : role;
}

export default function SystemDesignHome({
  accessToken,
  tailoredResumes,
  history,
  preselectTailored,
}: {
  accessToken: string;
  tailoredResumes: TailoredOption[];
  history: HistoryItem[];
  preselectTailored: string | null;
}) {
  const router = useRouter();
  const preselected = tailoredResumes.some((t) => t.id === preselectTailored);
  const [source, setSource] = useState<"BANK" | "JOB">(
    preselected ? "JOB" : "BANK",
  );
  const [problems, setProblems] = useState<ProblemSummary[]>([]);
  const [problemId, setProblemId] = useState<string | null>(null);
  const [tailoredId, setTailoredId] = useState<string>(
    preselected ? preselectTailored! : (tailoredResumes[0]?.id ?? ""),
  );
  const [level, setLevel] = useState<Level>("SENIOR");
  const [model, setModel] = useState("");
  const [active, setActive] = useState<SessionStatus | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    apiFetch(accessToken, "/system-design/problems")
      .then((data: { problems: ProblemSummary[] }) => {
        if (!cancelled) setProblems(data.problems);
      })
      .catch(() => {});
    apiFetch(accessToken, "/system-design/active")
      .then((data: SessionStatus) => {
        if (!cancelled) setActive(data);
      })
      .catch(() => {
        // 404 = nothing in progress.
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  const averages = useMemo(
    () =>
      dimensionAverages(
        history.map((h) => (h.dimensions ? { dimensions: h.dimensions } : null)),
      ),
    [history],
  );
  const weakest = weakestDimension(averages);

  async function start() {
    if (busy) return;
    if (source === "JOB" && !tailoredId) return;
    setBusy(true);
    try {
      const { session_id, resumed } = (await apiFetch(
        accessToken,
        "/system-design",
        {
          method: "POST",
          body: JSON.stringify({
            source,
            problem_id: source === "BANK" ? problemId : null,
            tailored_resume_id: source === "JOB" ? tailoredId : null,
            level,
            model: model || null,
          }),
        },
      )) as { session_id: string; resumed?: boolean };
      if (resumed) {
        toast.info("Resumed your interview in progress", {
          description: "Finish or discard it before starting another.",
        });
      }
      router.push(`/system-design/${session_id}`);
    } catch (error) {
      if (isInsufficientBalance(error)) {
        toast.error("Insufficient balance", {
          description: "Top up to keep going.",
          action: { label: "Top Up", onClick: () => router.push("/billing") },
        });
      } else {
        toast.error("Couldn't start the interview", {
          description: describeApiError(error),
        });
      }
      setBusy(false);
    }
  }

  async function discardActive() {
    if (!active) return;
    try {
      await apiFetch(accessToken, `/system-design/${active.session_id}/dismiss`, {
        method: "POST",
      });
      setActive(null);
    } catch (error) {
      toast.error("Couldn't discard it", { description: describeApiError(error) });
    }
  }

  const tabClass = (on: boolean) =>
    cn(
      "inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors [&_svg]:size-4",
      on
        ? "bg-purple-500/20 text-purple-100"
        : "text-zinc-400 hover:bg-zinc-800/60 hover:text-zinc-200",
    );

  return (
    <div className="flex flex-col gap-6">
      <header className="flex items-center justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h1 className="bg-gradient-to-r from-purple-300 to-violet-500 bg-clip-text text-3xl font-semibold text-transparent">
              System Design Mock
            </h1>
            <HelpTip title="System Design Mock">
              <p>
                A 45-minute mock interview with an AI interviewer. Clarify the
                requirements, estimate the scale, draw your design, then
                answer deep-dive questions about it.
              </p>
              <p>
                Draw with the component palette and connect boxes with arrows
                — the interviewer reads which components connect to which,
                so arrows must be attached at both ends.
              </p>
              <p>
                You get a letter grade, a hire signal, and feedback on each
                part of the rubric. Each interviewer reply draws from your
                balance.
              </p>
            </HelpTip>
          </div>
          <p className="mt-1 text-sm text-zinc-400">
            Practice the system design round with an AI interviewer, then get
            graded on a real rubric.
          </p>
        </div>
        <Link
          href="/dashboard"
          className="inline-flex shrink-0 items-center gap-1.5 text-sm text-zinc-500 underline-offset-4 hover:text-zinc-300 hover:underline"
        >
          <ArrowLeft className="size-3.5" /> Dashboard
        </Link>
      </header>

      {active && (
        <Card className="border-purple-500/30 bg-purple-500/5 text-zinc-100">
          <CardContent className="flex flex-wrap items-center justify-between gap-3 pt-6">
            <div className="text-sm">
              <p className="font-medium text-zinc-100">
                Interview in progress: {active.title ?? "Setting up…"}
              </p>
              <p className="text-zinc-400">
                Finish or discard it before starting another.
              </p>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={discardActive}
                className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
              >
                Discard
              </Button>
              <Button
                onClick={() => router.push(`/system-design/${active.session_id}`)}
                className="border-0 bg-gradient-to-r from-violet-600 to-purple-600 text-white hover:from-violet-500 hover:to-purple-500"
              >
                <Play /> Resume
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {!active && (
        <Card className="border-zinc-800 bg-zinc-900/80 text-zinc-100">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Network className="size-4 text-purple-400" /> New Interview
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-5">
            <div className="flex flex-wrap gap-1 rounded-lg border border-zinc-800 bg-zinc-950/50 p-1 self-start">
              <button
                type="button"
                className={tabClass(source === "BANK")}
                onClick={() => setSource("BANK")}
              >
                <Library /> Practice Bank
              </button>
              <button
                type="button"
                className={tabClass(source === "JOB")}
                onClick={() => setSource("JOB")}
              >
                <Briefcase /> From a Tailored Resume
              </button>
            </div>

            {source === "BANK" && (
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                <button
                  type="button"
                  onClick={() => setProblemId(null)}
                  className={cn(
                    "flex flex-col gap-1 rounded-lg border p-3 text-left transition-colors",
                    problemId === null
                      ? "border-purple-500/60 bg-purple-500/10"
                      : "border-zinc-800 bg-zinc-950/40 hover:border-zinc-700",
                  )}
                >
                  <span className="flex items-center gap-1.5 text-sm font-medium text-zinc-100">
                    <Dices className="size-4 text-purple-400" /> Surprise Me
                  </span>
                  <span className="text-xs text-zinc-400">
                    A random problem you haven&apos;t practiced yet.
                  </span>
                </button>
                {problems.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => setProblemId(p.id)}
                    className={cn(
                      "flex flex-col gap-1 rounded-lg border p-3 text-left transition-colors",
                      problemId === p.id
                        ? "border-purple-500/60 bg-purple-500/10"
                        : "border-zinc-800 bg-zinc-950/40 hover:border-zinc-700",
                    )}
                  >
                    <span className="flex items-center justify-between gap-2">
                      <span className="text-sm font-medium text-zinc-100">
                        {p.title}
                      </span>
                      <span
                        className={cn(
                          "rounded border px-1.5 py-px text-[10px] font-medium tracking-wide",
                          DIFFICULTY_STYLES[p.difficulty],
                        )}
                      >
                        {p.difficulty}
                      </span>
                    </span>
                    <span className="text-xs text-zinc-400">{p.summary}</span>
                  </button>
                ))}
              </div>
            )}

            {source === "JOB" &&
              (tailoredResumes.length ? (
                <div className="flex flex-col gap-1.5">
                  <label
                    htmlFor="sd-tailored"
                    className="text-xs font-medium tracking-wide text-zinc-500 uppercase"
                  >
                    Job
                  </label>
                  <select
                    id="sd-tailored"
                    value={tailoredId}
                    onChange={(e) => setTailoredId(e.target.value)}
                    className="max-w-md rounded-md border border-zinc-700 bg-zinc-950/50 px-2 py-2 text-sm text-zinc-200 focus:border-purple-500 focus:outline-none"
                  >
                    {tailoredResumes.map((t) => (
                      <option key={t.id} value={t.id}>
                        {tailoredLabel(t)}
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-zinc-500">
                    The interviewer writes a problem from this job&apos;s
                    posting: the company&apos;s domain, scale, and stack.
                  </p>
                </div>
              ) : (
                <p className="text-sm text-zinc-400">
                  You have no tailored resumes yet.{" "}
                  <Link
                    href="/tailor"
                    className="text-purple-300 underline underline-offset-4 hover:text-purple-200"
                  >
                    Tailor one to a job
                  </Link>{" "}
                  first, or practice from the bank.
                </p>
              ))}

            <div className="flex flex-wrap items-end justify-between gap-4">
              <div className="flex flex-col gap-1.5">
                <span className="text-xs font-medium tracking-wide text-zinc-500 uppercase">
                  Level
                </span>
                <div className="flex gap-1 rounded-lg border border-zinc-800 bg-zinc-950/50 p-1">
                  {LEVELS.map((l) => (
                    <button
                      key={l}
                      type="button"
                      className={tabClass(level === l)}
                      onClick={() => setLevel(l)}
                    >
                      {LEVEL_LABELS[l]}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <ModelSelect
                  accessToken={accessToken}
                  value={model}
                  onChange={setModel}
                  disabled={busy}
                  jobKind="SYSTEM_DESIGN"
                />
                <Button
                  onClick={start}
                  disabled={busy || (source === "JOB" && !tailoredId)}
                  className="border-0 bg-gradient-to-r from-violet-600 to-purple-600 text-white hover:from-violet-500 hover:to-purple-500"
                >
                  {busy ? <Loader2 className="animate-spin" /> : <Play />} Start
                  Interview
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {history.length > 0 && (
        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="border-zinc-800 bg-zinc-900/80 text-zinc-100 lg:col-span-2">
            <CardHeader>
              <CardTitle className="text-lg">Past Interviews</CardTitle>
            </CardHeader>
            <CardContent className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-zinc-800 text-xs text-zinc-500">
                    <th className="py-2 pr-3 font-medium">Problem</th>
                    <th className="py-2 pr-3 font-medium">Level</th>
                    <th className="py-2 pr-3 font-medium">Grade</th>
                    <th className="py-2 pr-3 font-medium">Signal</th>
                    <th className="py-2 font-medium">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((h) => (
                    <tr
                      key={h.id}
                      className="border-b border-zinc-800/50 last:border-0"
                    >
                      <td className="py-2 pr-3">
                        <Link
                          href={`/system-design/${h.id}`}
                          className="font-medium text-zinc-100 underline-offset-4 hover:text-purple-300 hover:underline"
                        >
                          {h.title ?? "Interview"}
                        </Link>
                        {h.source === "JOB" && h.company_name && (
                          <span className="text-zinc-500"> · {h.company_name}</span>
                        )}
                      </td>
                      <td className="py-2 pr-3 text-zinc-400">
                        {LEVEL_LABELS[h.level] ?? h.level}
                      </td>
                      <td
                        className={cn(
                          "py-2 pr-3 font-semibold",
                          GRADE_TONE_CLASSES[gradeTone(h.letter_grade)],
                        )}
                      >
                        {h.letter_grade ?? "—"}
                      </td>
                      <td className="py-2 pr-3 text-zinc-300">
                        {h.hire_signal ? HIRE_SIGNAL_LABELS[h.hire_signal] : "—"}
                      </td>
                      <td className="py-2 text-zinc-500">{fmtDate(h.completed_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>

          <Card className="h-fit border-zinc-800 bg-zinc-900/80 text-zinc-100">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Target className="size-4 text-purple-400" /> Your Progress
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-3 text-sm">
              {averages.map((a) => (
                <div key={a.key} className="flex flex-col gap-1">
                  <div className="flex justify-between text-zinc-300">
                    <span>{a.label}</span>
                    <span className="text-zinc-500">{a.average.toFixed(1)} / 5</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-zinc-800">
                    <div
                      className={cn(
                        "h-1.5 rounded-full",
                        a.key === weakest?.key ? "bg-amber-400" : "bg-purple-500",
                      )}
                      style={{ width: `${(a.average / 5) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
              {weakest && (
                <p className="mt-1 rounded-md border border-amber-500/30 bg-amber-500/10 p-2 text-xs text-amber-200">
                  Focus next on <strong>{weakest.label}</strong> — it&apos;s
                  your lowest average across {history.length} interview
                  {history.length === 1 ? "" : "s"}.
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
