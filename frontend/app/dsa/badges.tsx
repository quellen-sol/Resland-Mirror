import { cn } from "cn";
import { DSA_LEVEL_LABELS, type DsaDifficulty, type DsaLevel } from "@/lib/dsa";

const chip =
  "inline-flex items-center rounded border px-1.5 py-px text-[10px] font-medium tracking-wide uppercase";

const DIFFICULTY_STYLES: Record<DsaDifficulty, string> = {
  EASY: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
  MEDIUM: "border-amber-500/30 bg-amber-500/10 text-amber-300",
  HARD: "border-red-500/30 bg-red-500/10 text-red-300",
};

const LEVEL_STYLES: Record<DsaLevel, string> = {
  BEGINNER: "border-sky-500/30 bg-sky-500/10 text-sky-300",
  INTERMEDIATE: "border-brand-500/30 bg-brand-500/10 text-brand-200",
  ADVANCED: "border-fuchsia-500/30 bg-fuchsia-500/10 text-fuchsia-300",
};

export function DifficultyBadge({ difficulty }: { difficulty: DsaDifficulty }) {
  return <span className={cn(chip, DIFFICULTY_STYLES[difficulty])}>{difficulty}</span>;
}

export function LevelBadge({ level }: { level: DsaLevel }) {
  return (
    <span className={cn(chip, LEVEL_STYLES[level])}>{DSA_LEVEL_LABELS[level]}</span>
  );
}

/** An example's time and space cost, e.g. "Time O(n)  Space O(1)". */
export function ComplexityNote({ time, space }: { time: string; space: string }) {
  return (
    <p className="flex flex-wrap gap-x-4 gap-y-1 font-mono text-xs text-zinc-400">
      <span>
        <span className="text-zinc-500">Time</span> {time}
      </span>
      <span>
        <span className="text-zinc-500">Space</span> {space}
      </span>
    </p>
  );
}
