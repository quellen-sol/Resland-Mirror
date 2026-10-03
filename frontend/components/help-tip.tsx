"use client";

import { useState, type ReactNode } from "react";
import Link from "next/link";
import { CircleHelp } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { cn } from "cn";

/** A "?" button that opens a short help dialog. Render it beside a heading
 *  (e.g. in a flex row), not inside it — inside an <h1> screen readers
 *  announce the button as part of the heading text. */
export default function HelpTip({
  title,
  children,
  className,
}: {
  title: string;
  children: ReactNode;
  className?: string;
}) {
  const [open, setOpen] = useState(false);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger
        aria-label={`${title} — Help`}
        title="Help"
        className={cn(
          "inline-flex shrink-0 items-center justify-center rounded-full border border-zinc-700 p-1 text-zinc-400 transition-colors hover:border-purple-500/50 hover:text-purple-300",
          className,
        )}
      >
        <CircleHelp className="size-4" />
      </DialogTrigger>
      <DialogContent className="border-zinc-800 bg-zinc-900 text-zinc-100 sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-zinc-100">
            <CircleHelp className="size-4 text-purple-400" /> {title}
          </DialogTitle>
          <DialogDescription
            render={<div className="flex flex-col gap-2 text-zinc-400" />}
          >
            {children}
          </DialogDescription>
        </DialogHeader>
        <p className="text-sm text-zinc-500">
          More questions? See the{" "}
          <Link
            href="/help"
            onClick={() => setOpen(false)}
            className="text-purple-300 underline-offset-4 hover:underline"
          >
            Help &amp; FAQ
          </Link>{" "}
          page.
        </p>
      </DialogContent>
    </Dialog>
  );
}
