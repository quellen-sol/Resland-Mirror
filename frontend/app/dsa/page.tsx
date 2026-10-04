import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { DSA_TOPICS } from "@/content/dsa/index.ts";
import {
  DSA_LANGUAGES,
  groupTopicsByCategory,
  orderTopics,
  toTopicRef,
} from "@/lib/dsa";
import { LevelBadge } from "./badges";
import { LanguageTabs } from "./language";
import {
  CategoryCount,
  ProgressOverview,
  StudiedCheck,
} from "./progress-ui";

const DESCRIPTION =
  "Learn data structures and algorithms one topic at a time, with worked problems and code in TypeScript, Python, Go, C# and Java.";

export const metadata: Metadata = {
  title: "DSA Study Center",
  description: DESCRIPTION,
  alternates: { canonical: "/dsa" },
  openGraph: { title: "DSA Study Center", description: DESCRIPTION, url: "/dsa" },
};

export default function DsaIndexPage() {
  const ordered = orderTopics(DSA_TOPICS);
  const refs = ordered.map(toTopicRef);
  const problemCount = DSA_TOPICS.reduce((n, t) => n + t.problems.length, 0);

  return (
    <main className="relative mx-auto flex w-full max-w-6xl flex-col gap-10 px-6 pt-8 pb-16">
      <section className="flex flex-col gap-4">
        <p className="font-mono text-xs tracking-wider text-brand-400 uppercase">
          DSA Study Center
        </p>
        <h1 className="max-w-3xl text-4xl font-semibold tracking-[-0.03em] text-balance sm:text-5xl">
          Data structures and algorithms, one topic at a time.
        </h1>
        <p className="max-w-2xl text-[17px] leading-7 text-zinc-400">
          {DSA_TOPICS.length} topics, each with how it works, how to spot it in an
          interview question, and {problemCount} classic problems worked through
          step by step. Every example comes in {DSA_LANGUAGES.length} languages.
        </p>
        <div className="mt-2 flex flex-wrap items-center gap-3">
          <Link
            href={`/dsa/${ordered[0].slug}`}
            className="inline-flex h-10 items-center gap-2 rounded-xl bg-white px-5 text-sm font-medium text-zinc-950 hover:bg-zinc-200"
          >
            Start with {ordered[0].title} <ArrowRight className="size-4" />
          </Link>
          <div className="flex flex-wrap items-center gap-2 rounded-xl border border-white/[.08] bg-zinc-950/50 py-1 pr-1 pl-3">
            <span className="text-xs text-zinc-500">Show code in</span>
            <LanguageTabs label="Code language" />
          </div>
        </div>
      </section>

      <ProgressOverview topics={refs} />

      {groupTopicsByCategory(ordered).map(({ category, topics }) => (
        <section key={category.id} className="flex flex-col gap-4">
          <div className="flex items-end justify-between gap-4 border-b border-white/[.06] pb-3">
            <div>
              <h2 className="text-xl font-semibold tracking-tight">{category.title}</h2>
              <p className="mt-1 text-sm text-zinc-500">{category.blurb}</p>
            </div>
            <CategoryCount topics={refs} category={category.id} />
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {topics.map((topic) => (
              <Link
                key={topic.slug}
                href={`/dsa/${topic.slug}`}
                className="group edge flex flex-col gap-2 rounded-xl border border-white/[.08] bg-card p-4 transition-colors hover:border-brand-500/40"
              >
                <span className="flex items-center justify-between gap-2">
                  <span className="font-medium text-zinc-100 group-hover:text-white">
                    {topic.title}
                  </span>
                  <StudiedCheck slug={topic.slug} />
                </span>
                <span className="text-sm leading-6 text-zinc-400">{topic.summary}</span>
                <span className="mt-auto flex items-center gap-2 pt-1 text-xs text-zinc-500">
                  <LevelBadge level={topic.level} />
                  {topic.problems.length} worked{" "}
                  {topic.problems.length === 1 ? "problem" : "problems"}
                </span>
              </Link>
            ))}
          </div>
        </section>
      ))}
    </main>
  );
}
