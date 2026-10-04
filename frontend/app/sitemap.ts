import type { MetadataRoute } from "next";
import { DSA_TOPICS } from "@/content/dsa/index.ts";

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    { url: "https://resland.org/" },
    { url: "https://resland.org/help" },
    { url: "https://resland.org/dsa" },
    ...DSA_TOPICS.map((t) => ({ url: `https://resland.org/dsa/${t.slug}` })),
  ];
}
