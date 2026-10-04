"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ListTree } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { cn } from "cn";
import type { DsaCategory, DsaTopicRef } from "@/lib/dsa";
import { StudiedCheck } from "./progress-ui";

export interface TopicNavGroup {
  category: DsaCategory;
  topics: DsaTopicRef[];
}

function TopicList({
  groups,
  onNavigate,
}: {
  groups: TopicNavGroup[];
  onNavigate?: () => void;
}) {
  const pathname = usePathname();
  return (
    <nav aria-label="Topics" className="flex flex-col gap-5">
      {groups.map(({ category, topics }) => (
        <div key={category.id} className="flex flex-col gap-1">
          <p className="px-2.5 font-mono text-[11px] tracking-wider text-zinc-500 uppercase">
            {category.title}
          </p>
          {topics.map((topic) => {
            const href = `/dsa/${topic.slug}`;
            const active = pathname === href;
            return (
              <Link
                key={topic.slug}
                href={href}
                onClick={onNavigate}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex items-center justify-between gap-2 rounded-md px-2.5 py-1.5 text-sm transition-colors",
                  active
                    ? "bg-brand-500/15 text-brand-100"
                    : "text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200",
                )}
              >
                <span className="truncate">{topic.title}</span>
                <StudiedCheck slug={topic.slug} className="size-3.5" />
              </Link>
            );
          })}
        </div>
      ))}
    </nav>
  );
}

/** Every topic, grouped by category: a sticky sidebar on wide screens and a
 *  sheet behind a button on narrow ones. */
export default function TopicNav({ groups }: { groups: TopicNavGroup[] }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <aside className="sticky top-6 hidden max-h-[calc(100vh-3rem)] w-60 shrink-0 overflow-y-auto pr-2 pb-6 lg:block">
        <TopicList groups={groups} />
      </aside>
      <div className="lg:hidden">
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetTrigger className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-700 px-2.5 py-1.5 text-sm text-zinc-300 hover:bg-zinc-800/60">
            <ListTree className="size-4" /> All Topics
          </SheetTrigger>
          <SheetContent side="left" className="border-white/[.08] bg-card">
            <SheetHeader>
              <SheetTitle className="text-zinc-100">Topics</SheetTitle>
            </SheetHeader>
            <div className="min-h-0 flex-1 overflow-y-auto px-2 pb-6">
              <TopicList groups={groups} onNavigate={() => setOpen(false)} />
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </>
  );
}
