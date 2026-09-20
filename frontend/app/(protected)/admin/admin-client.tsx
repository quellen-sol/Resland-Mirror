"use client";

import { useEffect, useMemo, useState } from "react";
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
  balance_cents: number;
  cents_used: number;
  input_tokens: number;
  output_tokens: number;
  cents_purchased: number;
}

interface UsageByModel {
  model: string;
  job_count: number;
  input_tokens: number;
  output_tokens: number;
  cents: number;
}

interface UsageByKind {
  job_kind: string;
  job_count: number;
  cents: number;
}

interface UsageByDay {
  day: string;
  cents: number;
}

interface RecentUsage {
  id: number;
  user_id: string;
  job_kind: string;
  job_id: string;
  model: string;
  input_tokens: number;
  output_tokens: number;
  amount_cents: number;
  actual_cost_cents: number | null;
  created_at: string;
}

interface ModelPricing {
  id: string;
  display_name: string;
  cents_per_1k_input: number;
  cents_per_1k_output: number;
  enabled: boolean;
  sort_order: number;
}

interface AdminPurchase {
  id: string;
  user_id: string;
  cents: number;
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
const searchInput =
  "w-52 rounded border border-zinc-700 bg-zinc-800 px-2 py-1 text-xs";

const PAGE_SIZE = 10;

function matches(q: string, ...fields: (string | null | undefined)[]) {
  const needle = q.trim().toLowerCase();
  if (!needle) return true;
  return fields.some((f) => f?.toLowerCase().includes(needle));
}

function usePager<T>(rows: T[]) {
  const [page, setPage] = useState(0);
  const pages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
  const safePage = Math.min(page, pages - 1);
  return {
    page: safePage,
    setPage,
    pages,
    total: rows.length,
    slice: rows.slice(safePage * PAGE_SIZE, (safePage + 1) * PAGE_SIZE),
  };
}

function Pager({ pager }: { pager: ReturnType<typeof usePager> }) {
  if (pager.pages <= 1) return null;
  return (
    <div className="mt-3 flex items-center justify-between text-xs text-zinc-500">
      <span>
        Page {pager.page + 1} of {pager.pages} · {pager.total} rows
      </span>
      <div className="flex gap-2">
        <button
          className="rounded bg-zinc-700 px-2 py-1 hover:bg-zinc-600 disabled:opacity-40"
          disabled={pager.page === 0}
          onClick={() => pager.setPage(pager.page - 1)}
        >
          Prev
        </button>
        <button
          className="rounded bg-zinc-700 px-2 py-1 hover:bg-zinc-600 disabled:opacity-40"
          disabled={pager.page >= pager.pages - 1}
          onClick={() => pager.setPage(pager.page + 1)}
        >
          Next
        </button>
      </div>
    </div>
  );
}

function SearchBox({
  value,
  onChange,
  placeholder,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
}) {
  return (
    <input
      className={searchInput}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
    />
  );
}

export default function AdminClient({ accessToken }: { accessToken: string }) {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [byModel, setByModel] = useState<UsageByModel[]>([]);
  const [byKind, setByKind] = useState<UsageByKind[]>([]);
  const [byDay, setByDay] = useState<UsageByDay[]>([]);
  const [recent, setRecent] = useState<RecentUsage[]>([]);
  const [revenueCents, setRevenueCents] = useState(0);
  const [purchases, setPurchases] = useState<AdminPurchase[]>([]);
  const [models, setModels] = useState<ModelPricing[]>([]);
  const [savingModel, setSavingModel] = useState<string | null>(null);
  const [newModel, setNewModel] = useState({
    id: "openrouter:",
    display_name: "",
    cents_per_1k_input: "",
    cents_per_1k_output: "",
    sort_order: "",
  });
  const [usersQ, setUsersQ] = useState("");
  const [modelsQ, setModelsQ] = useState("");
  const [purchasesQ, setPurchasesQ] = useState("");
  const [recentQ, setRecentQ] = useState("");
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      apiFetch(accessToken, "/admin/users"),
      apiFetch(accessToken, "/admin/usage"),
      apiFetch(accessToken, "/admin/purchases"),
      apiFetch(accessToken, "/admin/models"),
    ])
      .then(([u, usage, p, m]) => {
        if (cancelled) return;
        setUsers((u as { users: AdminUser[] }).users);
        setModels((m as { models: ModelPricing[] }).models);
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

  const numInput =
    "w-24 rounded border border-zinc-700 bg-zinc-800 px-1.5 py-1 text-xs";

  function updateModel(id: string, patch: Partial<ModelPricing>) {
    setModels((ms) =>
      ms.map((m) => (m.id === id ? { ...m, ...patch } : m)),
    );
  }

  async function saveModel(m: ModelPricing) {
    setSavingModel(m.id);
    try {
      const saved = await apiFetch(
        accessToken,
        `/admin/models/${encodeURIComponent(m.id)}`,
        {
          method: "PUT",
          body: JSON.stringify({
            display_name: m.display_name,
            cents_per_1k_input: m.cents_per_1k_input,
            cents_per_1k_output: m.cents_per_1k_output,
            enabled: m.enabled,
            sort_order: m.sort_order,
          }),
        },
      );
      toast.success(`Saved ${(saved as ModelPricing).display_name}`);
      const res = await apiFetch(accessToken, "/admin/models");
      setModels((res as { models: ModelPricing[] }).models);
    } catch (e) {
      toast.error("Couldn't save model", {
        description: e instanceof Error ? e.message : String(e),
      });
    } finally {
      setSavingModel(null);
    }
  }

  async function deleteModel(id: string) {
    if (!window.confirm(`Delete ${id}? Users can no longer select it.`)) return;
    try {
      await apiFetch(
        accessToken,
        `/admin/models/${encodeURIComponent(id)}`,
        { method: "DELETE" },
      );
      setModels((ms) => ms.filter((m) => m.id !== id));
      toast.success(`Deleted ${id}`);
    } catch (e) {
      toast.error("Couldn't delete model", {
        description: e instanceof Error ? e.message : String(e),
      });
    }
  }

  const filteredUsers = useMemo(
    () =>
      users.filter((u) => matches(usersQ, u.auth0_id, u.email, u.full_name)),
    [users, usersQ],
  );
  const filteredModels = useMemo(
    () => models.filter((m) => matches(modelsQ, m.id, m.display_name)),
    [models, modelsQ],
  );
  const filteredPurchases = useMemo(
    () =>
      purchases.filter((p) =>
        matches(purchasesQ, p.id, p.user_id, p.status),
      ),
    [purchases, purchasesQ],
  );
  const filteredRecent = useMemo(
    () =>
      recent.filter((r) =>
        matches(recentQ, r.user_id, r.job_kind, r.job_id, r.model),
      ),
    [recent, recentQ],
  );
  const usersPager = usePager(filteredUsers);
  const modelsPager = usePager(filteredModels);
  const purchasesPager = usePager(filteredPurchases);
  const recentPager = usePager(filteredRecent);

  async function addModel() {
    const id = newModel.id.trim();
    if (!id || id === "openrouter:") {
      toast.error("Enter a model id", {
        description: 'e.g. "openrouter:openai/gpt-5-nano"',
      });
      return;
    }
    const row: ModelPricing = {
      id,
      display_name: newModel.display_name.trim() || id,
      cents_per_1k_input: parseFloat(newModel.cents_per_1k_input) || 0,
      cents_per_1k_output: parseFloat(newModel.cents_per_1k_output) || 0,
      enabled: true,
      sort_order: parseInt(newModel.sort_order) || 0,
    };
    await saveModel(row);
    setNewModel({
      id: "openrouter:",
      display_name: "",
      cents_per_1k_input: "",
      cents_per_1k_output: "",
      sort_order: "",
    });
  }

  return (
    <div className="flex flex-col gap-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="bg-gradient-to-r from-purple-300 to-violet-500 bg-clip-text text-3xl font-semibold text-transparent">
            Admin
          </h1>
          <p className="mt-1 text-sm text-zinc-400">
            Usage, purchases, and revenue across all users.
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
                ? fmtMoney(
                    users.reduce((acc, u) => acc + u.cents_used, 0),
                    "usd",
                  )
                : "—"}
            </p>
            <p className="text-xs text-zinc-500">balance consumed</p>
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
        <CardHeader className="flex-row items-center justify-between gap-2">
          <CardTitle className="text-lg">Per-user usage</CardTitle>
          <SearchBox
            value={usersQ}
            onChange={setUsersQ}
            placeholder="Search users…"
          />
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-zinc-800 text-xs">
                <th className={th}>User</th>
                <th className={th}>Balance</th>
                <th className={th}>Spent</th>
                <th className={th}>In / Out tokens</th>
                <th className={th}>Purchased</th>
              </tr>
            </thead>
            <tbody>
              {usersPager.slice.map((u) => (
                <tr key={u.auth0_id} className="border-b border-zinc-800/50">
                  <td className={td}>
                    {u.full_name ?? u.email ?? u.auth0_id}
                  </td>
                  <td className={td}>{fmtMoney(u.balance_cents, "usd")}</td>
                  <td className={td}>{fmtMoney(u.cents_used, "usd")}</td>
                  <td className={td}>
                    {u.input_tokens.toLocaleString()} /{" "}
                    {u.output_tokens.toLocaleString()}
                  </td>
                  <td className={td}>
                    {fmtMoney(u.cents_purchased, "usd")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pager pager={usersPager} />
        </CardContent>
      </Card>

      <Card className="border-zinc-800 bg-zinc-900/80 text-zinc-100">
        <CardHeader className="flex-row items-center justify-between gap-2">
          <CardTitle className="text-lg">Model pricing</CardTitle>
          <SearchBox
            value={modelsQ}
            onChange={setModelsQ}
            placeholder="Search models…"
          />
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-zinc-800 text-xs">
                <th className={th}>Id</th>
                <th className={th}>Name</th>
                <th className={th}>¢/1K in</th>
                <th className={th}>¢/1K out</th>
                <th className={th}>Sort</th>
                <th className={th}>Enabled</th>
                <th className={th}></th>
              </tr>
            </thead>
            <tbody>
              {modelsPager.slice.map((m) => (
                <tr key={m.id} className="border-b border-zinc-800/50">
                  <td className={td}>{m.id}</td>
                  <td className={td}>
                    <input
                      className="w-36 rounded border border-zinc-700 bg-zinc-800 px-1.5 py-1 text-xs"
                      value={m.display_name}
                      onChange={(e) =>
                        updateModel(m.id, { display_name: e.target.value })
                      }
                    />
                  </td>
                  <td className={td}>
                    <input
                      type="number"
                      step="0.001"
                      min="0"
                      className={numInput}
                      value={m.cents_per_1k_input}
                      onChange={(e) =>
                        updateModel(m.id, {
                          cents_per_1k_input:
                            parseFloat(e.target.value) || 0,
                        })
                      }
                    />
                  </td>
                  <td className={td}>
                    <input
                      type="number"
                      step="0.001"
                      min="0"
                      className={numInput}
                      value={m.cents_per_1k_output}
                      onChange={(e) =>
                        updateModel(m.id, {
                          cents_per_1k_output:
                            parseFloat(e.target.value) || 0,
                        })
                      }
                    />
                  </td>
                  <td className={td}>
                    <input
                      type="number"
                      className="w-16 rounded border border-zinc-700 bg-zinc-800 px-1.5 py-1 text-xs"
                      value={m.sort_order}
                      onChange={(e) =>
                        updateModel(m.id, {
                          sort_order: parseInt(e.target.value) || 0,
                        })
                      }
                    />
                  </td>
                  <td className={td}>
                    <input
                      type="checkbox"
                      className="size-4 cursor-pointer accent-purple-500"
                      checked={m.enabled}
                      onChange={(e) =>
                        updateModel(m.id, { enabled: e.target.checked })
                      }
                    />
                  </td>
                  <td className={td}>
                    <button
                      className="rounded bg-zinc-700 px-2.5 py-1 text-xs font-medium hover:bg-zinc-600 disabled:opacity-50"
                      disabled={savingModel === m.id}
                      onClick={() => saveModel(m)}
                    >
                      {savingModel === m.id ? "Saving…" : "Save"}
                    </button>
                    <button
                      className="ml-2 rounded bg-red-900/60 px-2.5 py-1 text-xs font-medium text-red-300 hover:bg-red-800/60"
                      onClick={() => deleteModel(m.id)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
              <tr className="border-b border-zinc-800/50">
                <td className={td}>
                  <input
                    className="w-56 rounded border border-zinc-700 bg-zinc-800 px-1.5 py-1 text-xs"
                    value={newModel.id}
                    onChange={(e) =>
                      setNewModel({ ...newModel, id: e.target.value })
                    }
                    placeholder="openrouter:vendor/model"
                  />
                </td>
                <td className={td}>
                  <input
                    className="w-36 rounded border border-zinc-700 bg-zinc-800 px-1.5 py-1 text-xs"
                    value={newModel.display_name}
                    onChange={(e) =>
                      setNewModel({
                        ...newModel,
                        display_name: e.target.value,
                      })
                    }
                    placeholder="Display name"
                  />
                </td>
                <td className={td}>
                  <input
                    type="number"
                    step="0.001"
                    min="0"
                    className={numInput}
                    value={newModel.cents_per_1k_input}
                    onChange={(e) =>
                      setNewModel({
                        ...newModel,
                        cents_per_1k_input: e.target.value,
                      })
                    }
                    placeholder="0.00"
                  />
                </td>
                <td className={td}>
                  <input
                    type="number"
                    step="0.001"
                    min="0"
                    className={numInput}
                    value={newModel.cents_per_1k_output}
                    onChange={(e) =>
                      setNewModel({
                        ...newModel,
                        cents_per_1k_output: e.target.value,
                      })
                    }
                    placeholder="0.00"
                  />
                </td>
                <td className={td}>
                  <input
                    type="number"
                    className="w-16 rounded border border-zinc-700 bg-zinc-800 px-1.5 py-1 text-xs"
                    value={newModel.sort_order}
                    onChange={(e) =>
                      setNewModel({
                        ...newModel,
                        sort_order: e.target.value,
                      })
                    }
                    placeholder="0"
                  />
                </td>
                <td className={td}></td>
                <td className={td}>
                  <button
                    className="rounded bg-purple-600/80 px-2.5 py-1 text-xs font-medium hover:bg-purple-500"
                    disabled={savingModel !== null}
                    onClick={addModel}
                  >
                    Add
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
          <p className="mt-2 text-xs text-zinc-500">
            Rates are the advertised fallback price — actual charges use
            OpenRouter&apos;s reported cost ×1.25. Disabled models are rejected
            at job creation.
          </p>
          <Pager pager={modelsPager} />
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
                  <th className={th}>Charged</th>
                </tr>
              </thead>
              <tbody>
                {byModel.map((m) => (
                  <tr key={m.model} className="border-b border-zinc-800/50">
                    <td className={td}>{m.model}</td>
                    <td className={td}>{m.job_count}</td>
                    <td className={td}>{fmtMoney(m.cents, "usd")}</td>
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
                  <th className={th}>Charged</th>
                </tr>
              </thead>
              <tbody>
                {byKind.map((k) => (
                  <tr key={k.job_kind} className="border-b border-zinc-800/50">
                    <td className={td}>{k.job_kind}</td>
                    <td className={td}>{k.job_count}</td>
                    <td className={td}>{fmtMoney(k.cents, "usd")}</td>
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
                  <th className={th}>Charged</th>
                </tr>
              </thead>
              <tbody>
                {byDay.map((d) => (
                  <tr key={d.day} className="border-b border-zinc-800/50">
                    <td className={td}>{d.day}</td>
                    <td className={td}>{fmtMoney(d.cents, "usd")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      </div>

      <Card className="border-zinc-800 bg-zinc-900/80 text-zinc-100">
        <CardHeader className="flex-row items-center justify-between gap-2">
          <CardTitle className="text-lg">Purchases</CardTitle>
          <SearchBox
            value={purchasesQ}
            onChange={setPurchasesQ}
            placeholder="Search purchases…"
          />
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-zinc-800 text-xs">
                <th className={th}>Date</th>
                <th className={th}>User</th>
                <th className={th}>Granted</th>
                <th className={th}>Amount</th>
                <th className={th}>Status</th>
              </tr>
            </thead>
            <tbody>
              {purchasesPager.slice.map((p) => (
                <tr key={p.id} className="border-b border-zinc-800/50">
                  <td className={td}>{fmtDate(p.created_at)}</td>
                  <td className={td}>{p.user_id}</td>
                  <td className={td}>{fmtMoney(p.cents, p.currency)}</td>
                  <td className={td}>{fmtMoney(p.amount_cents, p.currency)}</td>
                  <td className={td}>{p.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pager pager={purchasesPager} />
        </CardContent>
      </Card>

      <Card className="border-zinc-800 bg-zinc-900/80 text-zinc-100">
        <CardHeader className="flex-row items-center justify-between gap-2">
          <CardTitle className="text-lg">Recent usage events</CardTitle>
          <SearchBox
            value={recentQ}
            onChange={setRecentQ}
            placeholder="Search events…"
          />
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
                <th className={th}>Charged</th>
                <th className={th}>Actual cost</th>
              </tr>
            </thead>
            <tbody>
              {recentPager.slice.map((r) => (
                <tr key={r.id} className="border-b border-zinc-800/50">
                  <td className={td}>{fmtDate(r.created_at)}</td>
                  <td className={td}>{r.user_id}</td>
                  <td className={td}>{r.job_kind}</td>
                  <td className={td}>{r.model}</td>
                  <td className={td}>
                    {r.input_tokens.toLocaleString()} /{" "}
                    {r.output_tokens.toLocaleString()}
                  </td>
                  <td className={td}>{fmtMoney(r.amount_cents, "usd")}</td>
                  <td className={td}>
                    {r.actual_cost_cents == null
                      ? "—"
                      : fmtMoney(r.actual_cost_cents, "usd")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pager pager={recentPager} />
        </CardContent>
      </Card>
    </div>
  );
}
