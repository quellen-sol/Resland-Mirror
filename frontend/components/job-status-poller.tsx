"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

const POLL_INTERVAL_MS = 3000;
const TERMINAL_STATES = new Set(["COMPLETED", "FAILED"]);
const LOADING_TOAST_ID = "resume-processing";

export default function JobStatusPoller({ jobIds }: { jobIds: string[] }) {
  const router = useRouter();
  const finishedRef = useRef<Set<string>>(new Set());
  const consecutiveFailuresRef = useRef(0);

  const key = jobIds.join(",");

  useEffect(() => {
    if (jobIds.length === 0) {
      toast.dismiss(LOADING_TOAST_ID);
      return;
    }
    toast.loading("Processing your resume…", {
      id: LOADING_TOAST_ID,
      description: "We'll update your profile when it finishes.",
    });
    const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
    if (!baseUrl) return;

    let cancelled = false;

    async function poll() {
      let shouldRefresh = false;
      for (const jobId of jobIds) {
        if (finishedRef.current.has(jobId)) continue;
        try {
          const res = await fetch(`${baseUrl}/check-job-status/${jobId}`, {
            signal: AbortSignal.timeout(10_000),
          });
          if (res.status === 404) {
            finishedRef.current.add(jobId);
            shouldRefresh = true;
            continue;
          }
          if (!res.ok) {
            consecutiveFailuresRef.current += 1;
            if (consecutiveFailuresRef.current === 5) {
              toast.warning("Can't reach the server", {
                id: LOADING_TOAST_ID,
                description:
                  "Still trying — your resume is processing in the background.",
              });
            }
            continue;
          }
          const wasRecovering = consecutiveFailuresRef.current > 0;
          consecutiveFailuresRef.current = 0;
          if (wasRecovering) {
            toast.loading("Processing your resume…", {
              id: LOADING_TOAST_ID,
              description: "We'll update your profile when it finishes.",
            });
          }
          const { status } = (await res.json()) as { status: string };
          if (!TERMINAL_STATES.has(status)) continue;

          finishedRef.current.add(jobId);
          shouldRefresh = true;
          if (status === "COMPLETED") {
            toast.success("Resume processed", {
              description: "Your profile was updated from your resume.",
            });
          } else {
            toast.error("Resume processing failed", {
              description: "Something went wrong — try uploading again.",
            });
          }
        } catch {
          consecutiveFailuresRef.current += 1;
          if (consecutiveFailuresRef.current === 5) {
            toast.warning("Can't reach the server", {
              id: LOADING_TOAST_ID,
              description:
                "Still trying — your resume is processing in the background.",
            });
          }
        }
      }
      if (shouldRefresh && !cancelled) router.refresh();
    }

    void poll();
    const interval = setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, router]);

  return null;
}
