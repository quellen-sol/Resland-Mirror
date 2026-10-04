"use client";

import {
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type KeyboardEvent,
} from "react";
import Image from "next/image";
import {
  Bookmark,
  Briefcase,
  CircleCheck,
  FileUp,
  GraduationCap,
  List,
  Tags,
} from "lucide-react";
import { cn } from "cn";
import { useReducedMotion } from "./use-reduced-motion";

const TAB_MS = 6000;

const STEPS = [
  {
    title: "Upload your resume",
    body: "A PDF or .docx. Resland pulls out your jobs, bullets, skills and education.",
  },
  {
    title: "Answer a few questions",
    body: "Resland asks what you built and what came of it, then writes three options for each bullet.",
  },
  {
    title: "Tailor it to a job",
    body: "Paste the posting. Resland leads with what it values most, and you save and export the result.",
  },
];

function UploadPanel() {
  return (
    <div className="mx-auto w-full max-w-md">
      <div className="flex items-center gap-3 rounded-xl border border-dashed border-white/15 bg-black/20 p-4">
        <div className="grid size-10 place-items-center rounded-lg bg-brand-400/15 text-brand-400">
          <FileUp className="size-5" />
        </div>
        <div className="flex-1 text-sm">
          <p>jordan-alvarez-resume.pdf</p>
          <div className="mt-2 h-1 rounded-full bg-white/10">
            <div className="h-1 w-full rounded-full bg-gradient-to-r from-brand-400 to-brand-cyan" />
          </div>
        </div>
      </div>
      <ul className="mt-5 grid grid-cols-2 gap-2 text-sm">
        {(
          [
            [Briefcase, "3 jobs"],
            [List, "14 bullets"],
            [Tags, "18 skills"],
            [GraduationCap, "1 degree"],
          ] as const
        ).map(([Icon, label]) => (
          <li
            key={label}
            className="flex items-center gap-2 rounded-lg border border-white/[.07] px-3 py-2.5"
          >
            <Icon className="size-4 text-zinc-500" /> {label}
          </li>
        ))}
      </ul>
      <p className="mt-5 flex items-center gap-2 text-sm text-emerald-300">
        <CircleCheck className="size-4" /> Your profile was updated from your
        resume.
      </p>
    </div>
  );
}

function AnswerPanel() {
  return (
    <div className="mx-auto w-full max-w-md space-y-3 text-sm">
      <p className="text-zinc-400">Built the new checkout flow.</p>
      <div className="flex gap-3">
        <Image
          src="/resland-logo.png"
          alt=""
          width={24}
          height={24}
          className="size-6"
        />
        <div className="rounded-xl rounded-tl-sm border border-white/[.08] bg-panel-raised px-3.5 py-2.5">
          Roughly how many customers used it in the first month?
        </div>
      </div>
      <div className="flex justify-end">
        <div className="rounded-xl rounded-tr-sm bg-brand-400/90 px-3.5 py-2.5 text-white">
          Around 12,000.
        </div>
      </div>
      <div className="rounded-xl border border-emerald-400/20 bg-emerald-400/[.06] p-3.5 text-emerald-100">
        <p className="font-mono text-[11px] tracking-wider text-emerald-300/80 uppercase">
          Option 1 of 3
        </p>
        <p className="mt-1">
          Built the new checkout flow, used by about 12,000 customers in its
          first month.
        </p>
      </div>
    </div>
  );
}

function TailorPanel() {
  return (
    <div className="w-full">
      <div className="grid gap-4 text-sm md:grid-cols-2">
        <div className="rounded-xl border border-white/[.08] bg-black/20 p-4">
          <p className="font-mono text-[11px] tracking-wider text-zinc-500 uppercase">
            Job posting
          </p>
          <p className="mt-2 font-medium">Platform Engineer · Globex</p>
          <p className="mt-2 leading-6 text-zinc-400">
            …has run{" "}
            <mark className="rounded bg-brand-400/15 px-1 text-brand-200">
              Kubernetes in production
            </mark>{" "}
            and cares about{" "}
            <mark className="rounded bg-brand-400/15 px-1 text-brand-200">
              deploy speed
            </mark>
            …
          </p>
        </div>
        <div className="rounded-xl border border-white/[.08] bg-black/20 p-4">
          <p className="font-mono text-[11px] tracking-wider text-zinc-500 uppercase">
            Tailored
          </p>
          <ul className="mt-2 space-y-2 leading-6 text-zinc-300">
            <li>
              Moved 40 services to Kubernetes, cutting deploys from 25 minutes
              to 6.
            </li>
            <li className="text-zinc-500">Ran on-call for a team of eight…</li>
          </ul>
        </div>
      </div>
      <div className="mt-5 flex items-center justify-between rounded-xl border border-white/[.08] px-4 py-3 text-sm">
        <span className="flex items-center gap-2">
          <Bookmark className="size-4 text-brand-400" /> Saved to Tailored
          Resumes
        </span>
        <span className="font-mono text-xs text-zinc-500">globex.docx</span>
      </div>
    </div>
  );
}

const PANELS = [UploadPanel, AnswerPanel, TailorPanel];

export default function HowItWorks() {
  const reducedMotion = useReducedMotion();
  const rootRef = useRef<HTMLDivElement>(null);
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const [active, setActive] = useState(0);
  const [userPicked, setUserPicked] = useState(false);
  const [inView, setInView] = useState(false);
  // Advances on its own until the visitor picks a tab, and only while the
  // section is on screen.
  const auto = !reducedMotion && !userPicked && inView;

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;
    const io = new IntersectionObserver(([entry]) =>
      setInView(entry.isIntersecting),
    );
    io.observe(root);
    return () => io.disconnect();
  }, []);

  useEffect(() => {
    if (!auto) return;
    const id = setTimeout(
      () => setActive((i) => (i + 1) % STEPS.length),
      TAB_MS,
    );
    return () => clearTimeout(id);
  }, [auto, active]);

  function pick(i: number, focus = false) {
    setUserPicked(true);
    setActive(i);
    if (focus) tabRefs.current[i]?.focus();
  }

  function onKeyDown(e: KeyboardEvent<HTMLDivElement>) {
    const last = STEPS.length - 1;
    const next = {
      ArrowDown: active === last ? 0 : active + 1,
      ArrowRight: active === last ? 0 : active + 1,
      ArrowUp: active === 0 ? last : active - 1,
      ArrowLeft: active === 0 ? last : active - 1,
      Home: 0,
      End: last,
    }[e.key];
    if (next === undefined) return;
    e.preventDefault();
    pick(next, true);
  }

  const Panel = PANELS[active];

  return (
    <div ref={rootRef} className="mt-12 grid gap-8 lg:grid-cols-[360px_1fr]">
      <div
        role="tablist"
        aria-label="How Resland works"
        aria-orientation="vertical"
        onKeyDown={onKeyDown}
        className="flex flex-col gap-2"
      >
        {STEPS.map((step, i) => {
          const on = i === active;
          return (
            <button
              key={step.title}
              ref={(el) => {
                tabRefs.current[i] = el;
              }}
              type="button"
              role="tab"
              id={`how-tab-${i}`}
              aria-selected={on}
              aria-controls="how-panel"
              tabIndex={on ? 0 : -1}
              onClick={() => pick(i)}
              className={cn(
                "relative overflow-hidden rounded-xl border p-5 text-left transition-colors",
                on
                  ? "edge border-white/[.08] bg-card"
                  : "border-transparent hover:bg-white/[.02]",
              )}
            >
              <span className="font-mono text-xs text-zinc-500">0{i + 1}</span>
              <span className="mt-2 block font-medium">{step.title}</span>
              <span className="mt-1 block text-sm leading-6 text-zinc-400">
                {step.body}
              </span>
              {on && (
                <span
                  key={active}
                  aria-hidden
                  data-running={auto}
                  style={{ "--tab-duration": `${TAB_MS}ms` } as CSSProperties}
                  className="tab-progress absolute inset-x-0 bottom-0 h-0.5 bg-gradient-to-r from-brand-400 to-brand-cyan"
                />
              )}
            </button>
          );
        })}
      </div>
      <div
        id="how-panel"
        role="tabpanel"
        aria-labelledby={`how-tab-${active}`}
        className="edge relative flex min-h-[360px] items-center overflow-hidden rounded-2xl border border-white/[.08] bg-card p-8"
      >
        <div key={active} className="rise w-full">
          <Panel />
        </div>
      </div>
    </div>
  );
}
