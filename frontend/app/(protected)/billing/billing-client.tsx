"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Loader2, Zap } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch, describeApiError, fmtCents } from "@/lib/api";
import ApiUnavailable from "@/components/api-unavailable";
import HelpTip from "@/components/help-tip";

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

// balance_purchase.status values — show words, not raw enum names.
const PURCHASE_STATUS_LABELS: Record<string, string> = {
  PENDING: "Pending",
  COMPLETED: "Completed",
  EXPIRED: "Expired",
  REFUNDED: "Refunded",
};

function fmtStatus(status: string) {
  return (
    PURCHASE_STATUS_LABELS[status] ??
    status.charAt(0).toUpperCase() + status.slice(1).toLowerCase()
  );
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
  paymentsPaused: initialPaymentsPaused,
}: {
  accessToken: string;
  checkoutResult: string | null;
  paymentsPaused: boolean;
}) {
  const [balance, setBalance] = useState<number | null>(null);
  const [packs, setPacks] = useState<TokenPack[]>([]);
  const [purchases, setPurchases] = useState<Purchase[]>([]);
  const [busyPack, setBusyPack] = useState<string | null>(null);
  const [paused, setPaused] = useState(initialPaymentsPaused);
  const [error, setError] = useState<string | null>(null);

  function loadBilling() {
    return Promise.all([
      apiFetch(accessToken, "/billing/balance"),
      apiFetch(accessToken, "/billing/packs"),
      apiFetch(accessToken, "/billing/purchases"),
    ])
      .then(([bal, pk, pu]) => {
        setBalance((bal as { balance_cents: number }).balance_cents);
        setPacks(pk as TokenPack[]);
        setPurchases((pu as { purchases: Purchase[] }).purchases);
      })
      .catch((e) => {
        const message = describeApiError(e);
        setError(message);
        toast.error("Couldn't load billing info", { description: message });
      });
  }

  useEffect(() => {
    if (checkoutResult === "success") {
      toast.success("Balance topped up");
      // The Stripe webhook lands a moment after the redirect — poll so the
      // new balance and purchase row show up without a manual refresh.
      const interval = setInterval(() => void loadBilling(), 2000);
      const stop = setTimeout(() => clearInterval(interval), 12000);
      return () => {
        clearInterval(interval);
        clearTimeout(stop);
      };
    } else if (checkoutResult === "cancelled") {
      toast.info("Checkout cancelled");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [checkoutResult]);

  useEffect(() => {
    void loadBilling();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken]);

  // The page snapshot can go stale while open — re-read the flag on focus
  // and on a poll so resumed payments unlock Buy without a reload.
  useEffect(() => {
    let cancelled = false;
    async function refresh() {
      try {
        const res = await fetch("/api/site-settings");
        if (!res.ok) return;
        const body = (await res.json()) as { payments_paused?: boolean };
        if (!cancelled && typeof body.payments_paused === "boolean")
          setPaused(body.payments_paused);
      } catch {
        // Keep the last known state.
      }
    }
    const interval = setInterval(() => void refresh(), 60_000);
    const onVisible = () => {
      if (document.visibilityState === "visible") void refresh();
    };
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      cancelled = true;
      clearInterval(interval);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, []);

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
        description: describeApiError(e),
      });
      setBusyPack(null);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <header className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-semibold tracking-[-0.03em]">
              Billing
            </h1>
            <HelpTip title="How Billing Works">
              <p>
                There&apos;s no subscription. Buy a pack below to add balance,
                and each suggestion or tailoring run takes a little from it.
              </p>
              <p>
                Each request is charged for what it actually uses: the AI
                provider&apos;s cost for that work, plus a service fee. More
                capable models cost more, and any prices shown next to a model
                are estimates.
              </p>
              <p>
                Bigger packs include bonus balance. Nothing gets cut off
                halfway: if a run costs more than you have left, it still
                finishes and your balance stops at zero. You just need a balance
                above zero to start something new.
              </p>
              <p>
                Checkout is handled securely by Stripe, and every purchase
                shows up in your history below.
              </p>
            </HelpTip>
          </div>
          <p className="mt-1 text-sm text-zinc-400">
            Your balance pays for suggestions and tailoring. Top up when it runs low.
          </p>
        </div>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1.5 text-sm text-zinc-500 underline-offset-4 hover:text-zinc-300 hover:underline"
        >
          <ArrowLeft className="size-3.5" /> Dashboard
        </Link>
      </header>
      {error && (
        <ApiUnavailable
          onRetry={() => {
            setError(null);
            void loadBilling();
          }}
          message={error}
        />
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Zap className="size-4 text-brand-400" /> Balance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-semibold">
            {balance === null ? "—" : fmtCents(balance)}
          </p>
          <p className="mt-1 text-xs text-zinc-500">
            Available for suggestions and tailoring
          </p>
        </CardContent>
      </Card>

      {paused && (
        <Card className="bg-amber-950/40 text-amber-200 ring-amber-800/60">
          <CardContent className="pt-6 text-sm">
            Purchases are paused for now. Your balance and history aren&apos;t
            affected, so check back soon.
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 sm:grid-cols-3">
        {packs.map((pack) => (
          <Card
            key={pack.id}
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
                disabled={busyPack !== null || paused}
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

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Purchase History</CardTitle>
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
                    <td className="py-2 text-zinc-300">
                      {fmtDate(p.created_at)}
                    </td>
                    <td className="py-2 text-zinc-300">
                      {fmtMoney(p.cents, p.currency)}
                    </td>
                    <td className="py-2 text-zinc-300">
                      {fmtMoney(p.amount_cents, p.currency)}
                    </td>
                    <td className="py-2 text-zinc-400">{fmtStatus(p.status)}</td>
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
