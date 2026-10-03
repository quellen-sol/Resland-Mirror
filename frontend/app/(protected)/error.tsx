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
        <h1 className="text-3xl font-semibold tracking-[-0.03em]">
          We Couldn&apos;t Load Your Data
        </h1>
        <p className="text-zinc-400">
          The service may be having trouble. Try again or sign out and back in.
        </p>
        <div className="flex gap-3">
          <Button onClick={reset}>Try Again</Button>
          <Link
            href="/auth/logout"
            className="inline-flex h-8 items-center rounded-lg border border-zinc-700 px-2.5 text-sm font-medium text-zinc-300 hover:bg-zinc-800"
          >
            Sign Out
          </Link>
        </div>
      </div>
    </main>
  );
}
