"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { toast } from "sonner";
import type { DsaProgressResponse } from "@/lib/dsa";

export type DsaProgressState =
  | { status: "loading" }
  | { status: "anonymous" }
  /** The progress route failed. Hide progress UI rather than nag. */
  | { status: "unavailable" }
  | { status: "ready"; studied: ReadonlySet<string> };

interface DsaProgressValue {
  state: DsaProgressState;
  setStudied: (topic: string, studied: boolean) => Promise<void>;
}

const DsaProgressContext = createContext<DsaProgressValue | null>(null);

export function useDsaProgress() {
  const value = useContext(DsaProgressContext);
  if (!value) throw new Error("useDsaProgress needs a DsaProgressProvider");
  return value;
}

async function fetchProgress(init?: RequestInit): Promise<DsaProgressResponse> {
  const res = await fetch("/api/dsa/progress", init);
  if (!res.ok) throw new Error(`progress request failed: ${res.status}`);
  return res.json();
}

function toState(data: DsaProgressResponse): DsaProgressState {
  return data.signedIn
    ? { status: "ready", studied: new Set(data.studied) }
    : { status: "anonymous" };
}

/** Loads the visitor's progress once for every /dsa page. The layout keeps
 *  it mounted, so moving between topics doesn't refetch. */
export function DsaProgressProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<DsaProgressState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;
    fetchProgress()
      .then((data) => {
        if (!cancelled) setState(toState(data));
      })
      .catch(() => {
        if (!cancelled) setState({ status: "unavailable" });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const setStudied = useCallback(async (topic: string, studied: boolean) => {
    // Optimistic: flip it now, settle on the server's list, undo on failure.
    const flip = (on: boolean) =>
      setState((prev) => {
        if (prev.status !== "ready") return prev;
        const next = new Set(prev.studied);
        if (on) next.add(topic);
        else next.delete(topic);
        return { status: "ready", studied: next };
      });
    flip(studied);
    try {
      const data = await fetchProgress({
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic, studied }),
      });
      setState(toState(data));
    } catch {
      flip(!studied);
      toast.error("Couldn't save your progress", {
        description: "Check your connection and try again.",
      });
    }
  }, []);

  const value = useMemo(() => ({ state, setStudied }), [state, setStudied]);
  return (
    <DsaProgressContext.Provider value={value}>
      {children}
    </DsaProgressContext.Provider>
  );
}
