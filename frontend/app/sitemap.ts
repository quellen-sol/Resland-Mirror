import type { MetadataRoute } from "next";
import { DSA_TOPICS } from "@/content/dsa/index.ts";
import { orderTopics } from "@/lib/dsa";
import { absoluteUrl } from "@/lib/seo";

// No lastModified: the sitemap is built at deploy time, and stamping every
// page with the deploy date would tell crawlers unchanged pages changed.
// Google ignores lastmod once it proves unreliable.
export default function sitemap(): MetadataRoute.Sitemap {
  return [
    { url: absoluteUrl("/") },
    { url: absoluteUrl("/dsa") },
    ...orderTopics(DSA_TOPICS).map((t) => ({ url: absoluteUrl(`/dsa/${t.slug}`) })),
    { url: absoluteUrl("/help") },
  ];
}
