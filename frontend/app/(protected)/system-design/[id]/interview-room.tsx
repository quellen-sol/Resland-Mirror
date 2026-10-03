"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  ArrowRight,
  CircleAlert,
  Clock,
  Flag,
  Loader2,
  MonitorSmartphone,
  RotateCcw,
  Send,
} from "lucide-react";
import { toast } from "sonner";
import type { ExcalidrawElement } from "@excalidraw/excalidraw/element/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import HelpTip from "@/components/help-tip";
import {
  ApiError,
  apiFetch,
  describeApiError,
  isInsufficientBalance,
} from "@/lib/api";
import {
  COMPONENT_PALETTE,
  LEVEL_LABELS,
  PHASES,
  PHASE_LABELS,
  advanceLabel,
  fmtClock,
  phaseElapsedSeconds,
  type DiagramIssue,
  type Phase,
  type SessionStatus,
  type Workspace,
} from "@/lib/system-design";
import { cn } from "cn";
import type { DesignCanvasHandle } from "./design-canvas";
import InterviewReport from "./interview-report";

const DesignCanvas = dynamic(() => import("./design-canvas"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full items-center justify-center rounded-lg border border-zinc-800 text-sm text-zinc-500">
      <Loader2 className="mr-2 size-4 animate-spin" /> Loading whiteboard…
    </div>
  ),
});

const POLL_INTERVAL_MS = 2500;
const AUTOSAVE_DELAY_MS = 1200;

type WorkspaceField = "diagram" | "requirements" | "estimates";

function parseElements(raw: string): ExcalidrawElement[] {
  try {
    const data = JSON.parse(raw);
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

/** The structured detail of a 422 from the turn endpoint, if it has one. */
function turnRejection(
  error: unknown,
): { code: string; message: string; issues?: DiagramIssue[] } | null {
  if (!(error instanceof ApiError) || error.status !== 422) return null;
  try {
    const detail = JSON.parse(error.message)?.detail;
    return detail && typeof detail.code === "string" ? detail : null;
  } catch {
    return null;
  }
}

export default function InterviewRoom({
  accessToken,
  sessionId,
}: {
  accessToken: string;
  sessionId: string;
}) {
  const router = useRouter();
  const [status, setStatus] = useState<SessionStatus | null>(null);
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [requirements, setRequirements] = useState("");
  const [estimates, setEstimates] = useState("");
  const [issues, setIssues] = useState<DiagramIssue[]>([]);
  const [saveState, setSaveState] = useState<"saved" | "saving" | "error">(
    "saved",
  );
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [gone, setGone] = useState(false);
  const [offsetMs, setOffsetMs] = useState(0);
  const [now, setNow] = useState(() => Date.now());
  const [issueDialog, setIssueDialog] = useState<DiagramIssue[] | null>(null);
  const [confirmFinish, setConfirmFinish] = useState(false);
  const [finalDiagram, setFinalDiagram] = useState<ExcalidrawElement[] | null>(
    null,
  );

  const canvasRef = useRef<DesignCanvasHandle | null>(null);
  const diagramRef = useRef<string>("[]");
  const pendingRef = useRef<Partial<Record<WorkspaceField, string>>>({});
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  const api = useCallback(
    (path: string, init?: RequestInit) =>
      apiFetch(accessToken, `/system-design/${sessionId}${path}`, init),
    [accessToken, sessionId],
  );

  const refresh = useCallback(async () => {
    try {
      const data = (await api("")) as SessionStatus;
      setOffsetMs(Date.parse(data.server_time) - Date.now());
      setStatus(data);
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) setGone(true);
    }
  }, [api]);

  // Initial load: status plus the saved workspace.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      await refresh();
      try {
        const ws = (await api("/workspace")) as Workspace;
        if (cancelled) return;
        diagramRef.current = ws.diagram;
        setRequirements(ws.requirements);
        setEstimates(ws.estimates);
        setIssues(ws.issues);
        setWorkspace(ws);
      } catch {
        // refresh() already flagged a missing session.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [api, refresh]);

  // The report shows the final diagram. Fetch it once grading lands — the
  // copy loaded with the page can predate this session's edits, and the
  // report's canvas only reads its elements on mount.
  const completed = status?.status === "COMPLETED";
  useEffect(() => {
    if (!completed) return;
    let cancelled = false;
    api("/workspace")
      .then((ws: Workspace) => {
        if (!cancelled) setFinalDiagram(parseElements(ws.diagram));
      })
      .catch(() => {
        if (!cancelled) setFinalDiagram(parseElements(diagramRef.current));
      });
    return () => {
      cancelled = true;
    };
  }, [completed, api]);

  // Poll while the interviewer is working.
  useEffect(() => {
    if (status?.status !== "PROCESSING") return;
    const interval = setInterval(refresh, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [status?.status, refresh]);

  // Tick the phase clock.
  useEffect(() => {
    const interval = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(interval);
  }, []);

  const messageCount = status?.messages.length ?? 0;
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messageCount, status?.status]);

  const open =
    status?.status === "PROCESSING" || status?.status === "WAITING_FOR_INPUT";

  const flushSave = useCallback(async () => {
    if (saveTimerRef.current) {
      clearTimeout(saveTimerRef.current);
      saveTimerRef.current = null;
    }
    const pending = pendingRef.current;
    if (!Object.keys(pending).length) return;
    pendingRef.current = {};
    setSaveState("saving");
    try {
      const ws = (await api("/workspace", {
        method: "PUT",
        body: JSON.stringify(pending),
      })) as Workspace;
      setIssues(ws.issues);
      setSaveState("saved");
    } catch {
      // Put the edits back so the next save retries them.
      pendingRef.current = { ...pending, ...pendingRef.current };
      setSaveState("error");
    }
  }, [api]);

  const queueSave = useCallback(
    (field: WorkspaceField, value: string) => {
      pendingRef.current[field] = value;
      setSaveState("saving");
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
      saveTimerRef.current = setTimeout(() => void flushSave(), AUTOSAVE_DELAY_MS);
    },
    [flushSave],
  );

  // Don't lose the last edits when leaving the page.
  useEffect(() => {
    return () => {
      void flushSave();
    };
  }, [flushSave]);

  const onDiagramChange = useCallback(
    (json: string) => {
      diagramRef.current = json;
      queueSave("diagram", json);
    },
    [queueSave],
  );

  async function takeTurn(
    action: "message" | "advance" | "finish" | "retry",
    opts: { text?: string; acknowledge?: boolean } = {},
  ) {
    if (busy) return;
    setBusy(true);
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    const pending = pendingRef.current;
    pendingRef.current = {};
    try {
      await api("/turn", {
        method: "POST",
        body: JSON.stringify({
          action,
          text: opts.text ?? null,
          workspace: Object.keys(pending).length ? pending : null,
          acknowledge_issues: opts.acknowledge ?? false,
        }),
      });
      setSaveState("saved");
      if (action === "message") setMessage("");
      setIssueDialog(null);
      setConfirmFinish(false);
      await refresh();
    } catch (error) {
      // The turn didn't happen, but the server may already hold the
      // workspace (it saves before validating) — re-sending is harmless.
      pendingRef.current = { ...pending, ...pendingRef.current };
      const rejection = turnRejection(error);
      if (rejection?.code === "diagram_issues" && rejection.issues) {
        setIssues(rejection.issues);
        setIssueDialog(rejection.issues);
      } else if (rejection) {
        toast.error(rejection.message);
      } else if (isInsufficientBalance(error)) {
        toast.error("Insufficient balance", {
          description: "Top up to keep going. Your work is saved.",
          action: { label: "Top Up", onClick: () => router.push("/billing") },
        });
      } else {
        toast.error("Couldn't send that", { description: describeApiError(error) });
        await refresh();
      }
    } finally {
      setBusy(false);
    }
  }

  async function discard() {
    try {
      await api("/dismiss", { method: "POST" });
    } catch {
      // Best-effort.
    }
    router.push("/system-design");
  }

  const initialElements = useMemo(
    () => (workspace ? parseElements(workspace.diagram) : []),
    [workspace],
  );

  if (gone) {
    return (
      <Card className="ring-amber-500/30">
        <CardContent className="flex flex-col gap-3 pt-6">
          <p className="text-sm text-amber-400">This interview no longer exists.</p>
          <Link
            href="/system-design"
            className="text-sm text-brand-300 underline underline-offset-4"
          >
            Start a new one
          </Link>
        </CardContent>
      </Card>
    );
  }

  if (!status || !workspace) {
    return (
      <div className="flex items-center gap-2 text-sm text-zinc-400">
        <Loader2 className="size-4 animate-spin text-brand-400" /> Loading
        interview…
      </div>
    );
  }

  if (status.status === "COMPLETED") {
    return finalDiagram ? (
      <InterviewReport status={status} diagramElements={finalDiagram} />
    ) : (
      <div className="flex items-center gap-2 text-sm text-zinc-400">
        <Loader2 className="size-4 animate-spin text-brand-400" /> Loading
        your report…
      </div>
    );
  }

  const phase = status.phase;
  const waiting = status.status === "WAITING_FOR_INPUT";
  const processing = status.status === "PROCESSING";
  const failed = status.status === "FAILED";
  const notStarted = !status.title;
  const elapsed = phaseElapsedSeconds(status.phase_started_at, offsetMs, now);
  const total = phaseElapsedSeconds(status.created_at, offsetMs, now);
  const target = status.phase_targets[phase];
  const advance = advanceLabel(phase);
  const canAct = waiting && !status.notice && !busy && phase !== "FEEDBACK";

  return (
    <div className="flex flex-col gap-4">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h1 className="truncate text-2xl font-semibold tracking-[-0.03em]">
              {status.title ?? "Setting up your interview…"}
            </h1>
            <HelpTip title="How This Works">
              <p>
                Move through the phases like a real interview: clarify
                requirements with the interviewer, estimate the scale, draw
                your design, then answer deep-dive questions.
              </p>
              <p>
                Add components from the palette and connect them with the
                arrow tool. Drag each arrow end onto a box until it snaps, so
                the interviewer knows what connects to what.
              </p>
              <p>
                Your notes and diagram save automatically. Each interviewer
                reply draws from your balance.
              </p>
            </HelpTip>
          </div>
          <p className="mt-1 text-sm text-zinc-400">
            {LEVEL_LABELS[status.level]} level
            {status.company_name && ` · ${status.role ?? "Role"} at ${status.company_name}`}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-3">
          <span className="inline-flex items-center gap-1.5 text-sm text-zinc-400 tabular-nums">
            <Clock className="size-3.5" /> {fmtClock(total)}
          </span>
          <Link
            href="/system-design"
            className="inline-flex items-center gap-1.5 text-sm text-zinc-500 underline-offset-4 hover:text-zinc-300 hover:underline"
          >
            <ArrowLeft className="size-3.5" /> All Interviews
          </Link>
        </div>
      </header>

      {/* Phase stepper */}
      <ol className="grid grid-cols-5 gap-1 text-xs">
        {PHASES.map((p: Phase, i) => {
          const current = p === phase;
          const done = PHASES.indexOf(phase) > i;
          const spent = status.phase_durations[p];
          const over = current && target !== undefined && elapsed > target;
          return (
            <li
              key={p}
              className={cn(
                "flex flex-col gap-0.5 rounded-md border px-2 py-1.5",
                current
                  ? "border-brand-500/50 bg-brand-500/10 text-brand-100"
                  : done
                    ? "border-zinc-800 bg-zinc-900/60 text-zinc-300"
                    : "border-zinc-800/60 text-zinc-600",
              )}
            >
              <span className="font-medium">{PHASE_LABELS[p]}</span>
              <span className={cn("tabular-nums", over && "text-amber-400")}>
                {current && p !== "FEEDBACK"
                  ? `${fmtClock(elapsed)}${target ? ` / ${fmtClock(target)}` : ""}`
                  : spent !== undefined
                    ? fmtClock(spent)
                    : status.phase_targets[p]
                      ? `${Math.round(status.phase_targets[p]! / 60)} min`
                      : ""}
              </span>
            </li>
          );
        })}
      </ol>

      <Card className="lg:hidden">
        <CardContent className="flex items-center gap-3 pt-6 text-sm text-zinc-300">
          <MonitorSmartphone className="size-5 shrink-0 text-brand-400" />
          The whiteboard needs a bigger screen. Open this interview on a laptop or desktop to keep going.
        </CardContent>
      </Card>

      {failed && (
        <Card className="ring-red-500/30">
          <CardContent className="flex flex-wrap items-center justify-between gap-3 pt-6">
            <p className="text-sm text-red-400">
              This interview couldn&apos;t be set up. Discard it and start
              another.
            </p>
            <Button
              variant="outline"
              onClick={discard}
              className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
            >
              Discard
            </Button>
          </CardContent>
        </Card>
      )}

      <div className="hidden gap-4 lg:grid lg:grid-cols-[minmax(0,1fr)_380px]">
        {/* Whiteboard + notes */}
        <div className="flex min-w-0 flex-col gap-3">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="mr-1 text-xs font-medium tracking-wide text-zinc-500 uppercase">
              Add
            </span>
            {COMPONENT_PALETTE.map((item) => (
              <button
                key={item.kind}
                type="button"
                onClick={() => canvasRef.current?.addComponent(item)}
                className="inline-flex items-center gap-1.5 rounded-md border border-zinc-800 bg-zinc-900 px-2 py-1 text-xs text-zinc-300 hover:border-zinc-700 hover:text-zinc-100"
              >
                <span
                  className="size-2.5 rounded-sm"
                  style={{ backgroundColor: item.color }}
                />
                {item.label}
              </button>
            ))}
          </div>
          <div className="h-[62vh] min-h-[460px]">
            <DesignCanvas
              initialElements={initialElements}
              onChange={onDiagramChange}
              onReady={(handle) => {
                canvasRef.current = handle;
              }}
            />
          </div>
          <div className="flex items-center justify-between text-xs text-zinc-500">
            <span>
              {saveState === "saving"
                ? "Saving…"
                : saveState === "error"
                  ? "Couldn't save. We'll retry on your next change."
                  : "All changes saved"}
            </span>
            {issues.length > 0 && (
              <button
                type="button"
                onClick={() => setIssueDialog(issues)}
                className="inline-flex items-center gap-1 text-amber-400 hover:text-amber-300"
              >
                <CircleAlert className="size-3.5" />
                {issues.length} diagram {issues.length === 1 ? "issue" : "issues"}
              </button>
            )}
          </div>
          <div className="grid gap-3 xl:grid-cols-2">
            <label className="flex flex-col gap-1.5">
              <span className="text-xs font-medium tracking-wide text-zinc-500 uppercase">
                Requirements
              </span>
              <Textarea
                value={requirements}
                onChange={(e) => {
                  setRequirements(e.target.value);
                  queueSave("requirements", e.target.value);
                }}
                disabled={!open}
                placeholder={"Functional:\n- …\n\nNon-functional:\n- …"}
                className="min-h-40 border-zinc-700 bg-zinc-950/50 font-mono text-xs text-zinc-200 placeholder:text-zinc-600 focus-visible:border-brand-500 focus-visible:ring-brand-500/30"
              />
            </label>
            <label className="flex flex-col gap-1.5">
              <span className="text-xs font-medium tracking-wide text-zinc-500 uppercase">
                Estimates
              </span>
              <Textarea
                value={estimates}
                onChange={(e) => {
                  setEstimates(e.target.value);
                  queueSave("estimates", e.target.value);
                }}
                disabled={!open}
                placeholder={"DAU, reads/writes per second, storage, bandwidth…"}
                className="min-h-40 border-zinc-700 bg-zinc-950/50 font-mono text-xs text-zinc-200 placeholder:text-zinc-600 focus-visible:border-brand-500 focus-visible:ring-brand-500/30"
              />
            </label>
          </div>
        </div>

        {/* Problem + interviewer */}
        <div className="flex min-h-0 flex-col gap-3 lg:sticky lg:top-4 lg:h-[calc(100vh-2rem)]">
          {status.prompt && (
            <Card>
              <CardContent className="pt-4 text-sm">
                <p className="mb-1 text-xs font-medium tracking-wide text-zinc-500 uppercase">
                  Problem
                </p>
                <p className="text-zinc-300">{status.prompt}</p>
              </CardContent>
            </Card>
          )}

          <Card className="flex min-h-0 flex-1 flex-col py-0">
            <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto p-4 text-sm">
              {status.messages.map((m) => (
                <div
                  key={m.id}
                  className={cn(
                    "max-w-[90%] rounded-lg px-3 py-2 whitespace-pre-wrap",
                    m.role === "INTERVIEWER"
                      ? "self-start border border-brand-500/30 bg-brand-500/10 text-brand-100"
                      : "self-end bg-zinc-800 text-zinc-100",
                  )}
                >
                  {m.content}
                </div>
              ))}
              {processing && (
                <div className="flex items-center gap-2 self-start text-xs text-zinc-400">
                  <Loader2 className="size-3.5 animate-spin text-brand-400" />
                  {phase === "FEEDBACK"
                    ? "Grading your interview…"
                    : notStarted
                      ? "Preparing your problem…"
                      : "Interviewer is thinking…"}
                </div>
              )}
              {status.notice && (
                <div className="flex flex-col gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-amber-200">
                  <span>{status.notice}</span>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={busy}
                    onClick={() => takeTurn("retry")}
                    className="self-start border-amber-500/40 text-amber-200 hover:bg-amber-500/10"
                  >
                    <RotateCcw /> Retry
                  </Button>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
            <div className="flex flex-col gap-2 border-t border-zinc-800 p-3">
              <div className="flex gap-2">
                <Textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      if (canAct && message.trim()) {
                        void takeTurn("message", { text: message.trim() });
                      }
                    }
                  }}
                  disabled={!canAct}
                  rows={2}
                  placeholder={
                    phase === "DEEP_DIVE"
                      ? "Answer the interviewer…"
                      : "Ask a question or think out loud…"
                  }
                  className="min-h-0 resize-none border-zinc-700 bg-zinc-950/50 text-sm text-zinc-200 placeholder:text-zinc-600 focus-visible:border-brand-500 focus-visible:ring-brand-500/30"
                />
                <Button
                  onClick={() => takeTurn("message", { text: message.trim() })}
                  disabled={!canAct || !message.trim()}
                  aria-label="Send"
                  className="h-auto"
                >
                  {busy ? <Loader2 className="animate-spin" /> : <Send />}
                </Button>
              </div>
              <div className="flex items-center justify-between gap-2">
                <button
                  type="button"
                  disabled={!waiting || busy || notStarted || phase === "FEEDBACK"}
                  onClick={() => setConfirmFinish(true)}
                  className="inline-flex items-center gap-1 text-xs text-zinc-500 hover:text-zinc-300 disabled:opacity-40"
                >
                  <Flag className="size-3.5" /> End &amp; Grade
                </button>
                {advance && (
                  <Button
                    size="sm"
                    disabled={!canAct}
                    onClick={() =>
                      takeTurn("advance", { text: message.trim() || undefined })
                    }
                  >
                    {advance} <ArrowRight />
                  </Button>
                )}
              </div>
            </div>
          </Card>
        </div>
      </div>

      <Dialog
        open={issueDialog !== null}
        onOpenChange={(o) => {
          if (!o) setIssueDialog(null);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-zinc-100">
              Some of Your Diagram Isn&apos;t Connected
            </DialogTitle>
            <DialogDescription className="text-zinc-400">
              The interviewer reads your design from which boxes your arrows
              connect. These pieces won&apos;t count until they&apos;re attached.
            </DialogDescription>
          </DialogHeader>
          <ul className="flex max-h-64 flex-col gap-1.5 overflow-y-auto text-sm">
            {issueDialog?.map((issue) => (
              <li key={issue.element_id + issue.kind}>
                <button
                  type="button"
                  onClick={() => {
                    canvasRef.current?.focusElements([issue.element_id]);
                    setIssueDialog(null);
                  }}
                  className="w-full rounded-md border border-zinc-800 px-3 py-2 text-left text-zinc-300 hover:border-zinc-700 hover:text-zinc-100"
                >
                  {issue.message}
                </button>
              </li>
            ))}
          </ul>
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={() => {
                if (issueDialog?.length) {
                  canvasRef.current?.focusElements(
                    issueDialog.map((i) => i.element_id),
                  );
                }
                setIssueDialog(null);
              }}
              className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
            >
              Fix Them
            </Button>
            {phase === "HIGH_LEVEL_DESIGN" && canAct && (
              <Button
                onClick={() =>
                  takeTurn("advance", {
                    text: message.trim() || undefined,
                    acknowledge: true,
                  })
                }
              >
                Submit Anyway
              </Button>
            )}
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={confirmFinish} onOpenChange={setConfirmFinish}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-zinc-100">End the Interview?</DialogTitle>
            <DialogDescription className="text-zinc-400">
              You&apos;ll be graded on what you&apos;ve done so far. Phases you
              haven&apos;t reached score low.
            </DialogDescription>
          </DialogHeader>
          <div className="flex justify-between gap-2">
            <Button
              variant="ghost"
              onClick={discard}
              className="text-zinc-500 hover:text-red-300"
            >
              Discard Instead
            </Button>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => setConfirmFinish(false)}
                className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
              >
                Keep Going
              </Button>
              <Button
                disabled={busy}
                onClick={() => takeTurn("finish")}
              >
                {busy ? <Loader2 className="animate-spin" /> : <Flag />} End &amp;
                Grade
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
