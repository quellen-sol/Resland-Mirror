import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, ArrowRight, ExternalLink } from "lucide-react";
import { DSA_TOPICS } from "@/content/dsa/index.ts";
import {
  DSA_CATEGORIES,
  DSA_LANGUAGE_NAMES,
  DSA_LEVEL_LABELS,
  topicDependents,
  topicMetaDescription,
  topicNeighbors,
  type DsaTopic,
} from "@/lib/dsa";
import { absoluteUrl, breadcrumbJsonLd, pageMetadata } from "@/lib/seo";
import JsonLd from "@/components/json-ld";
import { ComplexityNote, DifficultyBadge, LevelBadge } from "../badges";
import CodeBlock from "../code-block";
import { Blocks, Inline } from "../prose";
import { MarkStudiedButton } from "../progress-ui";

// Every topic is prerendered; anything else is a 404.
export const dynamicParams = false;

export function generateStaticParams() {
  return DSA_TOPICS.map((t) => ({ slug: t.slug }));
}

function findTopic(slug: string): DsaTopic | undefined {
  return DSA_TOPICS.find((t) => t.slug === slug);
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const topic = findTopic((await params).slug);
  if (!topic) return {};
  return pageMetadata({
    title: topic.seoTitle,
    description: topicMetaDescription(topic),
    path: `/dsa/${topic.slug}`,
    type: "article",
    // ./opengraph-image.tsx renders the topic's own card.
    ownImage: true,
  });
}

const SECTIONS = [
  ["how-it-works", "How It Works"],
  ["spotting-it", "When to Reach for It"],
  ["complexity", "Complexity"],
  ["template", "The Template"],
  ["problems", "Worked Problems"],
  ["pitfalls", "Common Pitfalls"],
  ["practice", "Practice"],
] as const;

type SectionId = (typeof SECTIONS)[number][0];

function Section({
  id,
  children,
}: {
  id: SectionId;
  children: React.ReactNode;
}) {
  const title = SECTIONS.find(([s]) => s === id)![1];
  return (
    <section id={id} aria-labelledby={`${id}-title`} className="flex scroll-mt-6 flex-col gap-5">
      <h2 id={`${id}-title`} className="text-2xl font-semibold tracking-tight">
        {title}
      </h2>
      {children}
    </section>
  );
}

const subheading = "text-xs font-medium tracking-wide text-zinc-500 uppercase";

export default async function TopicPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const topic = findTopic((await params).slug);
  if (!topic) notFound();

  const category = DSA_CATEGORIES.find((c) => c.id === topic.category)!;
  const prerequisites = topic.prerequisites
    .map(findTopic)
    .filter((t): t is DsaTopic => t !== undefined);
  const { prev, next } = topicNeighbors(DSA_TOPICS, topic.slug);
  const dependents = topicDependents(DSA_TOPICS, topic.slug);
  const path = `/dsa/${topic.slug}`;
  const jsonLd = [
    {
      "@context": "https://schema.org",
      "@type": "LearningResource",
      name: topic.seoTitle,
      description: topic.summary,
      url: absoluteUrl(path),
      learningResourceType: "Tutorial",
      educationalLevel: DSA_LEVEL_LABELS[topic.level],
      teaches: topic.title,
      inLanguage: "en",
      isPartOf: { "@type": "WebSite", name: "Resland", url: absoluteUrl("/") },
    },
    breadcrumbJsonLd([
      { name: "Resland", path: "/" },
      { name: "DSA Study Center", path: "/dsa" },
      { name: topic.title, path },
    ]),
  ];

  return (
    <article className="flex flex-col gap-14">
      <header className="flex flex-col gap-4">
        <nav aria-label="Breadcrumb" className="text-sm text-zinc-500">
          <Link href="/dsa" className="hover:text-zinc-300">
            Study Center
          </Link>
          <span aria-hidden className="px-2 text-zinc-700">
            /
          </span>
          <Link href={`/dsa#${category.id}`} className="hover:text-zinc-300">
            {category.title}
          </Link>
        </nav>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <h1 className="text-4xl font-semibold tracking-[-0.03em]">{topic.title}</h1>
          <MarkStudiedButton slug={topic.slug} />
        </div>
        <p className="max-w-3xl text-[17px] leading-7 text-zinc-400">
          <Inline text={topic.summary} />
        </p>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2 text-sm text-zinc-500">
          <LevelBadge level={topic.level} />
          {prerequisites.length > 0 && (
            <span>
              Read first:{" "}
              {prerequisites.map((p, i) => (
                <span key={p.slug}>
                  {i > 0 && ", "}
                  <Link
                    href={`/dsa/${p.slug}`}
                    className="text-zinc-300 underline-offset-4 hover:text-white hover:underline"
                  >
                    {p.title}
                  </Link>
                </span>
              ))}
            </span>
          )}
        </div>
        <nav
          aria-label="On this page"
          className="flex flex-wrap gap-1.5 border-t border-white/[.06] pt-4"
        >
          {SECTIONS.map(([id, title]) => (
            <a
              key={id}
              href={`#${id}`}
              className="rounded-md border border-white/[.08] px-2 py-1 text-xs text-zinc-400 hover:border-white/20 hover:text-zinc-200"
            >
              {title}
            </a>
          ))}
        </nav>
        <nav aria-label="Worked problems" className="-mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs">
          <span className="text-zinc-500">Worked problems:</span>
          {topic.problems.map((problem) => (
            <a
              key={problem.id}
              href={`#${problem.id}`}
              className="text-zinc-400 underline-offset-4 hover:text-zinc-200 hover:underline"
            >
              {problem.title}
            </a>
          ))}
        </nav>
      </header>

      <Section id="how-it-works">
        <Blocks blocks={topic.overview} />
      </Section>

      <Section id="spotting-it">
        <ul className="flex flex-col gap-2 pl-5 leading-7 text-zinc-300 marker:text-brand-400 list-disc">
          {topic.signals.map((signal, i) => (
            <li key={i} className="pl-1">
              <Inline text={signal} />
            </li>
          ))}
        </ul>
      </Section>

      <Section id="complexity">
        <div className="edge overflow-x-auto rounded-xl border border-white/[.08]">
          <table className="w-full text-left text-sm">
            <thead className="bg-white/[.03] text-xs tracking-wide text-zinc-500 uppercase">
              <tr>
                <th scope="col" className="px-4 py-2.5 font-medium">Operation</th>
                <th scope="col" className="px-4 py-2.5 font-medium">Time</th>
                <th scope="col" className="px-4 py-2.5 font-medium">Space</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[.06]">
              {topic.complexity.map((row) => (
                <tr key={row.operation}>
                  <td className="px-4 py-2.5 text-zinc-300">
                    <Inline text={row.operation} />
                  </td>
                  <td className="px-4 py-2.5 font-mono text-xs whitespace-nowrap text-zinc-200">
                    {row.time}
                  </td>
                  <td className="px-4 py-2.5 font-mono text-xs text-zinc-200">{row.space}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <Section id="template">
        <h3 className="-mt-2 text-lg font-medium text-zinc-100">{topic.template.title}</h3>
        <Blocks blocks={topic.template.explanation} />
        <ComplexityNote time={topic.template.time} space={topic.template.space} />
        <CodeBlock topicSlug={topic.slug} example={topic.template} />
      </Section>

      <Section id="problems">
        <p className="-mt-2 text-sm text-zinc-500">
          Each solution is a complete program in {DSA_LANGUAGE_NAMES}, run and
          checked against its expected output.
        </p>
        <div className="flex flex-col gap-12">
          {topic.problems.map((problem) => (
            <div key={problem.id} id={problem.id} className="flex scroll-mt-6 flex-col gap-5">
              <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
                <h3 className="text-lg font-medium text-zinc-100">{problem.title}</h3>
                <DifficultyBadge difficulty={problem.difficulty} />
                {problem.link && (
                  <a
                    href={problem.link.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 text-sm text-zinc-500 hover:text-brand-300"
                  >
                    {problem.link.label} <ExternalLink className="size-3.5" />
                  </a>
                )}
              </div>
              <div className="flex flex-col gap-2">
                <p className={subheading}>Problem</p>
                <Blocks blocks={problem.statement} />
              </div>
              <div className="flex flex-col gap-2">
                <p className={subheading}>Approach</p>
                <Blocks blocks={problem.explanation} />
              </div>
              <ComplexityNote time={problem.time} space={problem.space} />
              <CodeBlock topicSlug={topic.slug} example={problem} />
            </div>
          ))}
        </div>
      </Section>

      <Section id="pitfalls">
        <ul className="flex flex-col gap-2 pl-5 leading-7 text-zinc-300 marker:text-amber-400 list-disc">
          {topic.pitfalls.map((pitfall, i) => (
            <li key={i} className="pl-1">
              <Inline text={pitfall} />
            </li>
          ))}
        </ul>
      </Section>

      <Section id="practice">
        <p className="-mt-2 text-sm text-zinc-500">More problems to try on your own.</p>
        <ul className="edge divide-y divide-white/[.06] overflow-hidden rounded-xl border border-white/[.08]">
          {topic.practice.map((p) => (
            <li key={p.url}>
              <a
                href={p.url}
                target="_blank"
                rel="noreferrer"
                className="flex items-center justify-between gap-3 px-4 py-3 text-sm text-zinc-300 hover:bg-white/[.03] hover:text-white"
              >
                <span className="flex items-center gap-2">
                  {p.title} <ExternalLink className="size-3.5 text-zinc-600" />
                </span>
                <DifficultyBadge difficulty={p.difficulty} />
              </a>
            </li>
          ))}
        </ul>
      </Section>

      <footer className="flex flex-col gap-6 border-t border-white/[.06] pt-8">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-zinc-400">Done with {topic.title}?</p>
          <MarkStudiedButton slug={topic.slug} />
        </div>
        {dependents.length > 0 && (
          <p className="text-sm text-zinc-500">
            Builds on this:{" "}
            {dependents.map((d, i) => (
              <span key={d.slug}>
                {i > 0 && ", "}
                <Link
                  href={`/dsa/${d.slug}`}
                  className="text-zinc-300 underline-offset-4 hover:text-white hover:underline"
                >
                  {d.title}
                </Link>
              </span>
            ))}
          </p>
        )}
        <nav aria-label="Topics" className="grid gap-3 sm:grid-cols-2">
          {prev ? (
            <Link
              href={`/dsa/${prev.slug}`}
              className="edge flex flex-col gap-1 rounded-xl border border-white/[.08] bg-card p-4 hover:border-brand-500/40"
            >
              <span className="flex items-center gap-1 text-xs text-zinc-500">
                <ArrowLeft className="size-3.5" /> Previous
              </span>
              <span className="font-medium text-zinc-100">{prev.title}</span>
            </Link>
          ) : (
            <span />
          )}
          {next && (
            <Link
              href={`/dsa/${next.slug}`}
              className="edge flex flex-col items-end gap-1 rounded-xl border border-white/[.08] bg-card p-4 text-right hover:border-brand-500/40"
            >
              <span className="flex items-center gap-1 text-xs text-zinc-500">
                Next <ArrowRight className="size-3.5" />
              </span>
              <span className="font-medium text-zinc-100">{next.title}</span>
            </Link>
          )}
        </nav>
      </footer>

      <aside
        aria-labelledby="interview-cta"
        className="edge flex flex-col gap-3 rounded-2xl border border-white/[.08] bg-card p-6 sm:flex-row sm:items-center sm:justify-between"
      >
        <div>
          <h2 id="interview-cta" className="font-medium text-zinc-100">
            Interview coming up?
          </h2>
          <p className="mt-1 max-w-xl text-sm leading-6 text-zinc-400">
            Resland tailors your resume to the job posting without making
            anything up, and runs mock system design interviews with an AI
            interviewer.
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Link
            href="/"
            className="inline-flex h-9 items-center rounded-lg bg-white px-3.5 text-sm font-medium text-zinc-950 hover:bg-zinc-200"
          >
            Tailor your resume
          </Link>
          <Link
            href="/#prep"
            className="inline-flex h-9 items-center rounded-lg border border-white/10 px-3.5 text-sm text-zinc-300 hover:bg-white/5"
          >
            Practice system design
          </Link>
        </div>
      </aside>

      <JsonLd data={jsonLd} />
    </article>
  );
}
