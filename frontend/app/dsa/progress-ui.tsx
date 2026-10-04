"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { CheckCircle2, Circle, LogIn } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "cn";
import {
  summarizeProgress,
  type DsaCategoryId,
  type DsaTopicRef,
} from "@/lib/dsa";
import { useDsaProgress } from "./progress";

function loginHref(returnTo: string) {
  return `/auth/login?returnTo=${encodeURIComponent(returnTo)}`;
}

/** Toggle for the current topic. Signed-out visitors get a sign-in link. */
export function MarkStudiedButton({ slug }: { slug: string }) {
  const { state, setStudied } = useDsaProgress();
  const pathname = usePathname();

  if (state.status === "loading") {
    return <div aria-hidden className="h-8 w-36 animate-pulse rounded-lg bg-zinc-800/60" />;
  }
  if (state.status === "unavailable") return null;
  if (state.status === "anonymous") {
    return (
      <a
        href={loginHref(pathname)}
        className="inline-flex h-8 items-center gap-1.5 rounded-lg border border-zinc-700 px-2.5 text-sm font-medium text-zinc-300 hover:bg-zinc-800/60 hover:text-zinc-100"
      >
        <LogIn className="size-4" /> Sign In to Track Progress
      </a>
    );
  }

  const studied = state.studied.has(slug);
  return (
    <Button
      variant={studied ? "outline" : "default"}
      aria-pressed={studied}
      onClick={() => setStudied(slug, !studied)}
      className={cn(
        studied &&
          "border-emerald-500/40 bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/15 hover:text-emerald-200 dark:border-emerald-500/40 dark:bg-emerald-500/10 dark:hover:bg-emerald-500/15",
      )}
    >
      {studied ? <CheckCircle2 /> : <Circle />}
      {studied ? "Studied" : "Mark as Studied"}
    </Button>
  );
}

/** A check beside a topic the visitor has studied; nothing otherwise. */
export function StudiedCheck({ slug, className }: { slug: string; className?: string }) {
  const { state } = useDsaProgress();
  if (state.status !== "ready" || !state.studied.has(slug)) return null;
  return (
    <CheckCircle2
      aria-label="Studied"
      className={cn("size-4 shrink-0 text-emerald-400", className)}
    />
  );
}

function ProgressBar({ done, total }: { done: number; total: number }) {
  const pct = total ? Math.round((done / total) * 100) : 0;
  return (
    <div
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={total}
      aria-valuenow={done}
      className="h-1.5 w-full overflow-hidden rounded-full bg-zinc-800"
    >
      <div
        className="h-full rounded-full bg-gradient-to-r from-brand-400 to-brand-cyan transition-[width] duration-500"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

/** Overall progress for the index page, or a sign-in prompt. */
export function ProgressOverview({ topics }: { topics: readonly DsaTopicRef[] }) {
  const { state } = useDsaProgress();

  if (state.status === "loading") {
    return <div aria-hidden className="h-[74px] animate-pulse rounded-xl bg-zinc-900/60" />;
  }
  if (state.status === "unavailable") return null;
  if (state.status === "anonymous") {
    return (
      <div className="edge flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/[.08] bg-card px-5 py-4">
        <p className="text-sm text-zinc-400">
          Sign in to mark topics as studied and pick up where you left off.
        </p>
        <a
          href={loginHref("/dsa")}
          className="inline-flex h-8 items-center gap-1.5 rounded-lg bg-white px-3 text-sm font-medium text-zinc-950 hover:bg-zinc-200"
        >
          <LogIn className="size-4" /> Sign In
        </a>
      </div>
    );
  }

  const { done, total } = summarizeProgress(topics, state.studied);
  const next = topics.find((t) => !state.studied.has(t.slug));
  return (
    <div className="edge flex flex-col gap-3 rounded-xl border border-white/[.08] bg-card px-5 py-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="text-sm text-zinc-300">
          <span className="font-semibold text-zinc-100">{done}</span> of {total} topics studied
        </p>
        {next && (
          <Link
            href={`/dsa/${next.slug}`}
            className="text-sm text-brand-300 underline-offset-4 hover:text-brand-200 hover:underline"
          >
            Up next: {next.title}
          </Link>
        )}
      </div>
      <ProgressBar done={done} total={total} />
    </div>
  );
}

/** "3 / 5" beside a category heading. */
export function CategoryCount({
  topics,
  category,
}: {
  topics: readonly DsaTopicRef[];
  category: DsaCategoryId;
}) {
  const { state } = useDsaProgress();
  if (state.status !== "ready") return null;
  const counts = summarizeProgress(topics, state.studied).byCategory[category];
  if (!counts) return null;
  return (
    <span className="font-mono text-xs text-zinc-500">
      {counts.done} / {counts.total}
    </span>
  );
}
