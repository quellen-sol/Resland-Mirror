"use client";

import { CloudOff } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

export default function ApiUnavailable({
  onRetry,
  message = "The Resland API is unavailable right now. Please try again in a moment.",
}: {
  onRetry: () => void;
  message?: string;
}) {
  return (
    <Alert className="border-amber-500/30 bg-amber-500/10 text-amber-100">
      <CloudOff className="text-amber-400" />
      <AlertTitle>Can&apos;t reach the Resland API</AlertTitle>
      <AlertDescription className="flex flex-wrap items-center justify-between gap-3 text-amber-200">
        <span>{message}</span>
        <Button
          variant="outline"
          size="sm"
          onClick={onRetry}
          className="border-amber-500/40 text-amber-100 hover:bg-amber-500/20 hover:text-amber-50"
        >
          Retry
        </Button>
      </AlertDescription>
    </Alert>
  );
}
