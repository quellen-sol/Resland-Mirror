"use client";

import { useRef, useState } from "react";
import {
  CircleAlert,
  CircleCheck,
  FileUp,
  Loader2,
  Upload,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

type UploadResult =
  | { kind: "idle" }
  | { kind: "uploading" }
  | { kind: "success"; status: number; body: string }
  | { kind: "error"; message: string };

export default function UploadForm({
  accessToken,
  onSuccess,
}: {
  accessToken: string;
  onSuccess?: () => void;
}) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<UploadResult>({ kind: "idle" });

  async function handleUpload() {
    if (!file) return;

    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
    if (!apiBaseUrl) {
      setResult({
        kind: "error",
        message: "NEXT_PUBLIC_API_BASE_URL is not configured",
      });
      return;
    }

    setResult({ kind: "uploading" });

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${apiBaseUrl}/upload-initial-resume`, {
        method: "POST",
        headers: { Authorization: `Bearer ${accessToken}` },
        body: formData,
      });
      const body = await response.text();

      if (response.ok) {
        setResult({ kind: "success", status: response.status, body });
        onSuccess?.();
      } else {
        setResult({
          kind: "error",
          message: `HTTP ${response.status}: ${body}`,
        });
      }
    } catch (error) {
      setResult({
        kind: "error",
        message: error instanceof Error ? error.message : String(error),
      });
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        <Label htmlFor="file" className="text-zinc-300">
          File
        </Label>
        <Input
          id="file"
          ref={fileInputRef}
          type="file"
          className="h-auto border-zinc-700 bg-zinc-950/50 py-2 text-zinc-300 file:mr-3 file:rounded-md file:bg-purple-500/10 file:px-2.5 file:py-1 file:text-purple-300 hover:file:bg-purple-500/20 focus-visible:border-purple-500 focus-visible:ring-purple-500/30"
          onChange={(event) => {
            setFile(event.target.files?.[0] ?? null);
            setResult({ kind: "idle" });
          }}
        />
      </div>

      {file && (
        <div className="flex items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-950/50 px-3 py-2 text-sm text-zinc-400">
          <FileUp className="size-4 text-purple-400" />
          <span className="truncate text-zinc-200">{file.name}</span>
          <span className="shrink-0">
            {(file.size / 1024).toFixed(1)} KB
            {file.type ? ` · ${file.type}` : ""}
          </span>
        </div>
      )}

      <Button
        onClick={handleUpload}
        disabled={!file || result.kind === "uploading"}
        className="h-9 w-full border-0 bg-gradient-to-r from-violet-600 to-purple-600 text-white shadow-lg shadow-purple-950/50 hover:from-violet-500 hover:to-purple-500"
      >
        {result.kind === "uploading" ? (
          <>
            <Loader2 className="animate-spin" />
            Uploading…
          </>
        ) : (
          <>
            <Upload />
            Upload
          </>
        )}
      </Button>

      {result.kind === "success" && !onSuccess && (
        <Alert className="border-purple-500/30 bg-purple-500/10 text-purple-200">
          <CircleCheck className="text-purple-400" />
          <AlertTitle>Upload succeeded (HTTP {result.status})</AlertTitle>
          {result.body && (
            <AlertDescription>
              <pre className="mt-1 max-h-64 overflow-auto rounded bg-black/40 p-2 font-mono text-xs whitespace-pre-wrap text-zinc-300">
                {result.body}
              </pre>
            </AlertDescription>
          )}
        </Alert>
      )}

      {result.kind === "error" && (
        <Alert
          variant="destructive"
          className="border-red-500/30 bg-red-500/10"
        >
          <CircleAlert />
          <AlertTitle>Upload failed</AlertTitle>
          <AlertDescription>
            <pre className="mt-1 max-h-64 overflow-auto rounded bg-black/40 p-2 font-mono text-xs whitespace-pre-wrap text-zinc-300">
              {result.message}
            </pre>
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
