import type { Metadata } from "next";
import type { Viewport } from "next";
import type { ReactNode } from "react";
import { Geist, Geist_Mono } from "next/font/google";
import PageViewTracker from "@/components/page-view-tracker";
import { SITE_DESCRIPTION, SITE_NAME, SITE_URL } from "@/lib/seo";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

// Defaults for pages that don't build their own with pageMetadata()
// (lib/seo.ts). Nothing here may name a page: no canonical, no og:url, and
// no twitter title or image, or every page that inherits them shares as the
// home page. The share image comes from app/opengraph-image.tsx.
export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "Resland: AI Resume Tailoring for Software Engineers",
    template: "%s · Resland",
  },
  description: SITE_DESCRIPTION,
  keywords: [
    "software engineer resume",
    "tailor resume to job description",
    "AI resume tailoring",
    "resume bullet points",
    "system design interview practice",
    "DSA study guide",
    "coding interview prep",
  ],
  applicationName: SITE_NAME,
  openGraph: {
    type: "website",
    siteName: SITE_NAME,
    title: "Resland: AI Resume Tailoring for Software Engineers",
    description: SITE_DESCRIPTION,
  },
  twitter: { card: "summary_large_image" },
  icons: {
    icon: [
      { url: "/favicon-16x16.png", sizes: "16x16", type: "image/png" },
      { url: "/favicon-32x32.png", sizes: "32x32", type: "image/png" },
    ],
    apple: "/apple-touch-icon.png",
  },
  manifest: "/manifest.webmanifest",
  robots: { index: true, follow: true },
  // Search Console / Bing Webmaster Tools ownership tags. Optional: a DNS
  // TXT record verifies the domain without them.
  verification: {
    google: process.env.GOOGLE_SITE_VERIFICATION,
    other: process.env.BING_SITE_VERIFICATION
      ? { "msvalidate.01": process.env.BING_SITE_VERIFICATION }
      : undefined,
  },
};

export const viewport: Viewport = {
  themeColor: "#08080b",
  colorScheme: "dark",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} dark h-full antialiased`}
    >
      <body className="flex min-h-full flex-col">
        {children}
        <PageViewTracker />
      </body>
    </html>
  );
}
