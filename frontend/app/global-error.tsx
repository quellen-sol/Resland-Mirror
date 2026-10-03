"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function GlobalError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-zinc-950 text-zinc-100">
        <main className="flex min-h-screen items-center justify-center px-6 py-24 text-center">
          <div className="flex max-w-md flex-col items-center gap-5">
            <h1 className="bg-gradient-to-r from-purple-300 to-violet-500 bg-clip-text text-3xl font-semibold text-transparent">
              Something Went Wrong
            </h1>
            <p className="text-zinc-400">Resland hit an unexpected error.</p>
            <div className="flex gap-3">
              <Button onClick={reset}>Try Again</Button>
              <Link
                href="/"
                className="inline-flex h-8 items-center rounded-lg border border-zinc-700 px-2.5 text-sm font-medium text-zinc-300 hover:bg-zinc-800"
              >
                Back Home
              </Link>
            </div>
          </div>
        </main>
      </body>
    </html>
  );
}
