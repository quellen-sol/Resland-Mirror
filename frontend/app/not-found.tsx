import Link from "next/link";

export default function NotFound() {
  return (
    <main className="flex min-h-full flex-1 items-center justify-center bg-zinc-950 px-6 py-24 text-center">
      <div className="flex max-w-md flex-col items-center gap-5">
        <h1 className="bg-gradient-to-r from-purple-300 to-violet-500 bg-clip-text text-3xl font-semibold text-transparent">Page not found</h1>
        <p className="text-zinc-400">That Resland page doesn&apos;t exist.</p>
        <div className="flex gap-3">
          <Link href="/" className="inline-flex h-8 items-center rounded-lg bg-purple-600 px-2.5 text-sm font-medium text-white hover:bg-purple-500">Back home</Link>
          <Link href="/dashboard" className="inline-flex h-8 items-center rounded-lg border border-zinc-700 px-2.5 text-sm font-medium text-zinc-300 hover:bg-zinc-800">Dashboard</Link>
        </div>
      </div>
    </main>
  );
}
