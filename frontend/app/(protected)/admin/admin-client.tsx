"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { toast } from "sonner";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { apiFetch } from "@/lib/api";

interface AdminUser {
  auth0_id: string;
  email: string | null;
  full_name: string | null;
  token_balance: number;
  credits_used: number;
  input_tokens: number;
  output_tokens: number;
  credits_purchased: number;
}

interface UsageByModel {
  model: string;
  job_count: number;
  input_tokens: number;
  output_tokens: number;
  credits: number;
}

interface UsageByKind {
  job_kind: string;
  job_count: number;
  credits: number;
}

interface UsageByDay {
  day: string;
  credits: number;
}

interface RecentUsage {
  id: number;
  user_id: string;
  job_kind: string;
  job_id: string;
  model: string;
  input_tokens: number;
  output_tokens: number;
  credits_charged: number;
  created_at: string;
}

interface AdminPurchase {
  id: string;
  user_id: string;
  credits: number;
  amount_cents: number;
  currency: string;
  status: string;
  created_at: string;
}

function fmtDate(iso: string) {
  const d = new Date(iso);
  return Number.isNaN(d.getTime())
    ? iso
    : d.toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
      });
}

function fmtMoney(cents: number, currency: string) {
  return (cents / 100).toLocaleString("en-US", {
    style: "currency",
    currency: currency.toUpperCase(),
  });
}

const th = "py-2 pr-4 font-medium text-zinc-500";
const td = "py-2 pr-4 text-zinc-300";

export default function AdminClient({ accessToken }: { accessToken: string }) {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [byModel, setByModel] = useState<UsageByModel[]>([]);
  const [byKind, setByKind] = useState<UsageByKind[]>([]);
  const [byDay, setByDay] = useState<UsageByDay[]>([]);
  const [recent, setRecent] = useState<RecentUsage[]>([]);
  const [revenueCents, setRevenueCents] = useState(0);
  const [purchases, setPurchases] = useState<AdminPurchase[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      apiFetch(accessToken, "/admin/users"),
      apiFetch(accessToken, "/admin/usage"),
      apiFetch(accessToken, "/admin/purchases"),
    ])
      .then(([u, usage, p]) => {
        if (cancelled) return;
        setUsers((u as { users: AdminUser[] }).users);
        const us = usage as {
          by_model: UsageByModel[];
          by_kind: UsageByKind[];
          by_day: UsageByDay[];
          recent: RecentUsage[];
        };
        setByModel(us.by_model);
        setByKind(us.by_kind);
        setByDay(us.by_day);
        setRecent(us.recent);
        const pr = p as { revenue_cents: number; purchases: AdminPurchase[] };
        setRevenueCents(pr.revenue_cents);
        setPurchases(pr.purchases);
        setLoaded(true);
      })
      .catch((e) => {
        toast.error("Couldn't load admin stats", {
          description: e instanceof Error ? e.message : String(e),
        });
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  return (
    <div className="flex flex-col gap-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="bg-gradient-to-r from-purple-300 to-violet-500 bg-clip-text text-3xl font-semibold text-transparent">
            Admin
          </h1>
          <p className="mt-1 text-sm text-zinc-400">
            Token usage, purchases, and revenue across all users.
          </p>
        </div>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1.5 text-sm text-zinc-500 underline-offset-4 hover:text-zinc-300 hover:underline"
        >
          <ArrowLeft className="size-3.5" /> Dashboard
        </Link>
      </header>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="border-zinc-800 bg-zinc-900/80 text-zinc-100">
          <CardContent className="pt-6">
            <p className="text-2xl font-semibold">
              {loaded ? users.length : "—"}
            </p>
            <p className="text-xs text-zinc-500">users</p>
          </CardContent>
        </Card>
        <Card className="border-zinc-800 bg-zinc-900/80 text-zinc-100">
          <CardContent className="pt-6">
            <p className="text-2xl font-semibold">
              {loaded
                ? users
                    .reduce((acc, u) => acc + u.credits_used, 0)
                    .toLocaleString()
                : "—"}
            </p>
            <p className="text-xs text-zinc-500">credits consumed</p>
          </CardContent>
        </Card>
        <Card className="border-zinc-800 bg-zinc-900/80 text-zinc-100">
          <CardContent className="pt-6">
            <p className="text-2xl font-semibold">
              {loaded ? fmtMoney(revenueCents, "usd") : "—"}
            </p>
            <p className="text-xs text-zinc-500">revenue</p>
          </CardContent>
        </Card>
      </div>

      <Card className="border-zinc-800 bg-zinc-900/80 text-zinc-100">
        <CardHeader>
          <CardTitle className="text-lg">Per-user usage</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-zinc-800 text-xs">
                <th className={th}>User</th>
                <th className={th}>Balance</th>
                <th className={th}>Used</th>
                <th className={th}>In / Out tokens</th>
                <th className={th}>Purchased</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.auth0_id} className="border-b border-zinc-800/50">
                  <td className={td}>
                    {u.full_name ?? u.email ?? u.auth0_id}
                  </td>
                  <td className={td}>{u.token_balance.toLocaleString()}</td>
                  <td className={td}>{u.credits_used.toLocaleString()}</td>
                  <td className={td}>
                    {u.input_tokens.toLocaleString()} /{" "}
                    {u.output_tokens.toLocaleString()}
                  </td>
                  <td className={td}>
                    {u.credits_purchased.toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="border-zinc-800 bg-zinc-900/80 text-zinc-100">
          <CardHeader>
            <CardTitle className="text-lg">By model</CardTitle>
          </CardHeader>
          <CardContent>
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-zinc-800 text-xs">
                  <th className={th}>Model</th>
                  <th className={th}>Jobs</th>
                  <th className={th}>Credits</th>
                </tr>
              </thead>
              <tbody>
                {byModel.map((m) => (
                  <tr key={m.model} className="border-b border-zinc-800/50">
                    <td className={td}>{m.model}</td>
                    <td className={td}>{m.job_count}</td>
                    <td className={td}>{m.credits.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>

        <Card className="border-zinc-800 bg-zinc-900/80 text-zinc-100">
          <CardHeader>
            <CardTitle className="text-lg">By feature</CardTitle>
          </CardHeader>
          <CardContent>
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-zinc-800 text-xs">
                  <th className={th}>Kind</th>
                  <th className={th}>Jobs</th>
                  <th className={th}>Credits</th>
                </tr>
              </thead>
              <tbody>
                {byKind.map((k) => (
                  <tr key={k.job_kind} className="border-b border-zinc-800/50">
                    <td className={td}>{k.job_kind}</td>
                    <td className={td}>{k.job_count}</td>
                    <td className={td}>{k.credits.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>

        <Card className="border-zinc-800 bg-zinc-900/80 text-zinc-100">
          <CardHeader>
            <CardTitle className="text-lg">Last 30 days</CardTitle>
          </CardHeader>
          <CardContent>
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-zinc-800 text-xs">
                  <th className={th}>Day</th>
                  <th className={th}>Credits</th>
                </tr>
              </thead>
              <tbody>
                {byDay.map((d) => (
                  <tr key={d.day} className="border-b border-zinc-800/50">
                    <td className={td}>{d.day}</td>
                    <td className={td}>{d.credits.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      </div>

      <Card className="border-zinc-800 bg-zinc-900/80 text-zinc-100">
        <CardHeader>
          <CardTitle className="text-lg">Purchases</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-zinc-800 text-xs">
                <th className={th}>Date</th>
                <th className={th}>User</th>
                <th className={th}>Tokens</th>
                <th className={th}>Amount</th>
                <th className={th}>Status</th>
              </tr>
            </thead>
            <tbody>
              {purchases.map((p) => (
                <tr key={p.id} className="border-b border-zinc-800/50">
                  <td className={td}>{fmtDate(p.created_at)}</td>
                  <td className={td}>{p.user_id}</td>
                  <td className={td}>{p.credits.toLocaleString()}</td>
                  <td className={td}>{fmtMoney(p.amount_cents, p.currency)}</td>
                  <td className={td}>{p.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <Card className="border-zinc-800 bg-zinc-900/80 text-zinc-100">
        <CardHeader>
          <CardTitle className="text-lg">Recent usage events</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-zinc-800 text-xs">
                <th className={th}>Date</th>
                <th className={th}>User</th>
                <th className={th}>Kind</th>
                <th className={th}>Model</th>
                <th className={th}>In / Out</th>
                <th className={th}>Credits</th>
              </tr>
            </thead>
            <tbody>
              {recent.map((r) => (
                <tr key={r.id} className="border-b border-zinc-800/50">
                  <td className={td}>{fmtDate(r.created_at)}</td>
                  <td className={td}>{r.user_id}</td>
                  <td className={td}>{r.job_kind}</td>
                  <td className={td}>{r.model}</td>
                  <td className={td}>
                    {r.input_tokens.toLocaleString()} /{" "}
                    {r.output_tokens.toLocaleString()}
                  </td>
                  <td className={td}>{r.credits_charged.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
