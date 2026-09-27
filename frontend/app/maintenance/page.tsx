import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";

// Served with a 503 + Retry-After while MAINTENANCE_MODE is on; crawlers treat
// that as a temporary outage and keep the existing index, so inherit the root
// layout's SEO metadata rather than marking anything noindex.
export const metadata: Metadata = {
  title: "Down for maintenance",
};

export default function MaintenancePage() {
  return (
    <main className="flex min-h-full flex-1 items-center justify-center bg-zinc-950 px-6 py-24 text-center">
      <div className="flex max-w-md flex-col items-center gap-5">
        <Image
          src="/resland-logo.png"
          alt="Resland"
          width={64}
          height={64}
          priority
        />
        <h1 className="bg-gradient-to-r from-purple-300 to-violet-500 bg-clip-text text-3xl font-semibold text-transparent">
          Down for maintenance
        </h1>
        <p className="text-zinc-400">
          Resland is temporarily paused while we make some updates. Your data is
          safe — please check back shortly.
        </p>
        <Link
          href="/auth/login?returnTo=%2Fdashboard"
          className="text-sm text-zinc-500 hover:text-zinc-300"
        >
          Admin? Log in
        </Link>
        <Link
          href="/auth/logout"
          className="text-sm text-zinc-500 hover:text-zinc-300"
        >
          Sign out
        </Link>
      </div>
    </main>
  );
}
