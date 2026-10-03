import Link from "next/link";

export default function NotFound() {
  return (
    <main className="flex min-h-full flex-1 items-center justify-center bg-zinc-950 px-6 py-24 text-center">
      <div className="flex max-w-md flex-col items-center gap-5">
        <h1 className="text-3xl font-semibold tracking-[-0.03em]">
          Page Not Found
        </h1>
        <p className="text-zinc-400">That Resland page doesn&apos;t exist.</p>
        <div className="flex gap-3">
          <Link
            href="/"
            className="inline-flex h-8 items-center rounded-lg bg-white px-2.5 text-sm font-medium text-zinc-950 hover:bg-zinc-200"
          >
            Back Home
          </Link>
          <Link
            href="/dashboard"
            className="inline-flex h-8 items-center rounded-lg border border-zinc-700 px-2.5 text-sm font-medium text-zinc-300 hover:bg-zinc-800"
          >
            Dashboard
          </Link>
        </div>
      </div>
    </main>
  );
}
