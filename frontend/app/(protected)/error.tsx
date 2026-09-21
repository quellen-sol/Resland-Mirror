"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function ProtectedError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="flex min-h-full flex-1 items-center justify-center bg-zinc-950 px-6 py-24 text-center">
      <div className="flex max-w-md flex-col items-center gap-5">
        <h1 className="bg-gradient-to-r from-purple-300 to-violet-500 bg-clip-text text-3xl font-semibold text-transparent">
          We couldn&apos;t load your data
        </h1>
        <p className="text-zinc-400">
          The service may be having trouble. Try again or sign out and back in.
        </p>
        <div className="flex gap-3">
          <Button onClick={reset}>Try again</Button>
          <Link
            href="/auth/logout"
            className="inline-flex h-8 items-center rounded-lg border border-zinc-700 px-2.5 text-sm font-medium text-zinc-300 hover:bg-zinc-800"
          >
            Sign out
          </Link>
        </div>
      </div>
    </main>
  );
}
