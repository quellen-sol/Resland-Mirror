import type { Metadata } from "next";
import type { Viewport } from "next";
import type { ReactNode } from "react";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL("https://resland.org"),
  title: {
    default: "Resland — AI Resume Tailoring",
    template: "%s · Resland",
  },
  description:
    "Resland rewrites your resume for each job you apply to, and asks you for the details instead of making them up.",
  keywords: [
    "resume tailoring",
    "AI resume builder",
    "resume optimization",
    "job applications",
  ],
  applicationName: "Resland",
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    url: "https://resland.org",
    siteName: "Resland",
    title: "Resland — AI Resume Tailoring",
    description:
      "Resland rewrites your resume for each job you apply to, and asks you for the details instead of making them up.",
    images: [
      {
        url: "/resland-logo.png",
        width: 1254,
        height: 1254,
        alt: "Resland logo",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Resland — AI Resume Tailoring",
    description:
      "Resland rewrites your resume for each job you apply to, and asks you for the details instead of making them up.",
    images: ["/resland-logo.png"],
  },
  icons: {
    icon: [
      { url: "/favicon-16x16.png", sizes: "16x16", type: "image/png" },
      { url: "/favicon-32x32.png", sizes: "32x32", type: "image/png" },
    ],
    apple: "/apple-touch-icon.png",
  },
  manifest: "/manifest.webmanifest",
  robots: { index: true, follow: true },
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
      <body className="flex min-h-full flex-col">{children}</body>
    </html>
  );
}
