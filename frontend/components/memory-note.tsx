import Link from "next/link";

/** Shown under an agent's interview questions: the answers outlive the run. */
export default function MemoryNote() {
  return (
    <p className="text-xs text-zinc-500">
      Lasting facts from your answers are saved to{" "}
      {/* A new tab, so a half-typed answer isn't lost. */}
      <Link
        href="/memory"
        target="_blank"
        className="text-zinc-400 underline underline-offset-4 hover:text-zinc-300"
      >
        Memory
      </Link>{" "}
      so you won&apos;t be asked again.
    </p>
  );
}
