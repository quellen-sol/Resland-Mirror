"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Send, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { cn } from "cn";
import ModelSelect from "@/components/model-select";
import {
  ApiError,
  apiFetch as apiRequest,
  describeApiError,
  isInsufficientBalance,
} from "@/lib/api";
import ApiUnavailable from "@/components/api-unavailable";

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

export default function SuggestionDialog({
  accessToken,
  experienceId,
  bulletId,
  targetText,
  contextLabel,
  variant = "button",
}: {
  accessToken: string;
  experienceId: number;
  /** Set for a single-bullet suggestion; omit for the whole experience. */
  bulletId?: number;
  /** The current text the suggestion would replace — shown for comparison. */
  targetText?: string;
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
  const [ownPrompt, setOwnPrompt] = useState("");
  const [promptMode, setPromptMode] = useState(false);
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

  /** POST a fresh session (optionally seeded with the user's own prompt)
   *  and prime local state for polling. */
  async function launch(prompt?: string, closeOnError = true) {
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
          prompt: prompt || null,
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
      if (closeOnError) setOpen(false);
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

  /** Discard the current suggestion and relaunch with the user's own prompt. */
  async function submitOwnPrompt() {
    const text = ownPrompt.trim();
    if (!text || busy) return;
    finishedRef.current = true;
    if (session) {
      await apiFetch(`/suggestions/${session.session_id}/dismiss`, {
        method: "POST",
      }).catch(() => {});
    }
    setSession(null);
    setAnswer("");
    setOwnPrompt("");
    setPromptMode(false);
    await launch(text, false);
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

  async function sendAnswer() {
    const text = answer.trim();
    if (!text || !session) return;
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
    if (!session) return;
    setBusy(true);
    finishedRef.current = true;
    try {
      await apiFetch(`/suggestions/${session.session_id}/accept`, {
        method: "POST",
      });
      toast.success("Suggestion applied");
      setOpen(false);
      router.refresh();
    } catch (error) {
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

  // Result is a JSON array of {bullet_id, suggestion} produced by the agent.
  const suggestions = useMemo(() => {
    if (!session?.result) return [];
    try {
      const parsed = JSON.parse(session.result);
      return Array.isArray(parsed)
        ? (parsed as { bullet_id: number; suggestion: string }[])
        : [];
    } catch {
      return [];
    }
  }, [session]);

  const waiting = session?.status === "WAITING_FOR_INPUT";
  const done = session?.status === "COMPLETED";
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
          className="inline-flex shrink-0 align-middle text-zinc-500 hover:text-purple-300"
        >
          <Sparkles className="size-3.5" />
        </DialogTrigger>
      ) : (
        <DialogTrigger
          className={cn(
            "inline-flex items-center gap-1.5 rounded-md border border-zinc-700 px-2 py-1 text-xs text-zinc-300 hover:bg-zinc-800",
          )}
        >
          <Sparkles className="size-3.5 text-purple-400" /> Suggest Improvements
        </DialogTrigger>
      )}

      <DialogContent className="max-h-[85vh] overflow-y-auto border-zinc-800 bg-zinc-900 text-zinc-100 sm:max-w-xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-zinc-100">
            <Sparkles className="size-4 text-purple-400" />
            {bulletId ? "Improve This Bullet" : "Improve This Experience"}
          </DialogTitle>
          <DialogDescription className="text-zinc-400">
            {contextLabel ? `${contextLabel} — ` : ""}
            The agent may ask a question or two before suggesting a rewrite.
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
              />
              <Button
                onClick={start}
                disabled={busy || !apiBaseUrl}
                className="border-0 bg-gradient-to-r from-violet-600 to-purple-600 text-white hover:from-violet-500 hover:to-purple-500"
              >
                {busy ? <Loader2 className="animate-spin" /> : "Start"}
              </Button>
            </div>
          )}

          {targetText && (
            <div className="rounded-lg border border-zinc-800 bg-zinc-950/50 p-3">
              <p className="text-xs font-medium tracking-wide text-zinc-500 uppercase">
                {bulletId ? "Your Bullet Point" : "Your Current Bullets"}
              </p>
              <p className="mt-1 text-sm whitespace-pre-wrap text-zinc-300">
                {targetText}
              </p>
            </div>
          )}

          {(session?.status === "PENDING" ||
            session?.status === "PROCESSING") && (
            <div className="flex items-center gap-2 text-sm text-zinc-400">
              <Loader2 className="size-4 animate-spin text-purple-400" />
              Thinking…
            </div>
          )}

          {waiting && (
            <div className="flex flex-col gap-3">
              <div className="rounded-lg border border-purple-500/30 bg-purple-500/10 p-3 text-sm text-purple-200">
                {session.pending_question}
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
            </div>
          )}

          {done && (
            <div className="flex flex-col gap-3">
              <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3">
                <p className="text-xs font-medium tracking-wide text-emerald-400 uppercase">
                  Suggested
                </p>
                <ul className="mt-1 list-disc space-y-1 pl-4 text-sm whitespace-pre-wrap text-emerald-100">
                  {suggestions.map((s) => (
                    <li key={s.bullet_id}>{s.suggestion}</li>
                  ))}
                </ul>
              </div>
              {promptMode && (
                <div className="flex gap-2">
                  <Input
                    value={ownPrompt}
                    onChange={(e) => setOwnPrompt(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        void submitOwnPrompt();
                      }
                    }}
                    placeholder="Tell the agent what to change…"
                    className="border-zinc-700 bg-zinc-950/50 text-zinc-200 placeholder:text-zinc-600 focus-visible:border-purple-500 focus-visible:ring-purple-500/30"
                  />
                  <Button
                    onClick={submitOwnPrompt}
                    disabled={busy || !ownPrompt.trim()}
                    className="border-0 bg-gradient-to-r from-violet-600 to-purple-600 text-white hover:from-violet-500 hover:to-purple-500"
                  >
                    <Send />
                  </Button>
                </div>
              )}
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
                  variant="outline"
                  onClick={() => setPromptMode((v) => !v)}
                  disabled={busy}
                  className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
                >
                  Enter Own Prompt
                </Button>
                <Button
                  onClick={accept}
                  disabled={busy}
                  className="border-0 bg-gradient-to-r from-violet-600 to-purple-600 text-white hover:from-violet-500 hover:to-purple-500"
                >
                  {busy ? <Loader2 className="animate-spin" /> : "Accept"}
                </Button>
              </div>
            </div>
          )}

          {timedOut && (
            <div className="flex flex-col gap-3">
              <p className="text-sm text-amber-400">
                This is taking too long — we couldn&apos;t finish the request.
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
                  className="border-0 bg-gradient-to-r from-violet-600 to-purple-600 text-white hover:from-violet-500 hover:to-purple-500"
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
                This session no longer exists — start a new one.
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
