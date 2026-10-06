import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { DSA_TOPICS } from "@/content/dsa/index.ts";
import {
  DSA_LANGUAGE_NAMES,
  DSA_LANGUAGES,
  groupTopicsByCategory,
  orderTopics,
  toTopicRef,
} from "@/lib/dsa";
import { breadcrumbJsonLd, pageMetadata } from "@/lib/seo";
import JsonLd from "@/components/json-ld";
import { LevelBadge } from "./badges";
import { LanguageTabs } from "./language";
import {
  CategoryCount,
  ProgressOverview,
  StudiedCheck,
} from "./progress-ui";

const PROBLEM_COUNT = DSA_TOPICS.reduce((n, t) => n + t.problems.length, 0);

export const metadata: Metadata = pageMetadata({
  title: "Data Structures and Algorithms (DSA) Study Guide",
  description: `Free DSA study guide for coding interviews: ${DSA_TOPICS.length} topics, ${PROBLEM_COUNT} worked problems, and tested solutions in ${DSA_LANGUAGE_NAMES}.`,
  path: "/dsa",
  // ./opengraph-image.tsx
  ownImage: true,
});

export default function DsaIndexPage() {
  const ordered = orderTopics(DSA_TOPICS);
  const refs = ordered.map(toTopicRef);

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
          A free study guide for coding interviews. {DSA_TOPICS.length} topics,
          each with how it works, how to spot it in an interview question, and
          classic problems worked through step by step: {PROBLEM_COUNT} in all.
          Every solution comes in {DSA_LANGUAGES.length} languages and is a
          complete program, run and checked against its expected output.
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
        <section key={category.id} id={category.id} className="flex scroll-mt-6 flex-col gap-4">
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
      <JsonLd
        data={breadcrumbJsonLd([
          { name: "Resland", path: "/" },
          { name: "DSA Study Center", path: "/dsa" },
        ])}
      />
    </main>
  );
}
