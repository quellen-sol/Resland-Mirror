"use client";

import type { ReactNode } from "react";
import { cn } from "cn";

/** A card that lights up under the pointer (see the `spotlight` utility). */
export default function Spotlight({
  className,
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return (
    <div
      onPointerMove={(e) => {
        const r = e.currentTarget.getBoundingClientRect();
        e.currentTarget.style.setProperty("--x", `${e.clientX - r.left}px`);
        e.currentTarget.style.setProperty("--y", `${e.clientY - r.top}px`);
      }}
      className={cn("spotlight", className)}
    >
      {children}
    </div>
  );
}
