"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Loader2, Zap } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { apiFetch, fmtCents } from "@/lib/api";

interface TokenPack {
  id: string;
  name: string;
  cents: number;
  amount_cents: number;
  currency: string;
}

interface Purchase {
  id: string;
  cents: number;
  amount_cents: number;
  currency: string;
  status: string;
  created_at: string;
}

function fmtMoney(cents: number, currency: string) {
  return (cents / 100).toLocaleString("en-US", {
    style: "currency",
    currency: currency.toUpperCase(),
  });
}

function fmtDate(iso: string) {
  const d = new Date(iso);
  return Number.isNaN(d.getTime())
    ? iso
    : d.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
}

export default function BillingClient({
  accessToken,
  checkoutResult,
}: {
  accessToken: string;
  checkoutResult: string | null;
}) {
  const [balance, setBalance] = useState<number | null>(null);
  const [packs, setPacks] = useState<TokenPack[]>([]);
  const [purchases, setPurchases] = useState<Purchase[]>([]);
  const [busyPack, setBusyPack] = useState<string | null>(null);

  useEffect(() => {
    if (checkoutResult === "success") {
      toast.success("Purchase complete — balance topped up");
    } else if (checkoutResult === "cancelled") {
      toast.info("Checkout cancelled");
    }
  }, [checkoutResult]);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      apiFetch(accessToken, "/billing/balance"),
      apiFetch(accessToken, "/billing/packs"),
      apiFetch(accessToken, "/billing/purchases"),
    ])
      .then(([bal, pk, pu]) => {
        if (cancelled) return;
        setBalance((bal as { balance_cents: number }).balance_cents);
        setPacks(pk as TokenPack[]);
        setPurchases((pu as { purchases: Purchase[] }).purchases);
      })
      .catch((e) => {
        toast.error("Couldn't load billing info", {
          description: e instanceof Error ? e.message : String(e),
        });
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  async function buy(packId: string) {
    setBusyPack(packId);
    try {
      const { url } = (await apiFetch(accessToken, "/billing/checkout", {
        method: "POST",
        body: JSON.stringify({ pack_id: packId }),
      })) as { url: string };
      window.location.assign(url);
    } catch (e) {
      toast.error("Couldn't start checkout", {
        description: e instanceof Error ? e.message : String(e),
      });
      setBusyPack(null);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="bg-gradient-to-r from-purple-300 to-violet-500 bg-clip-text text-3xl font-semibold text-transparent">
            Billing
          </h1>
          <p className="mt-1 text-sm text-zinc-400">
            Balance powers suggestions and tailoring — top up when you run low.
          </p>
        </div>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1.5 text-sm text-zinc-500 underline-offset-4 hover:text-zinc-300 hover:underline"
        >
          <ArrowLeft className="size-3.5" /> Dashboard
        </Link>
      </header>

      <Card className="border-zinc-800 bg-zinc-900/80 text-zinc-100">
        <CardContent className="flex items-center gap-3 pt-6">
          <Zap className="size-5 text-purple-400" />
          <div>
            <p className="text-2xl font-semibold">
              {balance === null ? "—" : fmtCents(balance)}
            </p>
            <p className="text-xs text-zinc-500">balance</p>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 sm:grid-cols-3">
        {packs.map((pack) => (
          <Card
            key={pack.id}
            className="border-zinc-800 bg-zinc-900/80 text-zinc-100"
          >
            <CardHeader>
              <CardTitle className="text-lg">{pack.name}</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              <p className="text-2xl font-semibold">
                {fmtMoney(pack.amount_cents, pack.currency)}
              </p>
              <p className="text-xs text-zinc-500">
                +{fmtCents(pack.cents)} balance
              </p>
              <Button
                onClick={() => buy(pack.id)}
                disabled={busyPack !== null}
                className="border-0 bg-gradient-to-r from-violet-600 to-purple-600 text-white hover:from-violet-500 hover:to-purple-500"
              >
                {busyPack === pack.id ? (
                  <Loader2 className="animate-spin" />
                ) : (
                  "Buy"
                )}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="border-zinc-800 bg-zinc-900/80 text-zinc-100">
        <CardHeader>
          <CardTitle className="text-lg">Purchase history</CardTitle>
        </CardHeader>
        <CardContent>
          {purchases.length === 0 ? (
            <p className="text-sm text-zinc-500">No purchases yet.</p>
          ) : (
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-zinc-800 text-xs text-zinc-500">
                  <th className="py-2 font-medium">Date</th>
                  <th className="py-2 font-medium">Added</th>
                  <th className="py-2 font-medium">Amount</th>
                  <th className="py-2 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {purchases.map((p) => (
                  <tr key={p.id} className="border-b border-zinc-800/50">
                    <td className="py-2 text-zinc-300">{fmtDate(p.created_at)}</td>
                    <td className="py-2 text-zinc-300">
                      {fmtMoney(p.cents, p.currency)}
                    </td>
                    <td className="py-2 text-zinc-300">
                      {fmtMoney(p.amount_cents, p.currency)}
                    </td>
                    <td className="py-2 text-zinc-400">{p.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
