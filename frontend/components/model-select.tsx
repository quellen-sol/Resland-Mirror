"use client";

import { useEffect, useState } from "react";
import { apiFetch, type PricedModel } from "@/lib/api";
import { cn } from "cn";

export default function ModelSelect({
  accessToken,
  value,
  onChange,
  disabled,
  className,
}: {
  accessToken: string;
  /** Selected model id, or "" for the system default. */
  value: string;
  onChange: (modelId: string) => void;
  disabled?: boolean;
  className?: string;
}) {
  const [models, setModels] = useState<PricedModel[]>([]);
  const defaultModel = models.find((m) => m.is_default);

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
  );
}
