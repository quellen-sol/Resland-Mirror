import { notFound } from "next/navigation";
import { DSA_TOPICS } from "@/content/dsa/index.ts";
import { DSA_CATEGORIES, toPlainText } from "@/lib/dsa";
import { OG_CONTENT_TYPE, OG_SIZE, ogCard } from "@/lib/og";

export const alt = "A topic from Resland's DSA Study Center";
export const size = OG_SIZE;
export const contentType = OG_CONTENT_TYPE;

// One card per topic, built with the pages.
export function generateStaticParams() {
  return DSA_TOPICS.map((t) => ({ slug: t.slug }));
}

export default async function Image({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const topic = DSA_TOPICS.find((t) => t.slug === slug);
  if (!topic) notFound();
  const category = DSA_CATEGORIES.find((c) => c.id === topic.category)!;
  return ogCard({
    eyebrow: `DSA Study Center · ${category.title}`,
    title: topic.title,
    subtitle: toPlainText(topic.summary),
  });
}
