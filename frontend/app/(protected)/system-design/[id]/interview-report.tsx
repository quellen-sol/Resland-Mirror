"use client";

import { useRef, useState } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import {
  ArrowLeft,
  BookOpen,
  ChevronDown,
  Loader2,
  MessageSquareText,
  Play,
  ThumbsUp,
  TrendingUp,
} from "lucide-react";
import type { ExcalidrawElement } from "@excalidraw/excalidraw/element/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  GRADE_TONE_CLASSES,
  HIRE_SIGNAL_LABELS,
  LEVEL_LABELS,
  PHASES,
  PHASE_LABELS,
  fmtClock,
  gradeTone,
  type SessionStatus,
} from "@/lib/system-design";
import { cn } from "cn";
import type { DesignCanvasHandle } from "./design-canvas";

const DesignCanvas = dynamic(() => import("./design-canvas"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full items-center justify-center rounded-lg border border-zinc-800 text-sm text-zinc-500">
      <Loader2 className="mr-2 size-4 animate-spin" /> Loading diagram…
    </div>
  ),
});

const SIGNAL_STYLES = {
  STRONG_HIRE: "border-emerald-500/40 bg-emerald-500/10 text-emerald-200",
  HIRE: "border-sky-500/40 bg-sky-500/10 text-sky-200",
  LEAN_NO_HIRE: "border-amber-500/40 bg-amber-500/10 text-amber-200",
  NO_HIRE: "border-red-500/40 bg-red-500/10 text-red-200",
} as const;

function List({ items }: { items: string[] }) {
  if (!items.length) return <p className="text-zinc-500">—</p>;
  return (
    <ul className="list-disc space-y-1 pl-5 text-zinc-300">
      {items.map((item, i) => (
        <li key={i}>{item}</li>
      ))}
    </ul>
  );
}

function Collapsible({
  title,
  children,
  defaultOpen = false,
}: {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="rounded-lg border border-zinc-800">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between px-3 py-2 text-left text-sm font-medium text-zinc-200 hover:bg-zinc-800/40"
      >
        {title}
        <ChevronDown
          className={cn("size-4 text-zinc-500 transition-transform", open && "rotate-180")}
        />
      </button>
      {open && <div className="border-t border-zinc-800 p-3 text-sm">{children}</div>}
    </div>
  );
}

export default function InterviewReport({
  status,
  diagramElements,
}: {
  status: SessionStatus;
  diagramElements: readonly ExcalidrawElement[];
}) {
  const yourCanvas = useRef<DesignCanvasHandle | null>(null);
  const report = status.result;
  const reference = status.reference;

  if (!report) {
    return (
      <Card className="ring-red-500/30">
        <CardContent className="pt-6 text-sm text-red-400">
          We couldn&apos;t read this interview&apos;s report.
        </CardContent>
      </Card>
    );
  }

  const tone = gradeTone(report.letter_grade);

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-[-0.03em]">
            {status.title}
          </h1>
          <p className="mt-1 text-sm text-zinc-400">
            {LEVEL_LABELS[report.level] ?? report.level} level
            {status.company_name && ` · ${status.role ?? "Role"} at ${status.company_name}`}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/system-design"
            className="inline-flex items-center gap-1.5 text-sm text-zinc-500 underline-offset-4 hover:text-zinc-300 hover:underline"
          >
            <ArrowLeft className="size-3.5" /> All Interviews
          </Link>
          <Link
            href="/system-design"
            className="inline-flex items-center gap-1.5 rounded-lg bg-white px-2.5 py-1.5 text-sm font-medium text-zinc-950 hover:bg-zinc-200 [&_svg]:size-4"
          >
            <Play /> Practice Another
          </Link>
        </div>
      </header>

      <Card>
        <CardContent className="flex flex-wrap items-center gap-6 pt-6">
          <div className="flex flex-col items-center">
            <span className={cn("text-6xl font-bold", GRADE_TONE_CLASSES[tone])}>
              {report.letter_grade}
            </span>
            <span className="text-xs text-zinc-500">
              {report.weighted_score.toFixed(2)} / 5
            </span>
          </div>
          <div className="flex min-w-0 flex-1 flex-col gap-2">
            <span
              className={cn(
                "self-start rounded-md border px-2 py-0.5 text-sm font-medium",
                SIGNAL_STYLES[report.hire_signal],
              )}
            >
              {HIRE_SIGNAL_LABELS[report.hire_signal]}
            </span>
            <p className="text-sm text-zinc-300">{report.summary}</p>
            <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-zinc-500">
              {PHASES.filter((p) => p !== "FEEDBACK").map((p) => (
                <span key={p}>
                  {PHASE_LABELS[p]}:{" "}
                  {report.phase_durations[p] !== undefined
                    ? fmtClock(report.phase_durations[p]!)
                    : "not reached"}
                </span>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle className="text-lg">Rubric</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4 text-sm">
            {report.dimensions.map((d) => (
              <div key={d.key} className="flex flex-col gap-1.5">
                <div className="flex items-baseline justify-between gap-2">
                  <span className="font-medium text-zinc-100">
                    {d.label}{" "}
                    <span className="text-xs font-normal text-zinc-500">
                      {Math.round(d.weight * 100)}%
                    </span>
                  </span>
                  <span className="text-zinc-400 tabular-nums">{d.score} / 5</span>
                </div>
                <div className="flex gap-1">
                  {[1, 2, 3, 4, 5].map((n) => (
                    <span
                      key={n}
                      className={cn(
                        "h-1.5 flex-1 rounded-full",
                        n <= d.score
                          ? d.score >= 4
                            ? "bg-emerald-400"
                            : d.score === 3
                              ? "bg-sky-400"
                              : "bg-amber-400"
                          : "bg-zinc-800",
                      )}
                    />
                  ))}
                </div>
                <p className="text-zinc-300">{d.feedback}</p>
                {d.evidence && <p className="text-xs text-zinc-500">{d.evidence}</p>}
              </div>
            ))}
          </CardContent>
        </Card>

        <div className="flex flex-col gap-6 lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <ThumbsUp className="size-4 text-emerald-400" /> Strengths
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm">
              <List items={report.strengths} />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <TrendingUp className="size-4 text-amber-400" /> Do Differently
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm">
              <List items={report.improvements} />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <BookOpen className="size-4 text-brand-400" /> Study Next
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm">
              <List items={report.study_topics} />
            </CardContent>
          </Card>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Your Design</CardTitle>
        </CardHeader>
        <CardContent className="hidden gap-4 lg:grid lg:grid-cols-[minmax(0,1fr)_320px]">
          <div className="h-[460px]">
            <DesignCanvas
              initialElements={diagramElements}
              readOnly
              onReady={(handle) => {
                yourCanvas.current = handle;
              }}
            />
          </div>
          <div className="flex flex-col gap-2 text-sm">
            <p className="text-xs font-medium tracking-wide text-zinc-500 uppercase">
              Notes on your diagram
            </p>
            {report.diagram_comments.length ? (
              report.diagram_comments.map((c) => (
                <button
                  key={c.ref + c.comment}
                  type="button"
                  onClick={() => yourCanvas.current?.focusElements([c.element_id])}
                  className="rounded-md border border-zinc-800 p-2 text-left hover:border-zinc-700"
                >
                  <span className="font-medium text-zinc-100">
                    {c.label || "Component"}
                  </span>
                  <span className="block text-zinc-400">{c.comment}</span>
                </button>
              ))
            ) : (
              <p className="text-zinc-500">No component-specific notes.</p>
            )}
          </div>
        </CardContent>
        <CardContent className="text-sm text-zinc-500 lg:hidden">
          Open this report on a larger screen to see your diagram.
        </CardContent>
      </Card>

      {reference && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Reference Design</CardTitle>
            <p className="text-sm text-zinc-400">
              One strong answer, not the only one. The interviewer used these
              notes to answer your questions and pick deep-dive topics.
            </p>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="hidden h-[460px] lg:block">
              <DesignCanvas reference={reference} readOnly />
            </div>
            <div className="grid gap-2 lg:grid-cols-2">
              <Collapsible title="Clarifications" defaultOpen>
                <ul className="space-y-1.5 text-zinc-300">
                  {reference.clarifications.map((c, i) => (
                    <li key={i}>
                      <span className="font-medium text-zinc-100">{c.topic}:</span>{" "}
                      {c.answer}
                    </li>
                  ))}
                </ul>
              </Collapsible>
              <Collapsible title="Expected Estimates" defaultOpen>
                <List items={reference.estimation_notes} />
              </Collapsible>
              <Collapsible title="Functional Requirements">
                <List items={reference.functional_requirements} />
              </Collapsible>
              <Collapsible title="Non-Functional Requirements">
                <List items={reference.non_functional_requirements} />
              </Collapsible>
              <Collapsible title="Components">
                <ul className="space-y-1.5 text-zinc-300">
                  {reference.reference_components.map((c) => (
                    <li key={c.id}>
                      <span className="font-medium text-zinc-100">{c.label}:</span>{" "}
                      {c.purpose}
                    </li>
                  ))}
                </ul>
              </Collapsible>
              <Collapsible title="Deep-Dive Topics">
                <List items={reference.deep_dive_topics} />
              </Collapsible>
              <Collapsible title="Common Pitfalls">
                <List items={reference.pitfalls} />
              </Collapsible>
            </div>
          </CardContent>
        </Card>
      )}

      <Collapsible title={`Transcript (${status.messages.length} messages)`}>
        <div className="flex flex-col gap-2">
          {status.messages.map((m) => (
            <div key={m.id} className="flex gap-2">
              <MessageSquareText
                className={cn(
                  "mt-0.5 size-4 shrink-0",
                  m.role === "INTERVIEWER" ? "text-brand-400" : "text-zinc-500",
                )}
              />
              <div>
                <span className="text-xs text-zinc-500">
                  {m.role === "INTERVIEWER" ? "Interviewer" : "You"} ·{" "}
                  {PHASE_LABELS[m.phase]}
                </span>
                <p className="whitespace-pre-wrap text-zinc-300">{m.content}</p>
              </div>
            </div>
          ))}
        </div>
      </Collapsible>
    </div>
  );
}
