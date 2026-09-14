"use client";

import { useEffect, useRef, useState } from "react";
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

const POLL_INTERVAL_MS = 3000;
const SESSION_TIMEOUT_MS = 5 * 60 * 1000;

type SuggestionStatus =
  | "PENDING"
  | "PROCESSING"
  | "WAITING_FOR_INPUT"
  | "COMPLETED"
  | "FAILED"
  | "TIMED_OUT";

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
  variant = "button",
}: {
  accessToken: string;
  experienceId: number;
  /** Set for a single-bullet suggestion; omit for the whole experience. */
  bulletId?: number;
  /** The current text the suggestion would replace — shown for comparison. */
  targetText?: string;
  /** "icon" for per-bullet rows, "button" for the experience-level action. */
  variant?: "icon" | "button";
}) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [session, setSession] = useState<SuggestionSession | null>(null);
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const finishedRef = useRef(false);
  const startedAtRef = useRef<number>(0);

  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

  async function apiFetch(path: string, init?: RequestInit) {
    const res = await fetch(`${apiBaseUrl}/bullets${path}`, {
      ...init,
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
    return res.json();
  }

  async function start() {
    if (session || !apiBaseUrl) return;
    try {
      startedAtRef.current = Date.now();
      const { session_id } = await apiFetch("/suggestions", {
        method: "POST",
        body: JSON.stringify({
          experience_id: experienceId,
          bullet_id: bulletId ?? null,
        }),
      });
      setSession({ session_id, status: "PROCESSING" });
    } catch (error) {
      toast.error("Couldn't start suggestion", {
        description: error instanceof Error ? error.message : String(error),
      });
      setOpen(false);
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
        const data = (await apiFetch(`/suggestions/${session.session_id}`)) as Omit<
          SuggestionSession,
          "session_id"
        >;
        if (cancelled) return;
        setSession((s) => (s ? { ...s, ...data } : s));
      } catch {
        // Transient network error — retry on next tick.
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
      setSession((s) => (s ? { ...s, status: "PROCESSING" } : s));
    } catch (error) {
      toast.error("Couldn't send answer", {
        description: error instanceof Error ? error.message : String(error),
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
      await apiFetch(`/suggestions/${session.session_id}/accept`, { method: "POST" });
      toast.success("Suggestion applied");
      setOpen(false);
      router.refresh();
    } catch (error) {
      toast.error("Couldn't apply suggestion", {
        description: error instanceof Error ? error.message : String(error),
      });
    } finally {
      setBusy(false);
    }
  }

  async function dismiss() {
    finishedRef.current = true;
    try {
      if (session) {
        await apiFetch(`/suggestions/${session.session_id}/dismiss`, { method: "POST" });
      }
    } catch {
      // Dismiss is best-effort — close regardless.
    }
    setOpen(false);
  }

  const waiting = session?.status === "WAITING_FOR_INPUT";
  const done = session?.status === "COMPLETED";
  const failed = session?.status === "FAILED";
  const timedOut = session?.status === "TIMED_OUT";

  return (
    <Dialog
      open={open}
      onOpenChange={(v, details) => {
        // Keep open on backdrop clicks — the session is in-flight work;
        // Escape and the X button still close it.
        if (!v && details.reason === "outside-press") return;
        setOpen(v);
        if (v) void start();
      }}
    >
      {variant === "icon" ? (
        <DialogTrigger
          title="Suggest improvement"
          className="ml-1 inline-flex shrink-0 align-middle text-zinc-500 hover:text-purple-300"
        >
          <Sparkles className="size-3.5" />
        </DialogTrigger>
      ) : (
        <DialogTrigger
          className={cn(
            "inline-flex items-center gap-1.5 rounded-md border border-zinc-700 px-2 py-1 text-xs text-zinc-300 hover:bg-zinc-800",
          )}
        >
          <Sparkles className="size-3.5 text-purple-400" /> Suggest improvements
        </DialogTrigger>
      )}

      <DialogContent className="border-zinc-800 bg-zinc-900 text-zinc-100">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-zinc-100">
            <Sparkles className="size-4 text-purple-400" />
            {bulletId ? "Improve this bullet" : "Improve this experience"}
          </DialogTitle>
          <DialogDescription className="text-zinc-400">
            The agent may ask a question or two before suggesting a rewrite.
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-4">
          {targetText && (
            <div className="rounded-lg border border-zinc-800 bg-zinc-950/50 p-3">
              <p className="text-xs font-medium tracking-wide text-zinc-500 uppercase">
                Current
              </p>
              <p className="mt-1 text-sm text-zinc-300">{targetText}</p>
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
                <p className="mt-1 text-sm whitespace-pre-wrap text-emerald-100">
                  {session.result}
                </p>
              </div>
              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  onClick={dismiss}
                  disabled={busy}
                  className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
                >
                  Dismiss
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

          {failed && (
            <p className="text-sm text-red-400">
              Something went wrong — close this and try again.
            </p>
          )}

          {timedOut && (
            <p className="text-sm text-amber-400">
              This is taking too long — we couldn&apos;t finish the request.
              Close this and try again.
            </p>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
