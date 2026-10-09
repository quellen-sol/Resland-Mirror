import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { requireOnboardedUser } from "@/lib/db";
import HelpTip from "@/components/help-tip";
import Backdrop from "@/components/backdrop";
import { db } from "@/prisma/db";
import MemoryBank from "./memory-bank";

export const metadata: Metadata = { title: "Memory" };

export default async function MemoryPage() {
  const user = await requireOnboardedUser();

  const [facts, experiences] = await Promise.all([
    db.orm.public.UserMemoryFact.where((f) => f.user_id.eq(user.auth0_id))
      .orderBy((f) => f.id.asc())
      .all(),
    db.orm.public.UserBaseExperience.where((e) =>
      e.user_id.eq(user.auth0_id),
    ).all(),
  ]);

  return (
    <div className="relative flex flex-1 justify-center overflow-clip bg-zinc-950 px-6 py-10 font-sans">
      <Backdrop />

      <main className="relative flex w-full max-w-3xl flex-col gap-6">
        <header className="flex items-center justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h1 className="text-3xl font-semibold tracking-[-0.03em]">
                Memory
              </h1>
              <HelpTip title="Memory">
                <p>
                  When you answer questions while tailoring or improving
                  bullets, Resland saves the lasting facts here, like the
                  scale of a system you built or whether you want a summary.
                  Later runs use them instead of asking you again, and pick
                  the ones that fit each job.
                </p>
                <p>
                  Fix anything that&apos;s wrong or out of date, and delete
                  anything you don&apos;t want used.
                </p>
              </HelpTip>
            </div>
            <p className="mt-1 text-sm text-zinc-400">
              Facts about your work that tailoring and suggestions use instead
              of asking you again.
            </p>
          </div>
          <Link
            href="/dashboard"
            className="inline-flex shrink-0 items-center gap-1.5 text-sm text-zinc-500 underline-offset-4 hover:text-zinc-300 hover:underline"
          >
            <ArrowLeft className="size-3.5" /> Dashboard
          </Link>
        </header>

        <MemoryBank
          initial={facts.map((f) => ({
            id: f.id,
            topic: f.topic,
            content: f.content,
            source: f.source,
          }))}
          // The topic the agents file a job's facts under.
          jobTopics={experiences.map((e) => `${e.title} at ${e.company_name}`)}
        />
      </main>
    </div>
  );
}
