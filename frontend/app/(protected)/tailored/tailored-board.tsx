"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
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
import { apiFetch, describeApiError } from "@/lib/api";
import type { ExportTailoredResponse } from "@/lib/tailored";

export interface TailoredItem {
  id: string;
  company_name: string | null;
  role: string | null;
  created_at: string;
  generated_at: string | null;
}

function fmtCreated(iso: string) {
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) return iso;
  return parsed.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
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
      <Card className="border-zinc-800 bg-zinc-900/80 text-zinc-100">
        <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
          <Briefcase className="size-8 text-zinc-600" />
          <p className="text-sm text-zinc-400">
            Nothing saved yet — tailor your resume to a job, then save it here.
          </p>
          <Link
            href="/tailor"
            className="text-sm text-purple-300 underline-offset-4 hover:underline"
          >
            Tailor a resume
          </Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((item) => (
          <Card
            key={item.id}
            className="border-zinc-800 bg-zinc-900/80 text-zinc-100"
          >
            <CardContent className="flex h-full flex-col gap-3 pt-6">
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium text-zinc-100">
                  {item.role || "Tailored resume"}
                </p>
                <p className="truncate text-sm text-zinc-400">
                  {item.company_name ?? "—"}
                </p>
                <p className="mt-1 text-xs text-zinc-500">
                  Saved {fmtCreated(item.created_at)}
                  {item.generated_at &&
                    ` · exported ${fmtCreated(item.generated_at)}`}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="border-zinc-700 bg-transparent text-zinc-200 hover:bg-zinc-800/60 hover:text-zinc-100"
                  onClick={() => router.push(`/tailored/${item.id}`)}
                >
                  <PenLine /> Edit
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={busyId === item.id}
                  onClick={() => onExport(item.id)}
                  className="border-zinc-700 bg-transparent text-zinc-200 hover:bg-zinc-800/60 hover:text-zinc-100"
                >
                  {busyId === item.id ? (
                    <Loader2 className="animate-spin" />
                  ) : (
                    <Download />
                  )}{" "}
                  Export
                </Button>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  aria-label="Delete"
                  disabled={busyId === item.id}
                  onClick={() => setDeleteTarget(item)}
                  className="ml-auto text-zinc-500 hover:text-red-300"
                >
                  <Trash2 />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Dialog
        open={deleteTarget !== null}
        onOpenChange={(open) => {
          if (!open) setDeleteTarget(null);
        }}
      >
        <DialogContent className="border-zinc-800 bg-zinc-900 text-zinc-100">
          <DialogHeader>
            <DialogTitle className="text-zinc-100">
              Delete tailored resume?
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
