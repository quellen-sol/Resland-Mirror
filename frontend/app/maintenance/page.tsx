import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import Backdrop from "@/components/backdrop";

// Served with a 503 + Retry-After in place of the signed-in app while
// maintenance mode is on (public pages stay up with a banner); crawlers treat
// that as a temporary outage and keep the existing index, so inherit the root
// layout's SEO metadata rather than marking anything noindex.
export const metadata: Metadata = {
  title: "Down for Maintenance",
};

export default function MaintenancePage() {
  return (
    <main className="relative flex min-h-full flex-1 items-center justify-center overflow-hidden px-6 py-24">
      <Backdrop />
      <div className="rise relative w-full max-w-md text-center">
        <div className="edge rounded-2xl border border-white/[.08] bg-card px-8 py-10">
          <Image
            src="/resland-logo.png"
            alt="Resland"
            width={48}
            height={48}
            preload
            className="mx-auto"
          />
          <p className="mt-6 inline-flex items-center gap-2 rounded-full border border-red-500/30 bg-red-500/10 px-3 py-1 font-mono text-xs tracking-wider text-red-300 uppercase">
            <span className="size-1.5 rounded-full bg-red-400 motion-safe:animate-pulse" />
            Maintenance
          </p>
          <h1 className="mt-4 text-3xl font-semibold tracking-[-0.03em]">
            Down for Maintenance
          </h1>
          <p className="mt-3 leading-7 text-zinc-400">
            Resland is down for a bit while we make some updates. Your data is
            safe. Check back soon.
          </p>
          <Link
            href="/"
            className="mt-8 inline-flex h-10 items-center gap-2 rounded-xl bg-white px-5 text-sm font-medium text-zinc-950 hover:bg-zinc-200"
          >
            <ArrowLeft className="size-4" /> Back to Home
          </Link>
        </div>
        {/* Plain <a>s: a <Link> would prefetch these auth routes. */}
        <div className="mt-6 flex justify-center gap-3 text-sm text-zinc-500">
          <a
            href="/auth/login?returnTo=%2Fdashboard"
            className="hover:text-zinc-300"
          >
            Admin? Log In
          </a>
          <span aria-hidden>·</span>
          <a href="/auth/logout" className="hover:text-zinc-300">
            Sign Out
          </a>
        </div>
      </div>
    </main>
  );
}
