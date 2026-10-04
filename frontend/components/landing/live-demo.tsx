"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import Image from "next/image";
import { Check, CircleCheck } from "lucide-react";
import { cn } from "cn";
import {
  DEMO_SCRIPT,
  DEMO_STATIC_FRAME,
  demoFrameAt,
  type DemoFrame,
} from "@/lib/live-demo";
import { useReducedMotion } from "./use-reduced-motion";

function Step({
  on,
  className,
  children,
}: {
  on: boolean;
  className?: string;
  children: ReactNode;
}) {
  return (
    <div
      className={cn(
        "transition duration-400",
        on ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0",
        className,
      )}
    >
      {children}
    </div>
  );
}

/** The hero's looping "Improve This Bullet" exchange. Renders the finished
 *  exchange on the server and for reduced motion; otherwise plays the loop
 *  while it's on screen. */
export default function LiveDemo() {
  const reducedMotion = useReducedMotion();
  const rootRef = useRef<HTMLDivElement>(null);
  const [playing, setPlaying] = useState<DemoFrame | null>(null);
  const frame = reducedMotion ? DEMO_STATIC_FRAME : (playing ?? DEMO_STATIC_FRAME);

  useEffect(() => {
    const root = rootRef.current;
    if (reducedMotion || !root) return;
    let raf = 0;
    let running = false;
    let origin = 0;
    let pausedAt = 0;
    let lastKey = "";
    const tick = (now: number) => {
      const next = demoFrameAt(now - origin);
      const key = JSON.stringify(next);
      if (key !== lastKey) {
        lastKey = key;
        setPlaying(next);
      }
      raf = requestAnimationFrame(tick);
    };
    const play = () => {
      if (running) return;
      running = true;
      origin = performance.now() - pausedAt;
      raf = requestAnimationFrame(tick);
    };
    const pause = () => {
      if (!running) return;
      running = false;
      cancelAnimationFrame(raf);
      pausedAt = performance.now() - origin;
    };
    // Only animate while the demo is on screen.
    const io = new IntersectionObserver(([entry]) =>
      entry.isIntersecting ? play() : pause(),
    );
    io.observe(root);
    return () => {
      io.disconnect();
      pause();
    };
  }, [reducedMotion]);

  return (
    <div className="relative">
      <div
        aria-hidden
        className="absolute -inset-6 rounded-[32px] bg-brand-400/10 blur-2xl"
      />
      <figure className="relative rounded-[20px] bg-gradient-to-b from-white/15 via-white/5 to-white/[.02] p-px">
        <figcaption className="sr-only">
          Resland asks “{DEMO_SCRIPT.question}” You answer “{DEMO_SCRIPT.answer}”
          and it writes three options: {DEMO_SCRIPT.options.join(" ")}
        </figcaption>
        <div
          ref={rootRef}
          aria-hidden
          className="relative min-h-[430px] overflow-hidden rounded-[19px] bg-card"
        >
          <div className="flex items-center justify-between border-b border-white/[.07] px-5 py-3.5">
            <div>
              <p className="text-sm font-medium">Improve This Bullet</p>
              <p className="text-xs text-zinc-500">
                Senior Engineer · Northwind Logistics
              </p>
            </div>
            <span className="rounded-md border border-white/10 px-2 py-0.5 font-mono text-[11px] text-zinc-500">
              Default model
            </span>
          </div>

          <div className="space-y-4 p-5 text-sm">
            <div>
              <p className="font-mono text-[11px] tracking-wider text-zinc-500 uppercase">
                Your bullet point
              </p>
              <p
                className={cn(
                  "mt-1.5 leading-6 transition-colors duration-500",
                  frame.struck
                    ? "text-red-300/55 line-through decoration-red-400/50"
                    : "text-zinc-300",
                )}
              >
                {DEMO_SCRIPT.bullet}
              </p>
            </div>

            <Step on={frame.questionVisible} className="flex gap-3">
              <Image
                src="/resland-logo.png"
                alt=""
                width={24}
                height={24}
                className="mt-0.5 size-6 shrink-0"
              />
              <div className="edge rounded-xl rounded-tl-sm border border-white/[.08] bg-panel-raised px-3.5 py-2.5 text-zinc-200">
                {frame.thinking ? (
                  <span className="thinking-dots text-zinc-500">
                    Thinking<span>.</span>
                    <span>.</span>
                    <span>.</span>
                  </span>
                ) : (
                  <span
                    className={cn(frame.typing === "question" && "typing-caret")}
                  >
                    {frame.question}
                  </span>
                )}
              </div>
            </Step>

            <Step on={frame.answerVisible} className="flex justify-end">
              <div className="rounded-xl rounded-tr-sm bg-brand-400/90 px-3.5 py-2.5 text-white">
                <span className={cn(frame.typing === "answer" && "typing-caret")}>
                  {frame.answer}
                </span>
              </div>
            </Step>

            <div className="space-y-2">
              {DEMO_SCRIPT.options.map((option, i) => {
                const picked = frame.picked === i;
                return (
                  <Step
                    key={option}
                    on={frame.optionsShown > i}
                    className={cn(
                      "rounded-xl border px-3.5 py-2.5 transition-colors duration-300",
                      picked
                        ? "border-emerald-400/40 bg-emerald-400/[.08]"
                        : "border-white/[.08] bg-black/20",
                    )}
                  >
                    <p
                      className={cn(
                        "font-mono text-[11px] tracking-wider uppercase",
                        picked ? "text-emerald-300/90" : "text-zinc-500",
                      )}
                    >
                      Option {i + 1}
                    </p>
                    <p
                      className={cn(
                        "mt-1 leading-6",
                        picked ? "text-emerald-100" : "text-zinc-300",
                      )}
                    >
                      {option}
                    </p>
                  </Step>
                );
              })}
            </div>

            <Step on={frame.actionsVisible} className="flex gap-2">
              <span
                className={cn(
                  "inline-flex h-8 items-center gap-1.5 rounded-lg bg-white px-3 font-medium text-zinc-950 transition duration-150",
                  frame.acceptPressed && "scale-[.94] ring-4 ring-brand-400/35",
                )}
              >
                <Check className="size-4" /> Accept
              </span>
              <span className="inline-flex h-8 items-center rounded-lg border border-white/10 px-3 text-zinc-300">
                More Options
              </span>
            </Step>
          </div>

          <Step
            on={frame.toastVisible}
            className="absolute right-4 bottom-4 flex items-center gap-2 rounded-lg border border-white/10 bg-zinc-900/95 px-3 py-2 text-sm shadow-xl"
          >
            <CircleCheck className="size-4 text-emerald-400" /> Suggestion
            applied
          </Step>
        </div>
      </figure>
    </div>
  );
}
