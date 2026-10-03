"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Bookmark,
  Briefcase,
  Check,
  Loader2,
  Send,
  Sparkles,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "cn";
import ModelSelect from "@/components/model-select";
import {
  ApiError,
  apiFetch as apiRequest,
  describeApiError,
  isInsufficientBalance,
} from "@/lib/api";
import ApiUnavailable from "@/components/api-unavailable";
import HelpTip from "@/components/help-tip";
import { groupSkills } from "@/lib/skills";

const MAX_JD_CHARS = 10_000;
const POLL_INTERVAL_MS = 3000;
const SESSION_TIMEOUT_MS = 5 * 60 * 1000;

type TailorStatus =
  | "PROCESSING"
  | "WAITING_FOR_INPUT"
  | "COMPLETED"
  | "FAILED"
  | "TIMED_OUT"
  | "GONE"
  | "UNREACHABLE";

interface TailorRun {
  run_id: string;
  status: TailorStatus;
  job_description?: string;
  company_name?: string | null;
  role?: string | null;
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
  skills,
  hasProfile,
}: {
  accessToken: string;
  experiences: ExperienceMeta[];
  skills: { name: string; category: string | null }[];
  hasProfile: boolean;
}) {
  const router = useRouter();
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [jd, setJd] = useState("");
  const [model, setModel] = useState("");
  const [run, setRun] = useState<TailorRun | null>(null);
  const [checked, setChecked] = useState(false);
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [savedId, setSavedId] = useState<string | null>(null);
  const finishedRef = useRef(false);
  const startedAtRef = useRef<number>(0);
  const consecutiveFailuresRef = useRef(0);
  const resumeNotifiedRef = useRef(false);

  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

  const expById = useMemo(() => {
    const map = new Map<number, ExperienceMeta>();
    for (const e of experiences) map.set(e.id, e);
    return map;
  }, [experiences]);

  const skillCategory = useMemo(() => {
    const map = new Map<string, string | null>();
    for (const s of skills) map.set(s.name, s.category);
    return map;
  }, [skills]);

  async function apiFetch(path: string, init?: RequestInit) {
    return apiRequest(accessToken, `/tailor${path}`, init);
  }

  function notifyResumed() {
    if (resumeNotifiedRef.current) return;
    resumeNotifiedRef.current = true;
    // An unfinished run resumes — its credits weren't lost; the user still
    // has to finish or cancel it.
    toast.info("Resumed your in-progress tailoring", {
      description:
        "An unfinished session is still open — continue it here, or Cancel to discard it.",
    });
  }

  // An outstanding (non-COMPLETED) run is unresolved work — reattach to it
  // on mount instead of offering a fresh form.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const status = (await apiFetch("/active")) as TailorRun;
        if (cancelled) return;
        startedAtRef.current = Date.now();
        consecutiveFailuresRef.current = 0;
        setRun(status);
        notifyResumed();
      } catch {
        // 404 = nothing outstanding; anything else also falls through to
        // the entry form (a failed start will toast its own error).
      } finally {
        if (!cancelled) setChecked(true);
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function start() {
    const text = jd.trim();
    const companyName = company.trim();
    const roleName = role.trim();
    if (!text || !companyName || !roleName || run || !apiBaseUrl) return;
    setBusy(true);
    finishedRef.current = false;
    consecutiveFailuresRef.current = 0;
    try {
      startedAtRef.current = Date.now();
      const { run_id, resumed } = (await apiFetch("", {
        method: "POST",
        body: JSON.stringify({
          job_description: text,
          company_name: companyName,
          role: roleName,
          model: model || null,
        }),
      })) as { run_id: string; resumed?: boolean };
      if (resumed) notifyResumed();
      try {
        const status = (await apiFetch(`/${run_id}`)) as Omit<
          TailorRun,
          "run_id"
        >;
        setRun({ run_id, ...status });
      } catch {
        setRun({ run_id, status: "PROCESSING" });
      }
    } catch (error) {
      if (isInsufficientBalance(error)) {
        toast.error("Insufficient balance", {
          description: "Top up to keep going.",
          action: {
            label: "Top Up",
            onClick: () => router.push("/billing"),
          },
        });
      } else {
        toast.error("Couldn't start tailoring", {
          description: describeApiError(error),
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
        consecutiveFailuresRef.current = 0;
        setRun((r) => {
          if (!r) return r;
          if (data.status === "PROCESSING") startedAtRef.current = Date.now();
          return { ...r, ...data };
        });
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) {
          setRun((r) => (r ? { ...r, status: "GONE" } : r));
          clearInterval(interval);
          return;
        }
        consecutiveFailuresRef.current += 1;
        if (consecutiveFailuresRef.current >= 5) {
          setRun((r) => (r ? { ...r, status: "UNREACHABLE" } : r));
          clearInterval(interval);
        }
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
      startedAtRef.current = Date.now();
      consecutiveFailuresRef.current = 0;
      setRun((r) => (r ? { ...r, status: "PROCESSING" } : r));
    } catch (error) {
      toast.error("Couldn't send answer", {
        description: describeApiError(error),
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
    setCompany("");
    setRole("");
    setAnswer("");
    setSavedId(null);
  }

  async function save() {
    if (!run || savedId) return;
    setBusy(true);
    try {
      const { tailored_id } = (await apiFetch(`/${run.run_id}/save`, {
        method: "POST",
      })) as { tailored_id: string };
      setSavedId(tailored_id);
      toast.success("Saved to Tailored Resumes", {
        action: {
          label: "Open",
          onClick: () => router.push(`/tailored/${tailored_id}`),
        },
      });
    } catch (error) {
      toast.error("Couldn't save", { description: describeApiError(error) });
    } finally {
      setBusy(false);
    }
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
  const gone = run?.status === "GONE";
  const unreachable = run?.status === "UNREACHABLE";

  return (
    <div className="flex flex-col gap-6">
      <header className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-semibold tracking-[-0.03em]">
              Tailor Resume
            </h1>
            <HelpTip title="Tailor Resume">
              <p>
                Paste a job description and AI rewrites and reorders your
                bullets to match it.
              </p>
              <p>
                Results aren&apos;t saved automatically — click Save to
                Tailored Resumes to keep one. Saved resumes live on your
                Tailored Resumes board, where you can keep editing and export
                them.
              </p>
              <p>
                Tailoring draws from your balance — the cost depends on how
                much work it takes and the model you pick.
              </p>
            </HelpTip>
          </div>
          <p className="mt-1 text-sm text-zinc-400">
            Paste a job description — AI rewrites and reorders your bullets to
            match it.
          </p>
        </div>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1.5 text-sm text-zinc-500 underline-offset-4 hover:text-zinc-300 hover:underline"
        >
          <ArrowLeft className="size-3.5" /> Dashboard
        </Link>
      </header>

      {checked && !hasProfile && !run && (
        <Card className="bg-amber-500/5 ring-amber-500/30">
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
      {checked && !run && hasProfile && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Sparkles className="size-4 text-brand-400" /> Job Description
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <Input
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                placeholder="Company name"
                aria-label="Company name"
                className="border-zinc-700 bg-zinc-950/50 text-zinc-200 placeholder:text-zinc-600 focus-visible:border-brand-500 focus-visible:ring-brand-500/30"
              />
              <Input
                value={role}
                onChange={(e) => setRole(e.target.value)}
                placeholder="Role (e.g. Senior Backend Engineer)"
                aria-label="Role"
                className="border-zinc-700 bg-zinc-950/50 text-zinc-200 placeholder:text-zinc-600 focus-visible:border-brand-500 focus-visible:ring-brand-500/30"
              />
            </div>
            <Textarea
              value={jd}
              onChange={(e) => setJd(e.target.value.slice(0, MAX_JD_CHARS))}
              placeholder="Paste the full job description here…"
              className="min-h-48 border-zinc-700 bg-zinc-950/50 text-zinc-200 placeholder:text-zinc-600 focus-visible:border-brand-500 focus-visible:ring-brand-500/30"
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
                  jobKind="TAILOR"
                />
                <Button
                  onClick={start}
                  disabled={
                    busy || !jd.trim() || !company.trim() || !role.trim()
                  }
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

      {/* Active run — job posting next to the live status/result */}
      {run && (running || waiting || done) && (
        <div className="grid gap-6 lg:grid-cols-5">
          <Card className="h-fit lg:sticky lg:top-6 lg:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Briefcase className="size-4 text-brand-400" /> Job Posting
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-3 text-sm">
              <dl className="grid grid-cols-[4.5rem_1fr] gap-x-3 gap-y-1.5">
                <dt className="text-zinc-500">Role</dt>
                <dd className="text-zinc-100">{run.role || "—"}</dd>
                <dt className="text-zinc-500">Company</dt>
                <dd className="text-zinc-100">{run.company_name || "—"}</dd>
              </dl>
              <p className="max-h-96 overflow-y-auto rounded-md border border-zinc-800 bg-zinc-950/50 p-3 whitespace-pre-wrap text-zinc-300">
                {run.job_description}
              </p>
            </CardContent>
          </Card>

          <div className="flex flex-col gap-6 lg:col-span-3">
            {running && (
              <div className="flex items-center gap-2 text-sm text-zinc-400">
                <Loader2 className="size-4 animate-spin text-brand-400" />
                {tailored
                  ? "Refining your resume…"
                  : "Tailoring your resume…"}
              </div>
            )}

            {waiting && !tailored && (
              <Card className="ring-brand-500/30">
                <CardContent className="flex flex-col gap-3 pt-6">
                  <div className="rounded-lg border border-brand-500/30 bg-brand-500/10 p-3 text-sm text-brand-200">
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
                      className="border-zinc-700 bg-zinc-950/50 text-zinc-200 placeholder:text-zinc-600 focus-visible:border-brand-500 focus-visible:ring-brand-500/30"
                    />
                    <Button
                      onClick={sendAnswer}
                      disabled={busy || !answer.trim()}
                    >
                      <Send />
                    </Button>
                    <Button
                      variant="outline"
                      onClick={reset}
                      className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
                    >
                      Cancel
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {tailored && (
              <>
                {tailored.summary && (
                  <Card>
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

                <Card>
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
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg">Skills</CardTitle>
                    </CardHeader>
                    <CardContent className="flex flex-col gap-3">
                      {groupSkills(
                        tailored.skills.map((name) => ({
                          name,
                          category: skillCategory.get(name) ?? null,
                        })),
                      ).map((group, gi) => (
                        <div key={group.category ?? `ungrouped-${gi}`}>
                          {group.category !== null && (
                            <p className="mb-1.5 text-xs font-medium tracking-wide text-zinc-500 uppercase">
                              {group.category}
                            </p>
                          )}
                          <div className="flex flex-wrap gap-2">
                            {group.skills.map((skill) => (
                              <span
                                key={skill}
                                className="rounded-md border border-brand-500/30 bg-brand-500/10 px-2 py-0.5 text-sm text-brand-200"
                              >
                                {skill}
                              </span>
                            ))}
                          </div>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                )}
              </>
            )}

            {waiting && tailored && (
              <Card className="ring-brand-500/30">
                <CardContent className="flex flex-col gap-3 pt-6">
                  <div className="rounded-lg border border-brand-500/30 bg-brand-500/10 p-3 text-sm text-brand-200">
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
                      placeholder="Describe a tweak, or reply 'done'…"
                      className="border-zinc-700 bg-zinc-950/50 text-zinc-200 placeholder:text-zinc-600 focus-visible:border-brand-500 focus-visible:ring-brand-500/30"
                    />
                    <Button
                      onClick={sendAnswer}
                      disabled={busy || !answer.trim()}
                    >
                      <Send />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {tailored && (waiting || done) && (
              <div className="flex justify-end gap-2">
                {savedId ? (
                  <Link
                    href={`/tailored/${savedId}`}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-brand-500/40 bg-brand-500/10 px-2.5 py-1.5 text-sm font-medium text-brand-200 hover:bg-brand-500/20 [&_svg]:size-4"
                  >
                    <Check /> Saved — Open It
                  </Link>
                ) : (
                  <Button
                    onClick={save}
                    disabled={busy}
                  >
                    {busy ? <Loader2 className="animate-spin" /> : <Bookmark />}{" "}
                    Save to Tailored Resumes
                  </Button>
                )}
                <Button
                  variant="outline"
                  onClick={reset}
                  className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
                >
                  Cancel
                </Button>
              </div>
            )}
          </div>
        </div>
      )}

      {failed && (
        <Card className="ring-red-500/30">
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
                Start Over
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {timedOut && (
        <Card className="ring-amber-500/30">
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
                Start Over
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {gone && (
        <Card className="ring-amber-500/30">
          <CardContent className="flex flex-col gap-3 pt-6">
            <p className="text-sm text-amber-400">
              This session no longer exists — start a new one.
            </p>
            <Button
              variant="outline"
              onClick={reset}
              className="self-start border-zinc-700 text-zinc-300 hover:bg-zinc-800"
            >
              Start Over
            </Button>
          </CardContent>
        </Card>
      )}

      {unreachable && (
        <ApiUnavailable
          onRetry={() => {
            consecutiveFailuresRef.current = 0;
            startedAtRef.current = Date.now();
            setRun((r) => (r ? { ...r, status: "PROCESSING" } : r));
          }}
        />
      )}

      {done && !tailored && (
        <Card className="ring-red-500/30">
          <CardContent className="flex flex-col gap-3 pt-6">
            <p className="text-sm text-red-400">
              We couldn&apos;t read the tailored result — try again.
            </p>
            <div>
              <Button
                variant="outline"
                onClick={reset}
                className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
              >
                Start Over
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
