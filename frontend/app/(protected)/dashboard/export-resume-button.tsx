"use client";

import { useState } from "react";
import { Download, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
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
  const [busy, setBusy] = useState(false);

  const onExport = async () => {
    setBusy(true);
    try {
      const res = (await apiFetch(accessToken, "/resume/export")) as ExportResumeResponse;
      window.open(res.url, "_blank", "noopener,noreferrer");
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
        onClick={onExport}
        disabled={busy}
        className="border-zinc-700 bg-transparent text-zinc-200 hover:bg-zinc-800/60 hover:text-zinc-100"
      >
        {busy ? <Loader2 className="animate-spin" /> : <Download />} Export resume
      </Button>
    </>
  );
}
