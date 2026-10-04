import { DSA_TOPICS } from "@/content/dsa/index.ts";
import { DSA_LANGUAGE_NAMES } from "@/lib/dsa";
import { OG_CONTENT_TYPE, OG_SIZE, ogCard } from "@/lib/og";

export const alt = "Resland's DSA Study Center: data structures and algorithms for coding interviews";
export const size = OG_SIZE;
export const contentType = OG_CONTENT_TYPE;

export default function Image() {
  const problems = DSA_TOPICS.reduce((n, t) => n + t.problems.length, 0);
  return ogCard({
    eyebrow: "DSA Study Center",
    title: "Data structures and algorithms for coding interviews",
    subtitle: `${DSA_TOPICS.length} topics, ${problems} worked problems, code in ${DSA_LANGUAGE_NAMES}.`,
  });
}
