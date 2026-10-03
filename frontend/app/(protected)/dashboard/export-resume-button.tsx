"use client";

import { useState } from "react";
import Link from "next/link";
import { Download, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { apiFetch, describeApiError } from "@/lib/api";

interface ExportResumeResponse {
  url: string;
  generated_at: string;
  regenerated: boolean;
}

export default function ExportResumeButton({
  accessToken,
}: {
  accessToken: string;
}) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  const onExport = async () => {
    setBusy(true);
    try {
      const res = (await apiFetch(accessToken, "/resume/export")) as ExportResumeResponse;
      window.open(res.url, "_blank", "noopener,noreferrer");
      setOpen(false);
    } catch (error) {
      toast.error(describeApiError(error));
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setOpen(true)}
        className="border-zinc-700 bg-transparent text-zinc-200 hover:bg-zinc-800/60 hover:text-zinc-100"
      >
        <Download /> Export Resume
      </Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="border-zinc-800 bg-zinc-900 text-zinc-100">
          <DialogHeader>
            <DialogTitle className="text-zinc-100">
              Export Your Resume
            </DialogTitle>
            <DialogDescription className="text-zinc-400">
              We do our best to match your original formatting, but the
              generated document may differ. Please double-check it before
              sending it to employers.
            </DialogDescription>
            <p className="text-sm text-zinc-500">
              This exports your <span className="text-zinc-300">base</span>{" "}
              resume. For a version tailored to a specific job, head to{" "}
              <Link
                href="/tailored"
                className="text-purple-300 underline-offset-4 hover:underline"
              >
                Tailored Resumes
              </Link>
              .
            </p>
          </DialogHeader>
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setOpen(false)}
              disabled={busy}
              className="border-zinc-700 bg-transparent text-zinc-200 hover:bg-zinc-800/60 hover:text-zinc-100"
            >
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={onExport}
              disabled={busy}
              className="border-0 bg-gradient-to-r from-violet-600 to-purple-600 text-white hover:from-violet-500 hover:to-purple-500"
            >
              {busy ? (
                <Loader2 className="animate-spin" />
              ) : (
                <Download />
              )}{" "}
              Export
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
