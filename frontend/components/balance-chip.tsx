"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Zap } from "lucide-react";
import { apiFetch, fmtCents } from "@/lib/api";
import { cn } from "cn";

export default function BalanceChip({ accessToken }: { accessToken: string }) {
  const [balance, setBalance] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiFetch(accessToken, "/billing/balance")
      .then((data: { balance_cents: number }) => {
        if (!cancelled) setBalance(data.balance_cents);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  if (balance === null) return null;

  return (
    <Link
      href="/billing"
      title="Top Up Balance"
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-xs",
        balance > 0
          ? "border-zinc-700 text-zinc-300 hover:bg-zinc-800"
          : "border-amber-500/40 bg-amber-500/10 text-amber-300 hover:bg-amber-500/20",
      )}
    >
      <Zap className="size-3.5 text-brand-400" />
      {fmtCents(balance)}
    </Link>
  );
}
