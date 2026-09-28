"use client";

import { useEffect, useState } from "react";
import { apiFetch, fmtCents, type PricedModel } from "@/lib/api";
import { cn } from "cn";

function fmtAvg(cents: number) {
  // Sub-cent averages render in cents — "$0.00" would read as free.
  return cents < 1 ? `${Number(cents.toFixed(3))}¢` : fmtCents(cents);
}

export default function ModelSelect({
  accessToken,
  value,
  onChange,
  disabled,
  className,
  jobKind,
}: {
  accessToken: string;
  /** Selected model id, or "" for the system default. */
  value: string;
  onChange: (modelId: string) => void;
  disabled?: boolean;
  className?: string;
  /** When set, shows what that action has historically averaged in cost
   *  for the effective model, under the picker. */
  jobKind?: "SUGGESTION" | "TAILOR";
}) {
  const [models, setModels] = useState<PricedModel[]>([]);
  const defaultModel = models.find((m) => m.is_default);
  const effective = models.find((m) => m.id === value) ?? defaultModel;
  const estimate = jobKind
    ? effective?.action_costs.find((c) => c.job_kind === jobKind)
    : undefined;

  useEffect(() => {
    let cancelled = false;
    apiFetch(accessToken, "/models")
      .then((data: { models: PricedModel[] }) => {
        if (!cancelled) setModels(data.models);
      })
      .catch(() => {
        // Picker degrades to just the system default.
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  return (
    <span className="inline-flex flex-col gap-0.5">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className={cn(
          "rounded-md border border-zinc-700 bg-zinc-950/50 px-2 py-1.5 text-xs text-zinc-300 focus:border-purple-500 focus:outline-none disabled:opacity-50",
          className,
        )}
      >
        <option value="">
          Default{defaultModel ? ` (${defaultModel.display_name})` : ""}
        </option>
        {models.map((m) => (
          <option key={m.id} value={m.id}>
            {m.display_name} — {m.cents_per_1k_input}/{m.cents_per_1k_output}¢
            per 1K tok
          </option>
        ))}
      </select>
      {estimate && (
        <span
          className="px-0.5 text-[10px] text-zinc-500"
          title={`Average charged across ${estimate.job_count} past ${
            estimate.job_count === 1 ? "run" : "runs"
          }`}
        >
          ~{fmtAvg(estimate.avg_cents)} avg per run
        </span>
      )}
    </span>
  );
}
