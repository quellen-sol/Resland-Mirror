import { OG_CONTENT_TYPE, OG_SIZE, ogCard } from "@/lib/og";

export const alt = "Resland: AI resume tailoring for software engineers";
export const size = OG_SIZE;
export const contentType = OG_CONTENT_TYPE;

export default function Image() {
  return ogCard({
    eyebrow: "For software engineers",
    title: "A resume for every job. Nothing made up.",
    subtitle: "AI resume tailoring, mock system design interviews and a free DSA study guide.",
  });
}
