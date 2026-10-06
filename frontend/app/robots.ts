import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      // Rules match by prefix, so the app routes that share a stem with a
      // possible public page (/tailor-resume-to-job-description,
      // /system-design-interview/...) are pinned with $ or a trailing slash.
      disallow: [
        "/dashboard",
        "/onboarding",
        "/edit-profile",
        "/tailor$",
        "/tailored",
        "/billing",
        "/admin",
        "/test-upload",
        "/system-design$",
        "/system-design/",
        "/maintenance",
        "/auth/",
        "/api/",
      ],
    },
    sitemap: "https://resland.org/sitemap.xml",
  };
}
