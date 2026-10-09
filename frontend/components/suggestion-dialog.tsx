"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Send, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { cn } from "cn";
import MemoryNote from "@/components/memory-note";
import ModelSelect from "@/components/model-select";
import {
  ApiError,
  apiFetch as apiRequest,
  describeApiError,
  isInsufficientBalance,
} from "@/lib/api";
import ApiUnavailable from "@/components/api-unavailable";
import { moreOptionsMessage, parseSuggestionResult } from "@/lib/suggestions";

const POLL_INTERVAL_MS = 3000;
const SESSION_TIMEOUT_MS = 5 * 60 * 1000;

type SuggestionStatus =
  | "PENDING"
  | "PROCESSING"
  | "WAITING_FOR_INPUT"
  | "COMPLETED"
  | "FAILED"
  | "TIMED_OUT"
  | "GONE"
  | "UNREACHABLE";

interface SuggestionSession {
  session_id: string;
  status: SuggestionStatus;
  pending_question?: string | null;
  result?: string | null;
}

/** Picked option index per bullet, tied to the result it was picked from
 *  so a fresh set of options starts with nothing selected. */
interface Picks {
  result: string | null | undefined;
  byBullet: Record<number, number>;
}

const fieldClass =
  "border-zinc-700 bg-zinc-950/50 text-zinc-200 placeholder:text-zinc-600 focus-visible:border-brand-500 focus-visible:ring-brand-500/30";

export default function SuggestionDialog({
  accessToken,
  experienceId,
  bulletId,
  targetText,
  bullets,
  contextLabel,
  variant = "button",
}: {
  accessToken: string;
  experienceId: number;
  /** Set for a single-bullet suggestion; omit for the whole experience. */
  bulletId?: number;
  /** The current text the suggestion would replace — shown for comparison. */
  targetText?: string;
  /** The experience's current bullets, so each set of options can show the
   *  bullet it would replace. */
  bullets?: { id: number; bullet: string }[];
  /** Job label shown in the header, e.g. "Engineer · Acme". */
  contextLabel?: string;
  /** "icon" for per-bullet rows, "button" for the experience-level action. */
  variant?: "icon" | "button";
}) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [model, setModel] = useState("");
  const [session, setSession] = useState<SuggestionSession | null>(null);
  const [answer, setAnswer] = useState("");
  const [picks, setPicks] = useState<Picks>({ result: null, byBullet: {} });
  const [busy, setBusy] = useState(false);
  const finishedRef = useRef(false);
  const startedAtRef = useRef<number>(0);
  const consecutiveFailuresRef = useRef(0);

  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

  async function apiFetch(path: string, init?: RequestInit) {
    return apiRequest(accessToken, `/bullets${path}`, init);
  }

  function reportStartError(error: unknown) {
    if (isInsufficientBalance(error)) {
      toast.error("Insufficient balance", {
        description: "Top up to keep going.",
        action: {
          label: "Top Up",
          onClick: () => router.push("/billing"),
        },
      });
    } else {
      toast.error("Couldn't start suggestion", {
        description: describeApiError(error),
      });
    }
  }

  /** POST a fresh session and prime local state for polling. */
  async function launch() {
    if (!apiBaseUrl || busy) return;
    setBusy(true);
    finishedRef.current = false;
    consecutiveFailuresRef.current = 0;
    try {
      startedAtRef.current = Date.now();
      const { session_id } = (await apiFetch("/suggestions", {
        method: "POST",
        body: JSON.stringify({
          experience_id: experienceId,
          bullet_id: bulletId ?? null,
          model: model || null,
        }),
      })) as { session_id: string };
      try {
        const status = (await apiFetch(`/suggestions/${session_id}`)) as Omit<
          SuggestionSession,
          "session_id"
        >;
        setSession({ session_id, ...status });
      } catch {
        setSession({ session_id, status: "PROCESSING" });
      }
    } catch (error) {
      reportStartError(error);
      setOpen(false);
    } finally {
      setBusy(false);
    }
  }

  async function start() {
    if (session) return;
    await launch();
  }

  /** Requeue a FAILED session — the backend resumes the checkpointed agent
   *  instead of starting over. */
  async function retry() {
    if (!session || busy) return;
    setBusy(true);
    try {
      await apiFetch(`/suggestions/${session.session_id}/retry`, {
        method: "POST",
      });
      startedAtRef.current = Date.now();
      consecutiveFailuresRef.current = 0;
      finishedRef.current = false;
      setSession((s) => (s ? { ...s, status: "PROCESSING" } : s));
    } catch (error) {
      reportStartError(error);
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    if (!open || !session) return;
    if (session.status !== "PENDING" && session.status !== "PROCESSING") return;
    if (finishedRef.current) return;

    let cancelled = false;
    const interval = setInterval(async () => {
      if (Date.now() - startedAtRef.current > SESSION_TIMEOUT_MS) {
        clearInterval(interval);
        setSession((s) => (s ? { ...s, status: "TIMED_OUT" } : s));
        void apiFetch(`/suggestions/${session.session_id}/dismiss`, {
          method: "POST",
        }).catch(() => {});
        return;
      }
      try {
        const data = (await apiFetch(
          `/suggestions/${session.session_id}`,
        )) as Omit<SuggestionSession, "session_id">;
        if (cancelled) return;
        consecutiveFailuresRef.current = 0;
        setSession((s) => {
          if (!s) return s;
          if (data.status === "PROCESSING") startedAtRef.current = Date.now();
          return { ...s, ...data };
        });
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) {
          setSession((s) => (s ? { ...s, status: "GONE" } : s));
          clearInterval(interval);
          return;
        }
        consecutiveFailuresRef.current += 1;
        if (consecutiveFailuresRef.current >= 5) {
          setSession((s) => (s ? { ...s, status: "UNREACHABLE" } : s));
          clearInterval(interval);
        }
      }
    }, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, session?.session_id, session?.status]);

  /** Reply to the agent: an answer to its question, or — once options are
   *  showing — direction for a fresh set of three. */
  async function sendAnswer(text: string) {
    if (!text || !session || busy) return;
    setBusy(true);
    try {
      await apiFetch(`/suggestions/${session.session_id}/answer`, {
        method: "POST",
        body: JSON.stringify({ text }),
      });
      setAnswer("");
      startedAtRef.current = Date.now();
      consecutiveFailuresRef.current = 0;
      setSession((s) => (s ? { ...s, status: "PROCESSING" } : s));
    } catch (error) {
      toast.error("Couldn't send answer", {
        description: describeApiError(error),
      });
    } finally {
      setBusy(false);
    }
  }

  async function accept() {
    const choices = Object.entries(pickedByBullet).map(([id, option]) => ({
      bullet_id: Number(id),
      option,
    }));
    if (!session || choices.length === 0) return;
    setBusy(true);
    finishedRef.current = true;
    try {
      await apiFetch(`/suggestions/${session.session_id}/accept`, {
        method: "POST",
        body: JSON.stringify({ choices }),
      });
      toast.success(
        choices.length === 1
          ? "Suggestion applied"
          : `${choices.length} bullets updated`,
      );
      setOpen(false);
      router.refresh();
    } catch (error) {
      finishedRef.current = false;
      toast.error("Couldn't apply suggestion", {
        description: describeApiError(error),
      });
    } finally {
      setBusy(false);
    }
  }

  async function dismiss() {
    finishedRef.current = true;
    try {
      if (session) {
        await apiFetch(`/suggestions/${session.session_id}/dismiss`, {
          method: "POST",
        });
      }
    } catch {
      // Dismiss is best-effort — close regardless.
    }
    setOpen(false);
  }

  async function reset() {
    await dismiss();
    setSession(null);
    setAnswer("");
    finishedRef.current = false;
    consecutiveFailuresRef.current = 0;
  }

  const options = useMemo(
    () => parseSuggestionResult(session?.result),
    [session?.result],
  );
  const pickedByBullet =
    picks.result === session?.result ? picks.byBullet : {};
  const pickedCount = Object.keys(pickedByBullet).length;

  /** Select an option for its bullet; selecting it again deselects it. */
  function togglePick(bullet: number, option: number) {
    const byBullet = { ...pickedByBullet };
    if (byBullet[bullet] === option) delete byBullet[bullet];
    else byBullet[bullet] = option;
    setPicks({ result: session?.result, byBullet });
  }

  function currentText(id: number) {
    return (
      bullets?.find((b) => b.id === id)?.bullet ??
      (id === bulletId ? targetText : undefined)
    );
  }

  const processing =
    session?.status === "PENDING" || session?.status === "PROCESSING";
  const waiting = session?.status === "WAITING_FOR_INPUT";
  // Options stay pickable while the agent waits for a reply to them.
  const reviewing =
    options.length > 0 && (waiting || session?.status === "COMPLETED");
  const asking = waiting && !reviewing;
  const failed = session?.status === "FAILED";
  const timedOut = session?.status === "TIMED_OUT";
  const gone = session?.status === "GONE";
  const unreachable = session?.status === "UNREACHABLE";

  return (
    <Dialog
      open={open}
      onOpenChange={(v, details) => {
        // Keep open on backdrop clicks — the session is in-flight work;
        // Escape and the X button still close it.
        if (!v && details.reason === "outside-press") return;
        setOpen(v);
      }}
    >
      {variant === "icon" ? (
        <DialogTrigger
          title="Suggest Improvement"
          className="inline-flex shrink-0 align-middle text-zinc-500 hover:text-brand-300"
        >
          <Sparkles className="size-3.5" />
        </DialogTrigger>
      ) : (
        <DialogTrigger
          className={cn(
            "inline-flex items-center gap-1.5 rounded-md border border-zinc-700 px-2 py-1 text-xs text-zinc-300 hover:bg-zinc-800",
          )}
        >
          <Sparkles className="size-3.5 text-brand-400" /> Suggest Improvements
        </DialogTrigger>
      )}

      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-zinc-100">
            <Sparkles className="size-4 text-brand-400" />
            {bulletId ? "Improve This Bullet" : "Improve This Experience"}
          </DialogTitle>
          <DialogDescription className="text-zinc-400">
            {contextLabel ? `${contextLabel}. ` : ""}Resland asks about the
            work behind your bullets, then writes three options to pick from.
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-4">
          {!session && (
            <div className="flex items-center justify-between gap-2">
              <ModelSelect
                accessToken={accessToken}
                value={model}
                onChange={setModel}
                disabled={busy}
                jobKind="SUGGESTION"
              />
              <Button
                onClick={start}
                disabled={busy || !apiBaseUrl}
              >
                {busy ? <Loader2 className="animate-spin" /> : "Start"}
              </Button>
            </div>
          )}

          {/* Experience-wide options show each bullet's current text inline. */}
          {targetText && !(reviewing && !bulletId) && (
            <div className="rounded-lg border border-zinc-800 bg-zinc-950/50 p-3">
              <p className="text-xs font-medium tracking-wide text-zinc-500 uppercase">
                {bulletId ? "Your Bullet Point" : "Your Current Bullets"}
              </p>
              <p className="mt-1 text-sm whitespace-pre-wrap text-zinc-300">
                {targetText}
              </p>
            </div>
          )}

          {processing && (
            <div className="flex items-center gap-2 text-sm text-zinc-400">
              <Loader2 className="size-4 animate-spin text-brand-400" />
              {options.length > 0 ? "Writing new options…" : "Thinking…"}
            </div>
          )}

          {reviewing && (
            <div className="flex flex-col gap-4">
              {options.map((b) => {
                const current = bulletId ? undefined : currentText(b.bullet_id);
                return (
                  <div key={b.bullet_id} className="flex flex-col gap-2">
                    {current && (
                      <p className="text-xs text-zinc-500">
                        <span className="font-medium tracking-wide uppercase">
                          Current:
                        </span>{" "}
                        {current}
                      </p>
                    )}
                    <div role="radiogroup" className="flex flex-col gap-2">
                      {b.options.map((text, i) => {
                        const picked = pickedByBullet[b.bullet_id] === i;
                        return (
                          <button
                            key={i}
                            type="button"
                            role="radio"
                            aria-checked={picked}
                            onClick={() => togglePick(b.bullet_id, i)}
                            disabled={busy}
                            className={cn(
                              "flex flex-col gap-1 rounded-lg border p-3 text-left text-sm transition-colors",
                              picked
                                ? "border-emerald-500/50 bg-emerald-500/10 text-emerald-100"
                                : "border-zinc-800 bg-zinc-950/50 text-zinc-300 hover:border-zinc-600",
                            )}
                          >
                            <span
                              className={cn(
                                "text-xs font-medium tracking-wide uppercase",
                                picked ? "text-emerald-400" : "text-zinc-500",
                              )}
                            >
                              Option {i + 1}
                            </span>
                            <span className="whitespace-pre-wrap">{text}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {waiting && (
            <div className="flex flex-col gap-3">
              <div className="rounded-lg border border-brand-500/30 bg-brand-500/10 p-3 text-sm whitespace-pre-wrap text-brand-200">
                {session.pending_question}
              </div>
              <div className="flex items-end gap-2">
                <Textarea
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      void sendAnswer(
                        asking ? answer.trim() : moreOptionsMessage(answer),
                      );
                    }
                  }}
                  rows={asking ? 3 : 1}
                  placeholder={
                    asking
                      ? "Your answer… (Shift+Enter for a new line)"
                      : "What should change? (optional)"
                  }
                  className={cn(asking ? "min-h-20" : "min-h-9", fieldClass)}
                />
                {asking ? (
                  <Button
                    onClick={() => sendAnswer(answer.trim())}
                    disabled={busy || !answer.trim()}
                  >
                    <Send />
                  </Button>
                ) : (
                  <Button
                    variant="outline"
                    onClick={() => sendAnswer(moreOptionsMessage(answer))}
                    disabled={busy}
                    className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
                  >
                    {answer.trim() ? <Send /> : <Sparkles />} More Options
                  </Button>
                )}
              </div>
              {asking && <MemoryNote />}
            </div>
          )}

          {reviewing && (
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={dismiss}
                disabled={busy}
                className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
              >
                Cancel
              </Button>
              <Button
                onClick={accept}
                disabled={busy || pickedCount === 0}
              >
                {busy ? (
                  <Loader2 className="animate-spin" />
                ) : pickedCount > 1 ? (
                  `Accept ${pickedCount}`
                ) : (
                  "Accept"
                )}
              </Button>
            </div>
          )}

          {timedOut && (
            <div className="flex flex-col gap-3">
              <p className="text-sm text-amber-400">
                This took too long, so we stopped waiting. Start over to try again.
              </p>
              <Button
                variant="outline"
                onClick={reset}
                className="self-start border-zinc-700 text-zinc-300 hover:bg-zinc-800"
              >
                Start Over
              </Button>
            </div>
          )}
          {failed && (
            <div className="flex flex-col gap-3">
              <p className="text-sm text-red-400">
                Something went wrong on our end.
              </p>
              <div className="flex gap-2">
                <Button
                  onClick={retry}
                  disabled={busy}
                >
                  {busy ? <Loader2 className="animate-spin" /> : "Retry"}
                </Button>
                <Button
                  variant="outline"
                  onClick={reset}
                  disabled={busy}
                  className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
                >
                  Start Over
                </Button>
              </div>
            </div>
          )}
          {gone && (
            <div className="flex flex-col gap-3">
              <p className="text-sm text-amber-400">
                This session has expired. Start a new one.
              </p>
              <Button
                variant="outline"
                onClick={reset}
                className="self-start border-zinc-700 text-zinc-300 hover:bg-zinc-800"
              >
                Start Over
              </Button>
            </div>
          )}
          {unreachable && (
            <ApiUnavailable
              onRetry={() => {
                consecutiveFailuresRef.current = 0;
                startedAtRef.current = Date.now();
                setSession((s) => (s ? { ...s, status: "PROCESSING" } : s));
              }}
            />
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
