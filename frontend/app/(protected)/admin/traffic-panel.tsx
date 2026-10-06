"use client";

import { useEffect, useState } from "react";
import { cn } from "cn";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TRAFFIC_RANGES, type TrafficRange, type TrafficSummary } from "@/lib/traffic";

const th = "py-2 pr-4 font-medium text-zinc-500";
const td = "py-2 pr-4 text-zinc-300";
const ROWS = 15;

const SOURCE_LABELS: Record<string, string> = {
  SEARCH: "Search",
  AI: "AI assistant",
  SOCIAL: "Social",
  REFERRAL: "Referral",
  DIRECT: "Direct",
  INTERNAL: "Internal",
};

function pct(part: number, whole: number) {
  return whole ? `${Math.round((part / whole) * 100)}%` : "—";
}

function Table({
  head,
  rows,
  empty = "No visits yet.",
  limit = ROWS,
}: {
  head: string[];
  rows: (string | number)[][];
  empty?: string;
  limit?: number;
}) {
  if (rows.length === 0) return <p className="text-sm text-zinc-500">{empty}</p>;
  return (
    <table className="w-full text-left text-sm">
      <thead>
        <tr className="border-b border-zinc-800 text-xs">
          {head.map((h) => (
            <th key={h} className={th}>
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.slice(0, limit).map((row, i) => (
          <tr key={i} className="border-b border-zinc-800/50">
            {row.map((cell, j) => (
              <td key={j} className={cn(td, j === 0 && "font-mono text-xs break-all")}>
                {cell}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/** First-party traffic from page_view: where visits come from, where they
 *  land, and where they go next. */
export default function TrafficPanel() {
  const [days, setDays] = useState<TrafficRange>(7);
  const [data, setData] = useState<TrafficSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch(`/api/admin/traffic?days=${days}`)
      .then((r) => {
        if (!r.ok) throw new Error(`traffic ${r.status}`);
        return r.json() as Promise<TrafficSummary>;
      })
      .then((summary) => {
        if (cancelled) return;
        setData(summary);
        setError(null);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      });
    return () => {
      cancelled = true;
    };
  }, [days]);

  const stats: [string, string][] = data
    ? [
        ["Visits", data.visits.toLocaleString()],
        ["Page views", data.views.toLocaleString()],
        ["From search", `${data.searchVisits} · ${pct(data.searchVisits, data.visits)}`],
        ["From AI assistants", `${data.aiVisits} · ${pct(data.aiVisits, data.visits)}`],
        ["Reached onboarding", `${data.onboardingVisits} · ${pct(data.onboardingVisits, data.visits)}`],
      ]
    : [];

  return (
    <section aria-labelledby="traffic-heading" className="flex flex-col gap-4">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 id="traffic-heading" className="text-2xl font-semibold tracking-[-0.02em]">
            Traffic
          </h2>
          <p className="mt-1 text-sm text-zinc-400">
            Visits by first page, from Resland&apos;s own page-view log. Bots and site admins
            aren&apos;t counted. Search queries live in Google Search Console.
          </p>
        </div>
        <div role="group" aria-label="Range" className="flex gap-1 rounded-lg border border-zinc-800 p-1">
          {TRAFFIC_RANGES.map((r) => (
            <button
              key={r}
              type="button"
              aria-pressed={days === r}
              onClick={() => setDays(r)}
              className={cn(
                "rounded-md px-2.5 py-1 text-sm",
                days === r ? "bg-zinc-800 text-zinc-100" : "text-zinc-400 hover:text-zinc-200",
              )}
            >
              {r === 1 ? "Today" : `${r} days`}
            </button>
          ))}
        </div>
      </header>

      {error && <p className="text-sm text-red-400">Couldn&apos;t load traffic ({error}).</p>}

      <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-5">
        {(stats.length ? stats : [["Visits", "—"]]).map(([label, value]) => (
          <Card key={label}>
            <CardContent className="pt-6">
              <p className="text-2xl font-semibold">{value}</p>
              <p className="text-xs text-zinc-500">{label}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {data && (
        <>
          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Sources</CardTitle>
              </CardHeader>
              <CardContent>
                <Table
                  head={["Source", "Type", "Visits"]}
                  rows={data.sources.map((s) => [
                    s.name ?? SOURCE_LABELS[s.source],
                    SOURCE_LABELS[s.source],
                    s.visits,
                  ])}
                />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Landing Pages</CardTitle>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <Table
                  head={["Page", "Visits", "From search", "Onboarded"]}
                  rows={data.landingPages.map((l) => [l.path, l.visits, l.search, l.onboarding])}
                />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Pages</CardTitle>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <Table
                  head={["Page", "Views", "Visits"]}
                  rows={data.pages.map((p) => [p.path, p.views, p.visits])}
                />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Navigation</CardTitle>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <Table
                  head={["From → To", "Times"]}
                  rows={data.navigation.map((n) => [`${n.from} → ${n.to}`, n.count])}
                  empty="No page-to-page moves yet."
                />
              </CardContent>
            </Card>
          </div>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">By Day (UTC)</CardTitle>
            </CardHeader>
            <CardContent className="overflow-x-auto">
              <Table
                head={["Day", "Visits", "Page views", "From search"]}
                rows={[...data.daily].reverse().map((d) => [d.day, d.visits, d.views, d.searchVisits])}
                limit={data.daily.length}
              />
            </CardContent>
          </Card>
        </>
      )}
    </section>
  );
}
