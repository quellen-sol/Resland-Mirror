"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useDsaProgress } from "./progress";

/** Right side of the study center header. These pages are prerendered, so
 *  who's signed in comes from the progress request, not the server render. */
export default function HeaderLinks() {
  const { state } = useDsaProgress();
  const pathname = usePathname();

  if (state.status === "ready") {
    return (
      <Link
        href="/dashboard"
        className="rounded-lg bg-white px-3.5 py-1.5 text-sm font-medium text-zinc-950 hover:bg-zinc-200"
      >
        Dashboard
      </Link>
    );
  }
  if (state.status !== "anonymous") return null;
  return (
    <div className="flex items-center gap-1">
      <a
        href={`/auth/login?returnTo=${encodeURIComponent(pathname)}`}
        className="rounded-lg px-3 py-1.5 text-sm text-zinc-300 hover:bg-white/5 hover:text-white"
      >
        Log In
      </a>
      <a
        href="/auth/login?screen_hint=signup"
        className="rounded-lg bg-white px-3.5 py-1.5 text-sm font-medium text-zinc-950 hover:bg-zinc-200"
      >
        Tailor Your Resume
      </a>
    </div>
  );
}
