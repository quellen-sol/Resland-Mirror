"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  Briefcase,
  Download,
  Loader2,
  PenLine,
  Trash2,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { apiFetch, describeApiError } from "@/lib/api";
import { cn } from "cn";
import type { ExportTailoredResponse } from "@/lib/tailored";

export interface TailoredItem {
  id: string;
  company_name: string | null;
  role: string | null;
  created_at: string;
  generated_at: string | null;
}

type SortKey = "role" | "company" | "saved" | "exported";
type SortDir = "asc" | "desc";

const th = "py-2 pr-4 font-medium text-zinc-500";
const td = "py-2 pr-4 text-zinc-300";

function fmtDate(iso: string | null) {
  if (!iso) return "—";
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) return iso;
  return parsed.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function sortValue(item: TailoredItem, key: SortKey): string | null {
  switch (key) {
    case "role":
      return item.role?.toLowerCase() || null;
    case "company":
      return item.company_name?.toLowerCase() || null;
    case "saved":
      return item.created_at;
    case "exported":
      return item.generated_at;
  }
}

export default function TailoredBoard({
  accessToken,
  items,
}: {
  accessToken: string;
  items: TailoredItem[];
}) {
  const router = useRouter();
  const [busyId, setBusyId] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<TailoredItem | null>(null);
  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("saved");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    const filtered = q
      ? items.filter((i) =>
          `${i.role ?? ""} ${i.company_name ?? ""}`.toLowerCase().includes(q),
        )
      : items;
    const dir = sortDir === "asc" ? 1 : -1;
    return [...filtered].sort((a, b) => {
      const av = sortValue(a, sortKey);
      const bv = sortValue(b, sortKey);
      if (av === bv) return 0;
      if (av === null) return 1;
      if (bv === null) return -1;
      return av < bv ? -dir : dir;
    });
  }, [items, query, sortKey, sortDir]);

  function sortHeader(label: string, col: SortKey) {
    const active = sortKey === col;
    return (
      <th className={th}>
        <button
          type="button"
          onClick={() => {
            if (active) {
              setSortDir((d) => (d === "asc" ? "desc" : "asc"));
            } else {
              setSortKey(col);
              setSortDir(col === "role" || col === "company" ? "asc" : "desc");
            }
          }}
          className={cn(
            "inline-flex items-center gap-1 hover:text-zinc-300",
            active && "text-zinc-300",
          )}
        >
          {label}
          {active ? (
            sortDir === "asc" ? (
              <ArrowUp className="size-3" />
            ) : (
              <ArrowDown className="size-3" />
            )
          ) : (
            <ArrowUpDown className="size-3 opacity-40" />
          )}
        </button>
      </th>
    );
  }

  async function onExport(id: string) {
    setBusyId(id);
    try {
      const res = (await apiFetch(accessToken, `/tailored/${id}/export`, {
        method: "POST",
      })) as ExportTailoredResponse;
      window.open(res.url, "_blank", "noopener,noreferrer");
    } catch (error) {
      toast.error(describeApiError(error));
    } finally {
      setBusyId(null);
    }
  }

  async function onDelete() {
    if (!deleteTarget) return;
    setBusyId(deleteTarget.id);
    try {
      await apiFetch(accessToken, `/tailored/${deleteTarget.id}`, {
        method: "DELETE",
      });
      toast.success("Tailored resume deleted");
      setDeleteTarget(null);
      router.refresh();
    } catch (error) {
      toast.error(describeApiError(error));
    } finally {
      setBusyId(null);
    }
  }

  if (items.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
          <Briefcase className="size-8 text-zinc-600" />
          <p className="text-sm text-zinc-400">
            Nothing saved yet — tailor your resume to a job, then save it here.
          </p>
          <Link
            href="/tailor"
            className="text-sm text-brand-300 underline-offset-4 hover:underline"
          >
            Tailor a Resume
          </Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardContent className="flex flex-col gap-4 pt-6">
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by role or company…"
            aria-label="Search tailored resumes"
            className="max-w-sm border-zinc-700 bg-zinc-950/50 text-zinc-200 placeholder:text-zinc-600 focus-visible:border-brand-500 focus-visible:ring-brand-500/30"
          />
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-zinc-800 text-xs">
                  {sortHeader("Role", "role")}
                  {sortHeader("Company", "company")}
                  {sortHeader("Saved", "saved")}
                  {sortHeader("Exported", "exported")}
                  <th className={cn(th, "w-28 text-right")}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((item) => (
                  <tr
                    key={item.id}
                    className="border-b border-zinc-800/50 last:border-0"
                  >
                    <td className={cn(td, "font-medium text-zinc-100")}>
                      <Link
                        href={`/tailored/${item.id}`}
                        className="hover:text-brand-300 hover:underline underline-offset-4"
                      >
                        {item.role || "Tailored Resume"}
                      </Link>
                    </td>
                    <td className={td}>{item.company_name ?? "—"}</td>
                    <td className={td}>{fmtDate(item.created_at)}</td>
                    <td className={td}>{fmtDate(item.generated_at)}</td>
                    <td className={cn(td, "text-right")}>
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          aria-label="Edit"
                          onClick={() => router.push(`/tailored/${item.id}`)}
                          className="text-zinc-500 hover:text-zinc-100"
                        >
                          <PenLine />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          aria-label="Export"
                          disabled={busyId === item.id}
                          onClick={() => onExport(item.id)}
                          className="text-zinc-500 hover:text-zinc-100"
                        >
                          {busyId === item.id ? (
                            <Loader2 className="animate-spin" />
                          ) : (
                            <Download />
                          )}
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          aria-label="Delete"
                          disabled={busyId === item.id}
                          onClick={() => setDeleteTarget(item)}
                          className="text-zinc-500 hover:text-red-300"
                        >
                          <Trash2 />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
                {visible.length === 0 && (
                  <tr>
                    <td
                      colSpan={5}
                      className="py-8 text-center text-sm text-zinc-500"
                    >
                      No tailored resumes match &ldquo;{query}&rdquo;.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <Dialog
        open={deleteTarget !== null}
        onOpenChange={(open) => {
          if (!open) setDeleteTarget(null);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-zinc-100">
              Delete Tailored Resume?
            </DialogTitle>
            <DialogDescription className="text-zinc-400">
              {deleteTarget?.role || "This tailored resume"}
              {deleteTarget?.company_name
                ? ` · ${deleteTarget.company_name}`
                : ""}{" "}
              will be removed permanently, along with its generated document.
            </DialogDescription>
          </DialogHeader>
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setDeleteTarget(null)}
              disabled={busyId !== null}
              className="border-zinc-700 bg-transparent text-zinc-200 hover:bg-zinc-800/60 hover:text-zinc-100"
            >
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={onDelete}
              disabled={busyId !== null}
              className="border-0 bg-red-600 text-white hover:bg-red-500"
            >
              {busyId !== null ? <Loader2 className="animate-spin" /> : null}{" "}
              Delete
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
