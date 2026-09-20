"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Loader2, Send, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "cn";
import ModelSelect from "@/components/model-select";
import { apiFetch as apiRequest, isInsufficientBalance } from "@/lib/api";

const MAX_JD_CHARS = 10_000;
const POLL_INTERVAL_MS = 3000;
const SESSION_TIMEOUT_MS = 5 * 60 * 1000;

type TailorStatus =
  | "PROCESSING"
  | "WAITING_FOR_INPUT"
  | "COMPLETED"
  | "FAILED"
  | "TIMED_OUT";

interface TailorRun {
  run_id: string;
  status: TailorStatus;
  pending_question?: string | null;
  result?: string | null;
}

interface TailoredResume {
  summary: string | null;
  experiences: {
    experience_id: number;
    bullets: { bullet_id: number; text: string }[];
  }[];
  skills: string[];
}

interface ExperienceMeta {
  id: number;
  title: string;
  company_name: string;
  start_date: string;
  end_date: string | null;
}

function fmtDate(date: string | null) {
  if (!date) return "Present";
  const parsed = new Date(date);
  if (Number.isNaN(parsed.getTime())) return date;
  return parsed.toLocaleDateString("en-US", {
    month: "short",
    year: "numeric",
  });
}

export default function TailorForm({
  accessToken,
  experiences,
  hasProfile,
}: {
  accessToken: string;
  experiences: ExperienceMeta[];
  hasProfile: boolean;
}) {
  const router = useRouter();
  const [jd, setJd] = useState("");
  const [model, setModel] = useState("");
  const [run, setRun] = useState<TailorRun | null>(null);
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const finishedRef = useRef(false);
  const startedAtRef = useRef<number>(0);

  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

  const expById = useMemo(() => {
    const map = new Map<number, ExperienceMeta>();
    for (const e of experiences) map.set(e.id, e);
    return map;
  }, [experiences]);

  async function apiFetch(path: string, init?: RequestInit) {
    return apiRequest(accessToken, `/tailor${path}`, init);
  }

  async function start() {
    const text = jd.trim();
    if (!text || run || !apiBaseUrl) return;
    setBusy(true);
    try {
      startedAtRef.current = Date.now();
      const { run_id } = await apiFetch("", {
        method: "POST",
        body: JSON.stringify({ job_description: text, model: model || null }),
      });
      setRun({ run_id, status: "PROCESSING" });
    } catch (error) {
      if (isInsufficientBalance(error)) {
        toast.error("Insufficient balance", {
          description: "Top up to keep going.",
          action: {
            label: "Top up",
            onClick: () => router.push("/billing"),
          },
        });
      } else {
        toast.error("Couldn't start tailoring", {
          description: error instanceof Error ? error.message : String(error),
        });
      }
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    if (!run) return;
    if (run.status !== "PROCESSING") return;
    if (finishedRef.current) return;

    let cancelled = false;
    const interval = setInterval(async () => {
      if (Date.now() - startedAtRef.current > SESSION_TIMEOUT_MS) {
        clearInterval(interval);
        setRun((r) => (r ? { ...r, status: "TIMED_OUT" } : r));
        void apiFetch(`/${run.run_id}/dismiss`, { method: "POST" }).catch(
          () => {},
        );
        return;
      }
      try {
        const data = (await apiFetch(`/${run.run_id}`)) as Omit<
          TailorRun,
          "run_id"
        >;
        if (cancelled) return;
        setRun((r) => (r ? { ...r, ...data } : r));
      } catch {
        // Transient network error — retry on next tick.
      }
    }, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [run?.run_id, run?.status]);

  async function sendAnswer() {
    const text = answer.trim();
    if (!text || !run) return;
    setBusy(true);
    try {
      await apiFetch(`/${run.run_id}/answer`, {
        method: "POST",
        body: JSON.stringify({ text }),
      });
      setAnswer("");
      setRun((r) => (r ? { ...r, status: "PROCESSING" } : r));
    } catch (error) {
      toast.error("Couldn't send answer", {
        description: error instanceof Error ? error.message : String(error),
      });
    } finally {
      setBusy(false);
    }
  }

  async function reset() {
    finishedRef.current = true;
    try {
      if (run) {
        await apiFetch(`/${run.run_id}/dismiss`, { method: "POST" });
      }
    } catch {
      // Dismiss is best-effort — reset regardless.
    }
    setRun(null);
    setJd("");
    setAnswer("");
  }

  let tailored: TailoredResume | null = null;
  if (run?.result) {
    try {
      tailored = JSON.parse(run.result) as TailoredResume;
    } catch {
      tailored = null;
    }
  }

  const running = run?.status === "PROCESSING";
  const waiting = run?.status === "WAITING_FOR_INPUT";
  const done = run?.status === "COMPLETED";
  const failed = run?.status === "FAILED";
  const timedOut = run?.status === "TIMED_OUT";

  return (
    <div className="flex flex-col gap-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="bg-gradient-to-r from-purple-300 to-violet-500 bg-clip-text text-3xl font-semibold text-transparent">
            Tailor resume
          </h1>
          <p className="mt-1 text-sm text-zinc-400">
            Paste a job description — the agent rewrites and reorders your
            bullets to match it.
          </p>
        </div>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1.5 text-sm text-zinc-500 underline-offset-4 hover:text-zinc-300 hover:underline"
        >
          <ArrowLeft className="size-3.5" /> Dashboard
        </Link>
      </header>

      {!hasProfile && !run && (
        <Card className="border-amber-500/30 bg-amber-500/5 text-zinc-100">
          <CardContent className="pt-6 text-sm text-amber-200">
            You have no work experience yet —{" "}
            <Link
              href="/dashboard"
              className="underline underline-offset-4 hover:text-amber-100"
            >
              upload a resume
            </Link>{" "}
            first so there&apos;s something to tailor.
          </CardContent>
        </Card>
      )}

      {/* Job description input */}
      {!run && hasProfile && (
        <Card className="border-zinc-800 bg-zinc-900/80 text-zinc-100">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Sparkles className="size-4 text-purple-400" /> Job description
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <Textarea
              value={jd}
              onChange={(e) => setJd(e.target.value.slice(0, MAX_JD_CHARS))}
              placeholder="Paste the full job description here…"
              className="min-h-48 border-zinc-700 bg-zinc-950/50 text-zinc-200 placeholder:text-zinc-600 focus-visible:border-purple-500 focus-visible:ring-purple-500/30"
            />
            <div className="flex items-center justify-between">
              <span
                className={cn(
                  "text-xs",
                  jd.length >= MAX_JD_CHARS
                    ? "text-amber-400"
                    : "text-zinc-600",
                )}
              >
                {jd.length.toLocaleString()} / {MAX_JD_CHARS.toLocaleString()}
              </span>
              <div className="flex items-center gap-2">
                <ModelSelect
                  accessToken={accessToken}
                  value={model}
                  onChange={setModel}
                  disabled={busy}
                />
                <Button
                  onClick={start}
                  disabled={busy || !jd.trim()}
                className="border-0 bg-gradient-to-r from-violet-600 to-purple-600 text-white hover:from-violet-500 hover:to-purple-500"
              >
                {busy ? (
                  <Loader2 className="animate-spin" />
                ) : (
                  <>
                    <Sparkles /> Tailor
                  </>
                )}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* In-flight states */}
      {running && (
        <div className="flex items-center gap-2 text-sm text-zinc-400">
          <Loader2 className="size-4 animate-spin text-purple-400" />
          Tailoring your resume…
        </div>
      )}

      {waiting && (
        <Card className="border-purple-500/30 bg-zinc-900/80 text-zinc-100">
          <CardContent className="flex flex-col gap-3 pt-6">
            <div className="rounded-lg border border-purple-500/30 bg-purple-500/10 p-3 text-sm text-purple-200">
              {run.pending_question}
            </div>
            <div className="flex gap-2">
              <Input
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    void sendAnswer();
                  }
                }}
                placeholder="Your answer…"
                className="border-zinc-700 bg-zinc-950/50 text-zinc-200 placeholder:text-zinc-600 focus-visible:border-purple-500 focus-visible:ring-purple-500/30"
              />
              <Button
                onClick={sendAnswer}
                disabled={busy || !answer.trim()}
                className="border-0 bg-gradient-to-r from-violet-600 to-purple-600 text-white hover:from-violet-500 hover:to-purple-500"
              >
                <Send />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {failed && (
        <Card className="border-red-500/30 bg-zinc-900/80 text-zinc-100">
          <CardContent className="flex flex-col gap-3 pt-6">
            <p className="text-sm text-red-400">
              Something went wrong while tailoring — try again.
            </p>
            <div>
              <Button
                variant="outline"
                onClick={reset}
                className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
              >
                Start over
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {timedOut && (
        <Card className="border-amber-500/30 bg-zinc-900/80 text-zinc-100">
          <CardContent className="flex flex-col gap-3 pt-6">
            <p className="text-sm text-amber-400">
              This is taking too long — we couldn&apos;t finish the request.
            </p>
            <div>
              <Button
                variant="outline"
                onClick={reset}
                className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
              >
                Start over
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tailored result */}
      {done && tailored && (
        <div className="flex flex-col gap-6">
          {tailored.summary && (
            <Card className="border-zinc-800 bg-zinc-900/80 text-zinc-100">
              <CardHeader>
                <CardTitle className="text-lg">Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm whitespace-pre-wrap text-zinc-300">
                  {tailored.summary}
                </p>
              </CardContent>
            </Card>
          )}

          <Card className="border-zinc-800 bg-zinc-900/80 text-zinc-100">
            <CardHeader>
              <CardTitle className="text-lg">Experience</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              {tailored.experiences.map((exp) => {
                const meta = expById.get(exp.experience_id);
                return (
                  <div
                    key={exp.experience_id}
                    className="flex flex-col gap-1.5"
                  >
                    <div className="flex items-baseline justify-between gap-2">
                      <span className="font-medium text-zinc-100">
                        {meta?.title ?? `Experience #${exp.experience_id}`}
                        {meta && (
                          <span className="text-zinc-400">
                            {" "}
                            · {meta.company_name}
                          </span>
                        )}
                      </span>
                      {meta && (
                        <span className="shrink-0 text-xs text-zinc-500">
                          {fmtDate(meta.start_date)} —{" "}
                          {fmtDate(meta.end_date)}
                        </span>
                      )}
                    </div>
                    <ul className="list-inside list-disc text-sm text-zinc-300">
                      {exp.bullets.map((b) => (
                        <li key={b.bullet_id}>{b.text}</li>
                      ))}
                    </ul>
                  </div>
                );
              })}
            </CardContent>
          </Card>

          {tailored.skills.length > 0 && (
            <Card className="border-zinc-800 bg-zinc-900/80 text-zinc-100">
              <CardHeader>
                <CardTitle className="text-lg">Skills</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {tailored.skills.map((skill) => (
                    <span
                      key={skill}
                      className="rounded-md border border-purple-500/30 bg-purple-500/10 px-2 py-0.5 text-sm text-purple-200"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          <div className="flex justify-end">
            <Button
              variant="outline"
              onClick={reset}
              className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
            >
              Tailor another job
            </Button>
          </div>
        </div>
      )}

      {done && !tailored && (
        <Card className="border-red-500/30 bg-zinc-900/80 text-zinc-100">
          <CardContent className="flex flex-col gap-3 pt-6">
            <p className="text-sm text-red-400">
              The agent finished but returned an unreadable result — try again.
            </p>
            <div>
              <Button
                variant="outline"
                onClick={reset}
                className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
              >
                Start over
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
